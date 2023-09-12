#API temperature des cours d'eau 
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
import seaborn as sns

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



def fetch_data_from_api_temStat(bbox):
    """
    Fetch data from the API using a bounding box.
    """
    url = "http://hubeau.eaufrance.fr/api/v1/temperature/station"
    params = {"bbox": bbox, "size": "100"}
    response = requests.get(url, params=params)
    if response.status_code == 200 or response.status_code == 206:
        contenu = response.json()
        if not contenu["data"]:
            print("Il n'y a pas de stations dans la zone de recherche.")
            return
        data = [{"code_station": x["code_station"],
                 "libelle_station": x["libelle_station"],
                 "localisation": x["localisation"],
                 "longitude": x["longitude"],
                 "latitude": x["latitude"],
                 "code_commune": x["code_commune"],
                 "libelle_commune":x["libelle_commune"],
                 "libelle_cours_eau": x["libelle_cours_eau"],
                 "coordonnées": [x["longitude"], x["latitude"]]
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

def get_data_from_api_temp_chronique(code_station):
    url = "https://hubeau.eaufrance.fr/api/v1/temperature/chronique"    
    params = {"code_station": code_station, "format": "json", "pretty": "", "size": "20000"}
    response = requests.get(url, params=params)
   
    if response.status_code == 206 or response.status_code == 200 :
        contenu = response.json()   
                   
        data = [{"code_station": x["code_station"],
                 "libelle_station": x["libelle_station"],
                 "code_commune": x["code_commune"],
                 "libelle_commune": x["libelle_commune"],
                 "code_parametre": x["code_parametre"],
                 "libelle_parametre": x["libelle_parametre"],
                 "date_mesure_temp":x["date_mesure_temp"],
                 "heure_mesure_temp":x["heure_mesure_temp"],
                 "resultat": x["resultat"],
                 "symbole_unite": x["symbole_unite"]
                 
                 } for x in contenu["data"]]
        
        nbre_station = len(data)
        resumed_info = {"nbre_station": nbre_station, "data": data}
        resumed_info = {"nbre_station": nbre_station, "data": data}
       
        if len(data) == 0:
                print("Il n'y a pas de données pour la station séléctionner.")
            
            # Convertir la liste de dictionnaires en DataFrame
        df = pd.DataFrame(data)

            # Vérifier si le DataFrame est vide ou si 'date_prelevement' n'est pas dans les colonnes
        if df.empty or 'date_mesure_temp' not in df.columns:
            print("Aucune donnée correspondant aux critères n'a été trouvée.")
            return {"data": df}
       
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
        station_location = [station['coordonnées'][1], station['coordonnées'][0]]
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
    st.title("TEMPÉRATURE DES COURS D'EAU")
    st.subheader("Une application pour analyser et visualiser la température des cours d'eau.")
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
        stations = fetch_data_from_api_temStat(bbox)
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
            st.info("""L'API "Température des cours d'eau" permet d'interroger les données de températures relevées par des capteurs automatiques posés dans les cours d'eau de France métropolitaine.
Ces capteurs enregistrent la température à des fréquences variant d'une minute à quelques heures.""")
        else:
            st.warning("Aucune station trouvée dans la boîte de géolocalisation.")
    
          

    if stations and choix_station:
        data = get_data_from_api_temp_chronique(choix_station)
        # st.dataframe(data)
        if len(data) == 1:
            st.warning("Il n'y a pas de données pour la station séléctionner!")
        else:
            data = data.sort_values('heure_mesure_temp')

            # Remove duplicates if any
            # data = data.drop_duplicates(subset='heure_mesure_temp', keep='first')
            
     # Conversion de 'heure_mesure_temp' en un format plus simple comme '8H' à partir de '08:00:00'
            data['heure_mesure_simplified'] = data['heure_mesure_temp'].apply(lambda x: f"{int(x.split(':')[0])}H")
# Graphique pour la dernière date de mesure

            # Filtrage des données pour ne conserver que les lignes correspondant à la dernière 'date_mesure_temp'
            latest_date = data['date_mesure_temp'].max()
            filtered_data = data[data['date_mesure_temp'] == latest_date]
            # st.dataframe(filtered_data)
    # Création du graphique avec l'heure de mesure simplifiée
            plt.figure(figsize=(12, 6))
            plt.plot(filtered_data['heure_mesure_simplified'], filtered_data['resultat'], marker='o')
            plt.title(f"Évolution des températures")
            plt.xlabel('Heure de mesure')
            plt.ylabel(f"Température ({filtered_data['symbole_unite'].iloc[0]})")
            plt.grid(True)
            # plt.show()
            st.pyplot(plt)
     
            # Convert 'date_mesure_temp' to datetime format if it's not
            data['date_mesure_temp'] = pd.to_datetime(data['date_mesure_temp'])
          # Extract month and year from 'date_mesure_temp'
            data['Year'] = data['date_mesure_temp'].dt.year
            data['Month'] = data['date_mesure_temp'].dt.month

            # Group by Year and Month, then calculate the mean temperature
            df_grouped = data.groupby(['Year', 'Month']).agg({'resultat': 'mean'}).reset_index()
            # Create the plot
            plt.figure(figsize=(12, 6))
            sns.lineplot(x='Month', y='resultat', hue='Year', data=df_grouped)
            plt.title('Moyenne des températures par mois pour chaque année')
            plt.xlabel('Mois')
            plt.ylabel('Température moyenne')
            plt.legend(title='Année', loc='upper right')
            st.pyplot(plt)

            # Code to generate a heatmap of the average temperature by month for each year

            # Group by Year and Month, then calculate the mean temperature
            df_grouped = data.groupby(['Year', 'Month']).agg({'resultat': 'mean'}).reset_index()

            # Pivot the DataFrame to get it in the right format for a heatmap
            df_pivot = df_grouped.pivot("Month", "Year", "resultat")

            # Create the heatmap
            plt.figure(figsize=(12, 8))
            sns.heatmap(df_pivot, annot=True, fmt=".1f", cmap='coolwarm', cbar_kws={'label': 'Température moyenne'})
            plt.title('Moyenne des températures par mois pour chaque année')
            plt.xlabel('Année')
            plt.ylabel('Mois')
            st.pyplot(plt)
    
     
     # Afficher les informations sur la station dans la sidebar
        for station in stations['data']:
            if station['code_station'] == choix_station:
                st.sidebar.markdown("---")  # Ajout d'une ligne horizontale
                st.sidebar.markdown(f"**Informations sur la station :** {choix_station}")
                info_text = f"""
                **Commune  :** {station['libelle_commune']}  
                **code de la station:** {station['code_station']} \n
                **Nom de lastation :** {station['libelle_station']}  
                **Nom cours d'eau :** {station["libelle_cours_eau"]}    
                    """
                st.sidebar.markdown(info_text)
                break

if __name__ == "__main__":
    main()
