
#--------------------------------------------------Import Packages-------------------------------------------------- tetetet

import streamlit as st
from geopy.geocoders import Nominatim
from geopy import distance
import folium
from streamlit_folium import folium_static


#--------------------------------------------------Config Page--------------------------------------------------

st.set_page_config(
                   initial_sidebar_state= "expanded" , 
                   page_title="Dashboard Piézométrique", 
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
background-size:cover;
background-position: center;
background-repeat: no-repeat;
background-attachment: local;
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

def get_bbox_around_city(city, distance_km):
    """ Fonction permettant de definir une bbox autour de la localité choisie en fonction du nombre de km defini par l utilisateur"""
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


#----------------------------------------------Dashboard--------------------------------------------------

def main( ):

    with st.container():

    # Layout avec logo et titre
        col1, col2 = st.columns([4, 1])
        with col2:
            st.image("logo.png", width=250) 

    # Presentation de l'application
        st.write("Bienvenue dans l'application EcoTrack'R - Suivi de la Ressource Eau")
        st.write("EcoTrack'R est une plateforme interactive conçue pour vous fournir des informations essentielles sur l'état de la ressource en eau dans votre région. Nous sommes déterminés à sensibiliser le public à l'importance de préserver nos ressources en eau et à comprendre les impacts du changement climatique.")
        
        st.write("🌊 **Niveaux des nappes phréatiques** : Suivez l'évolution des niveaux d'eau souterraine dans votre ville et sa région. Comprenez les tendances et les variations saisonnières.")
        st.write("💧 **Débits des cours d'eau** : Accédez aux données en temps réel sur les débits des rivières locales. Identifiez les changements de débit et leur impact sur l'écosystème.")
        st.write("🚰 **Qualité de l'eau potable** : Restez informé sur la qualité de l'eau potable dans votre zone. Découvrez les analyses et les éventuels problèmes de contamination.")
        st.write("🌡️ **Température des cours d'eau** : Explorez les données de température des rivières et des cours d'eau. Analysez les variations et leur corrélation avec les conditions environnementales.")
        st.write("🐟 **Espèces de poissons observés** : Découvrez les zones de reproduction et de vie des poissons dans votre région. Apprenez comment ces espaces sont affectés par les changements environnementaux.")
        st.write("\n\n")

        st.write("En utilisant EcoTrack'R, vous aurez accès à des informations détaillées, des graphiques interactifs et des analyses approfondies pour mieux comprendre l'état de votre environnement aquatique. Notre objectif est de vous fournir les connaissances nécessaires pour agir de manière informée et contribuer à la préservation de nos précieuses ressources en eau.")
        
        st.write("Explorez, apprenez et devenez un défenseur de notre ressource la plus précieuse - l'eau.")

        st.write("\n\n")
    
    # Formulaire de recherche dans la barre latérale
    with st.sidebar:  
        st.subheader("Sélectionnez votre zone de recherche")
        if "ville" not in st.session_state:
            st.session_state["ville"] = ""
        if "rayon_km" not in st.session_state:
            st.session_state["rayon_km"] = 1
            
    # Selection de la ville et du rayon de recherche
        ville = st.text_input("Entrez le nom d'une ville francaise : ", st.session_state["ville"])
        rayon_km = st.slider("Entrez le rayon de la boîte de géolocalisation en kilomètres :", 1, 50, int(st.session_state["rayon_km"]))
    # Définition de la boite de géolocalisation autour de la ville recherchée 
        bbox = get_bbox_around_city(ville, rayon_km)
        submit = st.button("Rechercher")
    
    # Gestions des erreurs    
        if submit:
            try:  # Block pour capturer les erreurs
                geolocator = Nominatim(user_agent="geoapiExercises")
                preliminary_location = geolocator.geocode(ville)

                # Si la ville n'est pas trouvée
                if not preliminary_location:
                    st.error("Ville non trouvée. Veuillez rentrer un autre nom de ville.")
                    return
                
                # Si la ville est trouvée mais n'est pas en France
                elif "France" not in preliminary_location.address:
                    st.error("Le service n'est disponible que pour la France. Veuillez rentrer une localité française.")
                    return
                
    # Enregistrement des données dans la session
                st.session_state["ville"] = ville
                st.session_state["rayon_km"] = rayon_km
                st.session_state["bbox"] = bbox
                st.write("Vous avez sélectionné", ville, "et un rayon de: ", rayon_km, "km")
                st.session_state["rayon_km"] = rayon_km
                
                
    # Si la ville existe et est en France : affichage de la carte
                location = geolocator.geocode(f"{ville}, France")
                m = folium.Map(location=[location.latitude, location.longitude], zoom_start=9)
                folium.Circle(
                    radius=rayon_km*1000,
                    location=[location.latitude, location.longitude],
                    color="blue",
                    fill=True,
                ).add_to(m)
                folium_static(m, height = 420, width = 420)
                
                st.info("Vous pouvez desormais naviguer dans les differents onglets de l'application afin d'explorer les données de votre region.")
     # Gestion d'erreurs inattendues pour aider à diagnostiquer le problème.
            except Exception as e:
                st.error(f"Une erreur s'est produite : {e}")
    

if __name__ == "__main__":
    main()
