import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

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

def stations_within_radius(stations, center_lat, center_lon, radius_km):
    valid_stations = []
    for station in stations:
        distance = geodesic((center_lat, center_lon), (station["latitude"], station["longitude"])).kilometers
        if distance <= radius_km:
            valid_stations.append(station)
    return valid_stations

def main():
    st.title("Qualité des Nappes Souterraines")
    ville = st.session_state.get("ville", None)
    st.write(f"Ville sélectionnée : {ville}")
    latitude, longitude = get_coordinates_from_city()
    rayon_km = st.session_state.get("rayon_km", 10)

    if latitude and longitude:
        stations = fetch_stations(latitude, longitude, rayon_km)
        valid_stations = stations_within_radius(stations, latitude, longitude, rayon_km)

        m = folium.Map(location=[latitude, longitude], zoom_start=10)
        for station in valid_stations:
            folium.Marker(
                [station["latitude"], station["longitude"]],
                tooltip=station["bss_id"],
                popup=folium.Popup(station["bss_id"], parse_html=True, max_width=300)
            ).add_to(m)

        folium_static(m)

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
