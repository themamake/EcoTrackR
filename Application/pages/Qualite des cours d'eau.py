# Import required libraries

import requests
import streamlit as st
from streamlit import cache
from streamlit_folium import folium_static
import folium
from geopy.geocoders import Nominatim
import requests

import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

st.set_page_config(
                   initial_sidebar_state= "expanded" , 
                   page_title="Dashboard Hydrologique", 
                   page_icon="📊",
                   layout='centered')

#--------------------------------------------------Police-------------------------------------------------------

st.markdown("""
    <style>
        * {
            font-family: Avenir Next, sans-serif !important;
        }
    </style>
    """, unsafe_allow_html=True)


#--------------------------------------------------background----------------------------------------------------   
page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] > .main {{
background-image: url("https://images.unsplash.com/photo-1524055988636-436cfa46e59e");
background-size:60%;
background-position: right;
background-repeat: no-repeat;
background-attachment: fixed;
}}



[data-testid="stSidebar"] > div:first-child {{
background-color: #99b247;
background-size:cover;
background-position:center; 
background-repeat: no-repeat;
}}

.main .block-container{{
background-color: rgba(255, 255, 255, 0.95);  /* Fond blanc avec 95% d'opacité */
border-radius: 10px; 
padding: 2rem; 
}}

.stSidebar {{
background-color: rgba(255, 255, 255, 0.95);  /* Fond blanc avec 95% d'opacité pour la barre latérale */
}}

[data-testid="stHeader"] {{
background: rgba(0,0,0,0);
}}

