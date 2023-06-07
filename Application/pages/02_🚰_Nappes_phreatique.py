import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit import cache
from streamlit_folium import folium_static
import folium
from geopy.geocoders import Nominatim
from geopy import distance
import datetime
import time


#--------------------------------------------------Fonctions--------------------------------------------------

def get_bbox_around_city(city, distance_km):
    if not city or city=="":
        st.info("Veuillez saisir le nom d'une ville dans la barre latérale.")
        return None
        
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(city)
    if not location:
        st.error("Impossible de trouver la localisation de la ville.")
        return None
    
    center_point = (location.latitude, location.longitude)
    radius = distance.distance(kilometers=distance_km)

# Calcul des coordonnées de la boîte de géolocalisation
    radius.destination(point=center_point, bearing=0)
    northeast = radius.destination(point=center_point, bearing=45)
    southwest = radius.destination(point=center_point, bearing=225)

    bbox = (southwest.longitude, southwest.latitude, northeast.longitude, northeast.latitude)
    return bbox

@st.cache_data()
def get_piezometric_stations_in_bbox(bbox):
    
    url = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations"
    params = {"bbox": bbox, "size": "100"}  # Nombre maximal de stations à récupérer

    response = requests.get(url, params=params)
    if response.status_code == 200 or response.status_code == 206:
        contenu = response.json()
        if "data" not in contenu or len(contenu["data"]) == 0:
            print("Il n'y a pas de stations piézométriques dans la zone de recherche.")
            return None

# Filtrer les stations dont la date_fin_mesure est supérieure au 1er janvier 2023
        data = [{
            "code_bss": x["code_bss"],
            "bss_id": x["bss_id"],
            "date_debut_mesure": x["date_debut_mesure"],
            "date_fin_mesure": x["date_fin_mesure"],
            "nb_mesures_piezo": x["nb_mesures_piezo"],
            "dep": x["nom_departement"],
            "commune": x["nom_commune"],
            "coordonnées": [x["x"], x["y"]]
        } for x in contenu["data"] if datetime.datetime.strptime(x["date_fin_mesure"], "%Y-%m-%d") > datetime.datetime(2023, 1, 1)]
        nbre_station = len(data)
        resumed_info = {"nbre_station": nbre_station}
        resumed_info.update({ "data": data})
        
        if len(data) == 0:
            print("Il n'y a pas de stations piézométriques dans la zone de recherche.")
        return resumed_info
    else:
        st.error("Erreur lors de la requête API:", response.status_code)





@st.cache_data()
def get_api_level(code_station, size):
    url = "http://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques_tr"
    params = {"code_bss": code_station, "size": size}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        contenu = response.json()
        data = [{"date_mesure": x["date_mesure"],
                #  "niveau_nappe_eau": x["niveau_nappe_eau"],
                 "profondeur_nappe": x["profondeur_nappe"]} for x in contenu["data"]]
        return data
    else:
        st.error("Erreur lors de la récupération des données. Statut de la réponse:"+ str(response.status_code))
        


@st.cache_data()
def get_api_history_level(code_station):
    url = "http://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques"
    params = {"code_bss": code_station}

    response = requests.get(url, params=params)

    if response.status_code == 200 or response.status_code == 206:
        contenu = response.json()
        data = [{"date_mesure": x["date_mesure"],
                "niveau_nappe_eau": x["niveau_nappe_eau"],
                "profondeur_nappe": x["profondeur_nappe"]} for x in contenu["data"]]
        return data
    else:
        st.error("Erreur lors de la récupération des données. Statut de la réponse:" + str(response.status_code))



def plot_stations_on_map(stations,bbox,choix_station, ville):
    
# Création de la carte centrée sur le centre de la boîte de géolocalisation
    west = float(bbox[0])
    south = float(bbox[1])
    east = float(bbox[2])
    north = float(bbox[3])
    center_lat = (north + south) / 2
    center_lon = (east + west) / 2
    map_center = [center_lat, center_lon]
    my_map = folium.Map(location=map_center, zoom_start=10)
    
# Ajout du marqueur pour la ville recherchée
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(ville)
    if location:
        folium.Marker(location=[location.latitude, location.longitude], popup=ville, icon=folium.Icon(color='green'), sticky=True).add_to(my_map)
    
