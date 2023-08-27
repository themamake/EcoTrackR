
#--------------------------------------------------Import Packages--------------------------------------------------
import streamlit as st



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

def about_us():
    
    with st.container():
    # Layout avec logo et titre
        col1, col2 = st.columns([4, 1])
        with col2:
            st.image("logo.png", width=250) 
    
        # st.subheader("À Propos d'EcoTrack'r")
        
        st.write("Bienvenue sur la page \"Qui Sommes-Nous\" d'EcoTrack'r ! Nous sommes trois etudiants en deuxieme année de mastère Data engineering / data science, concernés par les questions environnementales. EcoTrack'r est un outils réalisé dans le cadre de notre projet de fin d'etude et ayant pour objectif de sensibiliser le public aux enjeux écologiques. Nous avons mis en commun nos compétences en science des données et notre désir de créer un impact positif pour la planète. ")
        
        st.subheader("Notre Histoire")
        st.write("L'idée d'EcoTrack'r est née d'une simple question : Comment pouvons-nous rendre les données environnementales plus compréhensibles et pertinentes pour tous ? C'est ainsi que nous avons lancé notre aventure avec une vision claire : démocratiser l'accès aux informations environnementales.")
        
        st.subheader("Notre Mission")
        st.write("Notre objectif est de rendre les données environnementales plus qu'une simple collection de chiffres et de graphiques. Nous voulons offrir à chaque citoyen la possibilité de comprendre l'impact des changements climatiques et des activités humaines sur nos ressources naturelles. En utilisant des visualisations interactives et des analyses approfondies, nous souhaitons que chacun puisse prendre des décisions éclairées pour la préservation de notre planète.")
        
        st.subheader("Pourquoi EcoTrack'r ?")
        st.write("Les défis environnementaux auxquels nous sommes confrontés exigent une action collective. En comprenant les tendances et les fluctuations des ressources naturelles, nous pouvons identifier les problèmes émergents, surveiller les évolutions à long terme et collaborer pour des solutions durables. EcoTrack'r vise à être le pont entre les données complexes et les citoyens, en permettant à chacun de jouer un rôle actif dans la protection de notre environnement.")
        
        st.subheader("Notre Engagement")
        st.write("Nous croyons que la transparence et la connaissance sont les premières étapes vers le changement. Nous nous engageons à fournir des informations fiables et actualisées, et à travailler continuellement pour améliorer l'accessibilité et la compréhension de ces données. EcoTrack'r n'est pas seulement une application, c'est un mouvement pour un avenir plus vert et plus conscient.")
        
        st.write("Rejoignez-nous dans notre voyage pour mieux comprendre, préserver et chérir les ressources naturelles qui font de notre planète un lieu unique.")

if __name__ == "__main__":
    about_us()