[data-testid="stToolbar"] {{
right: 2rem;
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)



def fetch_data_from_api(bbox):
    """
    Fetch data from the API using a bounding box.
    """
    url = 'http://hubeau.eaufrance.fr/api/v2/qualite_rivieres/station_pc'
    params = {"bbox": bbox, "size": "100"}
    response = requests.get(url, params=params)
    if response.status_code == 200 or response.status_code == 206:
        contenu = response.json()
        if not contenu["data"]:
            print("Il n'y a pas de stations dans la zone de recherche.")
            return
        data = [{"code_station": x["code_station"],
                 "libelle_commune": x["libelle_commune"],
                 "libelle_station": x["libelle_station"],
                 "localisation_precise": x["localisation_precise"],
                 "code_commune": x["code_commune"],
                 "libelle_commune": x["libelle_commune"],
                 "code_cours_eau":x["code_cours_eau"],
                 "coordinates": x["geometry"]["coordinates"]
                 } for x in contenu["data"]] 
        nbre_station = len(data)
        resumed_info = {"nbre_station": nbre_station, "data": data}
        resumed_info = {"nbre_station": nbre_station, "data": data}
        if len(data) == 0:
            print("Il n'y a pas de stations dans la zone de recherche.")
        return resumed_info
    else:
        print("Erreur lors de la requête API:", response.status_code)   

#_______

def get_data_from_api_analyse(code_station):
    url = "http://hubeau.eaufrance.fr/api/v2/qualite_rivieres/analyse_pc"
    params = {"code_station": code_station, "format": "json", "pretty": ""}
    response = requests.get(url, params=params)
   
    # Ajouter une boîte de sélection pour le paramètre à analyser
    choixParam = st.selectbox(
        'Quel paramètre souhaitez-vous analyser ?',
        ('Nitrates', 'Sulfates', 'Orthophosphates (PO4)')
    )  
    
    st.session_state['choixParam'] = choixParam  # Sauvegarder dans l'état de la session

    if response.status_code == 206 or response.status_code == 200 :
        contenu = response.json()   
        # Définir la date limite comme le 1er janvier 2000
        date_limit = datetime.strptime('2000-01-01', '%Y-%m-%d')
           
        data = [{"code_station": x["code_station"],
                 "libelle_station": x["libelle_station"],
                 "date_prelevement": x["date_prelevement"],
                 "code_parametre": x["code_parametre"],
                 "libelle_parametre": x["libelle_parametre"],
                 "resultat": x["resultat"],
                 "symbole_unite":x["symbole_unite"],
                 "code_remarque": x["code_remarque"],
                 "mnemo_remarque": x["mnemo_remarque"],
                 "code_statut": x["code_statut"],
                 "mnemo_statut": x["mnemo_statut"],
                 "code_qualification": x["code_qualification"],
                 "libelle_qualification": x["libelle_qualification"]
                 } for x in contenu["data"] if x["libelle_parametre"] in choixParam and datetime.strptime(x["date_prelevement"], '%Y-%m-%d') >= date_limit] 
       
        if len(data) == 0:
            print("Il n'y a pas de données pour la station séléctionner.")
        
        # Convertir la liste de dictionnaires en DataFrame
        df = pd.DataFrame(data)

        # Vérifier si le DataFrame est vide ou si 'date_prelevement' n'est pas dans les colonnes
        if df.empty or 'date_prelevement' not in df.columns:
            print("Aucune donnée correspondant aux critères n'a été trouvée.")
            return {"data": df}
        
        # Trier le DataFrame par 'date_prelevement'
        df['date_prelevement'] = pd.to_datetime(df['date_prelevement'])
        df = df.sort_values('date_prelevement')

        return df
    else:
        print("Erreur lors de la requête API:", response.status_code)
#_______



def plot_stations_on_map(stations,bbox,choix_station, ville):
    """ Cette fonction permet de tracer les stations sur une carte Folium. """
# Création de la carte centrée sur le centre de la boîte de géolocalisation
    west = float(bbox[0])
    south = float(bbox[1])
    east = float(bbox[2])
    north = float(bbox[3])
    center_lat = (north + south) / 2
    center_lon = (east + west) / 2
    map_center = [center_lat, center_lon]
    my_map = folium.Map(location=map_center, zoom_start=10)#, width=1075, height=400)
# Ajout du marqueur pour la ville recherchée
    geolocator = Nominatim(user_agent="home_01")
    location = geolocator.geocode(ville)
    if location:
        folium.Marker(location=[location.latitude, location.longitude], popup=ville, icon=folium.Icon(color='green'), sticky=True).add_to(my_map)
# Ajout des marqueurs pour chaque station
    for station in stations['data']:
        station_name = station['code_station']
        station_location = [station['coordinates'][1], station['coordinates'][0]]
        if station_name == choix_station:
            color = 'red'  # Couleur pour la station choisie
        else:
            color = 'blue'  # Couleur pour les autres stations
        folium.Marker(location=station_location, popup=station_name, icon=folium.Icon(color=color), sticky=True).add_to(my_map)
# Affichage de la carte
    return my_map
#_______



def main():
    # Streamlit App Title and Subheader
    st.title("Qualité des Cours d'Eau")
    st.subheader("Une application pour analyser et visualiser la qualité des cours d'eau.")
     # Verification que la ville, le rayon et la bbox sont bien définis
    ville = st.session_state.get("ville", None)
    rayon_km = st.session_state.get("rayon_km", None)
    bbox = st.session_state.get("bbox", None)
    
    if not (ville and rayon_km and bbox):
        # Display an error message
        st.error("Veuillez vous rendre sur la page d'accueil afin de choisir une Localité.")
        return  # Exit the function
    # Initialisation des variables stations et choix_station
    stations = None 
    choix_station = None 
    # Récupération des stations dans la boîte de géolocalisation
    if bbox:
        stations = fetch_data_from_api(bbox)
        if stations and stations['data']:
            st.success("Stations récupérées avec succès !")
            options = [(f"{x['libelle_station']} - {x['code_station']}", x['code_station']) for x in stations["data"]]
            labels = [option[0] for option in options]
            proposition = st.sidebar.radio("Choisissez une station :", labels)
            # Récupérer la valeur de 'code_station' associée au libellé choisi
            choix_station = next(value for label, value in options if label == proposition)
     # Afficher la carte avec les stations
            my_map = plot_stations_on_map(stations, bbox, choix_station,ville)
            folium_static(my_map)#, width=1075, height=400)
            # Afficher la légende de la carte
            st.markdown("""
            <div style='text-align: center;'>
                <span style='font-size: 12px; color: black;'>
                    <span style='color: #72b026; font-size: 24px; vertical-align: middle;'>•</span>: Ville choisie &nbsp;&nbsp;&nbsp;&nbsp;
                    <span style='color: #38aadd; font-size: 24px; vertical-align: middle;'>•</span>: Stations disponibles &nbsp;&nbsp;&nbsp;&nbsp;
                    <span style='color: red; font-size: 24px; vertical-align: middle;'>•</span>: Station sélectionnée
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("Il y a", stations['nbre_station'], "stations dans la boîte de géolocalisation.",
                        style="margin-top: -100px;")
            st.info("""Les stations de mesures physico-chimiques sont souvent installées pour surveiller la qualité de l'eau dans différents milieux aquatiques comme les rivières, les lacs, et les océans. Elles peuvent servir à des fins de recherche, de réglementation, ou d'alerte précoce pour les problèmes environnementaux.""")
        else:
            st.warning("Aucune station trouvée dans la boîte de géolocalisation.")
    
          
    # Tracer un graphique illustrant l'évolution de la teneur en nitrate pour chaque date de prélèvement 
    if stations and choix_station:
        data = get_data_from_api_analyse(choix_station)
        if len(data) == 1:
            st.warning("Il n'y a pas de données pour la station séléctionner!")
        else:
            choixParam = st.session_state.get('choixParam', 'Nitrates') 
            plt.figure(figsize=(12, 6))
            plt.plot(data['date_prelevement'], data['resultat'], marker='o')
            # plt.title('Évolution de la teneur en Nitrate')
            plt.title(f'Évolution de la teneur en {choixParam}')
            plt.xlabel('Date de prélèvement')
            # plt.ylabel(f"Teneur en Nitrate ({data['symbole_unite'].iloc[0]})")
            plt.ylabel(f"Teneur en {choixParam}({data['symbole_unite'].iloc[0]})")
            plt.grid(True)
            plt.show()
            st.pyplot(plt)
     
     # Afficher les informations sur la station dans la sidebar
        for station in stations['data']:
            if station['code_station'] == choix_station:
                st.sidebar.markdown("---")  # Ajout d'une ligne horizontale
                st.sidebar.markdown(f"**Informations sur la station :** {choix_station}")
                info_text = f"""
                **Localisation precise :** {station['localisation_precise']}  
                **Code de la station:** {station['code_station']} \n
                **Commune :** {station['libelle_commune']}  
                **Cours d'eau :** {station["code_cours_eau"]}  s
                **Nom de la station :** {station['libelle_station']}  
                    """
                st.sidebar.markdown(info_text)
                break

if __name__ == "__main__":
    main()