# Ajout des marqueurs pour chaque station
    for station in stations['data']:
        station_name = station['code_bss']
        station_location = [station['coordonnées'][1], station['coordonnées'][0]]
        # folium.Marker(location=station_location, popup=station_name,sticky=True).add_to(my_map)
        # Vérifier si la station correspond à celle choisie
        if station_name == choix_station:
            color = 'red'  # Couleur pour la station choisie
        else:
            color = 'blue'  # Couleur pour les autres stations
        folium.Marker(location=station_location, popup=station_name, icon=folium.Icon(color=color), sticky=True).add_to(my_map)

# Affichage de la carte
    return my_map


def afficher_historique(code_station):
    st.header("Historique complet des points de mesure")
    json_data = get_api_history_level(code_station)
    df = pd.DataFrame(json_data)
    df['date_mesure'] = pd.to_datetime(df['date_mesure'])

    # Tracer le graphique
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date_mesure'], y=df['profondeur_nappe'], mode='lines', name='Profondeur de nappe'))
    fig.update_layout(xaxis_title='Date de mesure', yaxis_title='Niveau / Profondeur')
    fig.update_layout(xaxis=dict(rangeslider=dict(visible=True), type='date'))
    st.plotly_chart(fig)



#--------------------------------------------------Streamlit--------------------------------------------------
# Configuration de la page Streamlit
st.set_page_config(layout="wide", initial_sidebar_state= "expanded" , page_title="Dashboard Piézométrique", page_icon="📊",)

def main():

    #st.header("Relevés Piézométriques des nappes d'eau souterraines")
    st.markdown("<h2 style='text-align: center; color: blue; font-size: 36px;'>Relevés Piézométriques<br>des nappes d'eau souterraines</h2>", unsafe_allow_html=True)

    # with st.sidebar:
    #     ville = st.text_input("Entrez le nom de la ville : ")
    #     rayon_km = st.number_input("Entrez le rayon de la boîte de géolocalisation en kilomètres : ", step=1.0)
    #     #afficher_stations_btn = st.button("Afficher les stations")
    #     st.sidebar.markdown("---")  # Ajout d'une ligne horizontale

    ville= st.session_state["ville"]
    rayon_km= st.session_state["rayon_km"]

    bbox = None
    stations = None
    choix_station = None

    # Définition de la boite de géolocalisation autour de la ville recherchée 
    bbox = get_bbox_around_city(ville, rayon_km)
    stations = None  # Initialisation de la variable stations
    choix_station = None  # Initialisation de la variable choix_station

    # Récupération des stations piézométriques dans la boîte de géolocalisation
    if bbox:
        stations = get_piezometric_stations_in_bbox(bbox)
        if stations:
            st.success("Stations récupérées avec succès !")
            choix_station = st.sidebar.radio("Choisissez une station :", [x["code_bss"] for x in stations["data"]])
            my_map = plot_stations_on_map(stations, bbox, choix_station,ville)
            folium_static(my_map, width=600, height=400)
            st.write("Il y a", stations['nbre_station'], "stations dans la boîte de géolocalisation.",
                        style="margin-top: -100px;")
        else:
            st.warning("Aucune station piézométrique trouvée dans la boîte de géolocalisation.")
    # else:
    #     st.error("Erreur lors de la récupération de la boîte de géolocalisation.")

    # Récupération des données récentes de niveau de la nappe
    if stations and choix_station:
        st.write("#### Historique récent de la station:", choix_station)
        json_data = get_api_level(choix_station, 20000)
        df = pd.DataFrame(json_data)
        df['date_mesure'] = pd.to_datetime(df['date_mesure'])

    # tracer le graphique
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['date_mesure'], y=df['profondeur_nappe'], mode='lines', name='Profondeur de nappe'))
        fig.add_trace(go.Scatter(x=df['date_mesure'], y=df['niveau_nappe_eau'], mode='lines', name='niveau de nappe'))
        fig.update_layout(xaxis_title='Date de mesure', yaxis_title='Niveau / Profondeur')
        fig.update_layout(xaxis=dict(rangeslider=dict(visible=True), type='date'))
        # option de tracage du graphique
        fig.update_layout(
            autosize=True,  # Utilisez l'espace disponible
            margin=dict(l=0, r=0, t=0, b=0),  # Définissez les marges du graphique à 0 pour supprimer la bordure
            paper_bgcolor="rgba(0,0,0,0)",  # Définissez la couleur de l'arrière-plan du graphique sur transparent
            plot_bgcolor="rgba(0,0,0,0)",  # Définissez la couleur de l'arrière-plan du tracé sur transparent
            modebar={'orientation': 'v'}
        )
        st.plotly_chart(fig)
        
    # Afficher les informations sur la station dans la sidebar
        for station in stations['data']:
            if station['code_bss'] == choix_station:
                st.sidebar.markdown("---")  # Ajout d'une ligne horizontale
                st.sidebar.markdown(f"**Informations sur la station :** {choix_station}")
        
                info_text = f"""
                **Département :** {station['dep']}  
                **Commune :** {station['commune']}  
                **Date de début de mesure :** {station['date_debut_mesure']}  
                **Date de fin de mesure :** {station['date_fin_mesure']}  
                **Nombre de mesures :** {station['nb_mesures_piezo']}  
                **Coordonnées :** {station['coordonnées']}  
                    """
                st.sidebar.markdown(info_text)
                break
            
    # Bouton "Historique des mesures de la station"       
    with st.sidebar:
        bouton_historique = st.sidebar.button("Plus d'information sur le point de mesure")

    # Bouton "Historique des mesures de la station"
    if bouton_historique:
        afficher_historique(choix_station)
        
        # Afficher le graphique de l'historique des mesures de la station
        # ... code pour afficher le graphique ...









