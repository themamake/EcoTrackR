
import streamlit as st
import requests
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static
from geopy.distance import geodesic

def get_location_coordinates():
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

def fetch_observations(code_bss):
    if not code_bss:
        return []

    params = {
        "code_bss": code_bss,
        "size": 5
    }
    response = requests.get("https://hubeau.eaufrance.fr/api/v1/qualite_nappes/analyses", params=params)

    if response.status_code in [200, 206]:
        data = response.json()
        return data.get("data", [])
    else:
        st.error(f"Erreur lors de la récupération des observations: {response.text}")
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
    latitude, longitude = get_location_coordinates()
    rayon_km = st.session_state.get("rayon_km", 10)

    if latitude and longitude:
        stations = fetch_stations(latitude, longitude, rayon_km)
        valid_stations = stations_within_radius(stations, latitude, longitude, rayon_km)
        
        m = folium.Map(location=[latitude, longitude], zoom_start=10)
        for station in valid_stations:
            folium.Marker(
                [station["latitude"], station["longitude"]],
                tooltip=station["bss_id"]
            ).add_to(m)

        folium_static(m)

        station_names = [s["bss_id"] for s in valid_stations]
        selected_station = st.selectbox("Sélectionnez une station:", station_names)
        code_bss = next((s["code_bss"] for s in valid_stations if s["bss_id"] == selected_station), None)
        observations = fetch_observations(code_bss)
        st.write(observations)

if __name__ == "__main__":
    main()
