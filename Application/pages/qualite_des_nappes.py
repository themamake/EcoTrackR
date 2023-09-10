import requests
import pandas as pd
import streamlit as st
from streamlit import cache
from streamlit_folium import folium_static
import folium
from geopy.geocoders import Nominatim
from geopy import distance
from geographiclib.geodesic import Geodesic
from geopy.distance import distance




#--------------------------------------------------Config Page--------------------------------------------------

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

#--------------------------------------------------Fonctions--------------------------------------------------

parameters_to_keep = [
    'Teneur en Nitrates (NO3) en mg/l',
    'Teneur en Ammonium (NH4) en mg/l',
    'Teneur en Nitrites (NO2) en mg/l',
    'Teneur en Orthophosphates (PO4) en mg/l',
    'Teneur en Phosphore total (Ptot) en mg/l',
    'Demande Biochimique en oxygène en 5 jours (DBO5) en mg/l',
    'Taux de saturation en oxygène (O2sat) en %',
    "Température de l'eau en °C",
    'Potentiel en Hydrogène (pH)',
    'Conductivité en µS/cm',
    'Matières en suspension (MES) en mg/l',
    'Chloroforme',
    'Toluene',
    'Dibromométhane'
]
def get_coordinates_from_city():
    ville = st.session_state.get("ville", "")
    if not ville:
        st.warning("Veuillez spécifier une ville.")
        return None, None

    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(ville)
    if location:
        return location.latitude, location.longitude
    else:
        st.error(f"Impossible de trouver les coordonnées pour la ville: {ville}")
        return None, None

def fetch_stations(latitude, longitude, rayon_km):
    if not (latitude and longitude and rayon_km):
        return []

    params = {
        "lat": latitude,
        "lon": longitude,
        "dist": rayon_km,
        "size": "50"
    }
    
    response = requests.get("https://hubeau.eaufrance.fr/api/v1/qualite_nappes/stations", params=params)

    if response.status_code in [200, 206]:
        data = response.json()
        return data.get("data", [])
    else:
        st.error(f"Erreur lors de la récupération des données des stations: {response.text}")
        return []

def fetch_analyses(code_bss):
    params = {"code_bss": code_bss}
    response = requests.get("https://hubeau.eaufrance.fr/api/v1/qualite_nappes/analyses", params=params)
    if response.status_code in [200, 206]:
        return response.json().get("data", [])
    return []


def calculate_distance_geopy(center_lat, center_lon, station_lat, station_lon):
    center = (center_lat, center_lon)
    station = (station_lat, station_lon)
    return distance(center, station).kilometers



def stations_within_radius(stations, center_lat, center_lon, radius_km):
    valid_stations = []
    for station in stations:
        dist = calculate_distance_geopy(center_lat, center_lon, station["latitude"], station["longitude"])
        if dist <= radius_km:
            valid_stations.append(station)
    return valid_stations










def plot_stations_on_map(stations,bbox,choix_station, ville):
    """Fonction permettant la création de la carte centrée sur le centre de la boîte de géolocalisation """
    west = float(bbox[0])
    south = float(bbox[1])
    east = float(bbox[2])
    north = float(bbox[3])
    center_lat = (north + south) / 2
    center_lon = (east + west) / 2
    map_center = [center_lat, center_lon]
    my_map = folium.Map(location=map_center, zoom_start=9)            
    # Ajout du marqueur pour la ville recherchée
    geolocator = Nominatim(user_agent="home_01")
    location = geolocator.geocode(ville)
    if location:
        folium.Marker(location=[location.latitude, location.longitude], popup=ville, icon=folium.Icon(color='green'), sticky=True).add_to(my_map)
    # Ajout des marqueurs pour chaque station
    for station in stations:
        station_name = station['code_bss']
        station_location = [station['latitude'], station['longitude']]
        # folium.Marker(location=station_location, popup=station_name,sticky=True).add_to(my_map)
        # Vérifier si la station correspond à celle choisie
        if station_name == choix_station:
            color = 'red'  # Couleur pour la station choisie
        else:
            color = 'blue'  # Couleur pour les autres stations
        folium.Marker(location=station_location, popup=station_name, icon=folium.Icon(color=color), sticky=True).add_to(my_map)
    # Affichage de la carte
    return my_map
#_______






def main():
    st.title("Qualité des Nappes Souterraines")
    ville = st.session_state.get("ville", None)
    st.write(f"Ville sélectionnée : {ville}")
    latitude, longitude = get_coordinates_from_city()
    rayon_km = st.session_state.get("rayon_km", 10)
    bbox = st.session_state.get("bbox", None)

    if latitude and longitude:
        stations = fetch_stations(latitude, longitude, rayon_km)
        valid_stations = stations_within_radius(stations, latitude, longitude, rayon_km)
        choix_station = st.sidebar.radio("Choisissez une station :", [x["code_bss"] for x in valid_stations])

        my_map = plot_stations_on_map(stations, bbox, choix_station,ville)
        folium_static(my_map)
        # Si un point est sélectionné, affichez les analyses pour ce point
        selected_station = st.selectbox("Sélectionnez une station:", [s["bss_id"] for s in stations])
        analyses = fetch_analyses(selected_station)
        
        if analyses:
            df = pd.DataFrame(analyses)
            df = df[df["nom_param"].isin(parameters_to_keep)]  # Filtrer par les paramètres choisis

            # Check if "nom_param" column exists
            if "nom_param" in df.columns:
                # Menu déroulant pour sélectionner un paramètre spécifique
                params = list(df["nom_param"].unique())
                selected_param = st.selectbox("Sélectionnez un paramètre à visualiser:", params)

                # Affichage du graphique pour le paramètre sélectionné
                filtered_df = df[df["nom_param"] == selected_param]
                st.line_chart(filtered_df[["date_debut_prelevement", "resultat"]].set_index("date_debut_prelevement"))
            else:
                st.write("La colonne 'nom_param' est absente des données.")

        else:
            st.write("Aucune donnée d'analyse trouvée pour cette station.")

if __name__ == "__main__":
    main()
