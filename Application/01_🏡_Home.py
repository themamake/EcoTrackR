
import streamlit as st
from geopy.geocoders import Nominatim
from geopy import distance


st.set_page_config(layout="wide", 
                   initial_sidebar_state= "expanded" , 
                   page_title="Dashboard Piézométrique", 
                   page_icon="📊",)

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




#----------------------------------------------Streamlit--------------------------------------------------

def main( ):
    st.header("HOME PAGE")
    st.title("EcotrackR")

    # ville = st.text_input("Entrez le nom de la ville : ")
    # rayon_km = st.number_input("Entrez le rayon de la boîte de géolocalisation en kilomètres : ", step=1.0)
    
    if "ville" not in st.session_state:
        st.session_state["ville"] = ""
    if "rayon_km" not in st.session_state:
        st.session_state["rayon_km"] = ""

    ville = st. text_input("Entrez le nom de la ville : ", st.session_state["ville"])
    rayon_km = st.number_input("Entrez le rayon de la boîte de géolocalisation en kilomètres : ", value=float(st.session_state["rayon_km"]) if st.session_state["rayon_km"] != '' else 0.0, min_value=0.0, step=1.0)

    submit = st.button("Submit")
    if submit:
        st.session_state["ville"] = ville
        st.write("You have entered: ", ville)
        st.session_state["rayon_km"] = rayon_km
        st.write("You have entered: ", rayon_km)

if __name__ == "__main__":
    main()