if __name__ == "__main__":
    main()


#--------------------------------------------------version sauvegarde--------------------------------------------------
# # Définir la largeur de la page à 800 pixels
# st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="Dashboard Piézométrique", page_icon="📊",)

# def main():
#     st.title("Dashboard Piézométrique")

#     ville = st.sidebar.text_input("Entrez le nom de la ville : ")
#     rayon_km = st.sidebar.number_input("Entrez le rayon de la boîte de géolocalisation en kilomètres : ",step=1.0)
#     st.sidebar.button("Afficher les stations")

#     bbox = get_bbox_around_city(ville, rayon_km)
#     stations = None  # Initialisation de la variable stations
    
#     if bbox:
#         stations = get_piezometric_stations_in_bbox(bbox)
#         if stations:
#             st.success("Stations récupérées avec succès !")
#             my_map = plot_stations_on_map(stations, bbox,choix_station)
#             folium_static(my_map, width=600, height=400)
#             st.write("Il y a", stations['nbre_station'], "stations dans la boîte de géolocalisation.", style="margin-top: -100px;")
#         else:
#             st.warning("Aucune station piézométrique trouvée dans la boîte de géolocalisation.")
#     else:
#         st.error("Erreur lors de la récupération de la boîte de géolocalisation.")
    
#     choix_station = None
#     if stations:
#         choix_station = st.sidebar.radio("Choisissez une station :", [x["code_bss"] for x in stations["data"]])
        
#         if choix_station:
#             choix_station_index = [x["code_bss"] for x in stations["data"]].index(choix_station)            
#             st.write("### Historique récent de la station:", choix_station)
#             json_data = get_api_level(choix_station, 20000)
                            
#             df = pd.DataFrame(json_data)
#             # df['date_mesure'] = pd.to_datetime(df['date_mesure'])

#             fig = go.Figure()
#             fig.add_trace(go.Scatter(x=df['date_mesure'], y=df['profondeur_nappe'], mode='lines', name='Profondeur de nappe'))
            
            
#             fig.update_layout(xaxis_title='Date de mesure', yaxis_title='Niveau / Profondeur')
#             fig.update_layout(xaxis=dict(rangeslider=dict(visible=True), type='date'))
            
#             # option de tracage du graphique
#             fig.update_layout(
#             margin=dict(l=0, r=0, t=0, b=0),  # Définissez les marges du graphique à 0 pour supprimer la bordure
#             paper_bgcolor="rgba(0,0,0,0)",  # Définissez la couleur de l'arrière-plan du graphique sur transparent
#             plot_bgcolor="rgba(0,0,0,0)"  # Définissez la couleur de l'arrière-plan du tracé sur transparent
#             )
            
#             st.plotly_chart(fig)

# if __name__ == "__main__":
#     main()

#----------------------------------------------------------------





#------------------------------------------------
