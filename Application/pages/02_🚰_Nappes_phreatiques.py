#--------------------------------------------------Import Packages--------------------------------------------------

import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import plotly.graph_objects as go
import streamlit as st
from streamlit import cache
from streamlit_folium import folium_static
import folium
from geopy.geocoders import Nominatim
from geopy import distance
import datetime
import calendar
import locale

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

def convert_date_format(date_str):
    " Fonction permettant de convertir une date au format AAAA-MM-JJ en JJ-MM-AAAA"
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime('%d-%m-%Y')
#_______

@st.cache_data()
def get_piezometric_stations_in_bbox(bbox):
    url = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations"
    params = {"bbox": bbox, "size": "100"}  # Nombre maximal de stations à récupérer
    response = requests.get(url, params=params)
    if response.status_code == 200 or response.status_code == 206:
        contenu = response.json()
        if not contenu["data"]:
            print("Il n'y a pas de stations piezometrique dans la zone de recherche.")
            return
# Filtrer les stations dont la date_fin_mesure est supérieure au 1er janvier 2023
        data = [{
            "code_bss": x["code_bss"],
            "bss_id": x["bss_id"],
            "date_debut_mesure": convert_date_format(x["date_debut_mesure"]),
            "date_fin_mesure": convert_date_format(x["date_fin_mesure"]),
            "nb_mesures_piezo": x["nb_mesures_piezo"],
            "dep": x["nom_departement"],
            "commune": x["nom_commune"],
            "coordonnées": [x["x"], x["y"]]
        } for x in contenu["data"] if datetime.datetime.strptime(x["date_fin_mesure"], "%Y-%m-%d") > datetime.datetime(year=2023, month=1, day=1)]

        nbre_station = len(data)
        data.sort(key=lambda x: datetime.datetime.strptime(x["date_debut_mesure"], "%d-%m-%Y"))  # Tri des données
        resumed_info = {"nbre_station": nbre_station, "data": data}
        if len(data) == 0:
            print("Il n'y a pas de stations piézométriques dans la zone de recherche.")
        return resumed_info
    else:
        print("Erreur lors de la requête API:", response.status_code)        
#_______

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
#_______

@st.cache_data()
def get_api_level(code_station):
    url = "http://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques_tr"
    params = {"code_bss": code_station, "size":20000}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        contenu = response.json()
        data = [{"date_mesure": x["date_mesure"],
                #  "niveau_nappe_eau": x["niveau_nappe_eau"],
                 "profondeur_nappe": x["profondeur_nappe"]} for x in contenu["data"]]
        return data
    else:
        print("Erreur lors de la récupération des données. Statut de la réponse:"+ str(response.status_code))
#_______

def historique_recent(code_station):
    """ Fonction permettant de récupérer les données récentes de niveau de la nappe et de tracer un graphique interactif"""
    json_data = get_api_level(code_station)
    if not json_data:
        st.warning("Il n'y a pas de données disponibles pour cette station piézométrique")
        return
    df = pd.DataFrame(json_data)
    df['date_mesure'] = pd.to_datetime(df['date_mesure'])
    # Tracer le graphique
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date_mesure'], y=df['profondeur_nappe'], mode='lines', name='Profondeur de nappe'))
    fig.update_layout(xaxis_title='Date de mesure', yaxis_title='Profondeur de la nappe')
    fig.update_layout(xaxis=dict(rangeslider=dict(visible=True), type='date'))
    fig.update_layout(
    #autosize=True,  
    width=1075,
    height=400,
    margin=dict(l=0, r=0, t=0, b=0),  # Définissez les marges du graphique à 0 pour supprimer la bordure
    paper_bgcolor="rgba(0,0,0,0)",  # Définissez la couleur de l'arrière-plan du graphique sur transparent
    plot_bgcolor="rgba(0,0,0,0)",  # Définissez la couleur de l'arrière-plan du tracé sur transparent
    modebar={'orientation': 'v'}
        )
    return fig


#                                                       --------------------------------------

@st.cache_data()
def get_api_history_level(code_station):
    url = "http://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques"
    params = {"code_bss": code_station, "size":20000}
    response = requests.get(url, params=params)
    if response.status_code == 200 or response.status_code == 206:
        contenu = response.json()
        data = [{"date_mesure": x["date_mesure"],
                "niveau_nappe_eau": x["niveau_nappe_eau"],
                "profondeur_nappe": x["profondeur_nappe"]} for x in contenu["data"]]
        if not data:
            st.warning("Il n'y a pas de données disponibles pour cette station piézométrique")
        return data
    else:
        st.error("Erreur lors de la récupération des données. Statut de la réponse:" + str(response.status_code))
#_______      

def charger_donnees_historique(code_station):
    json_data = get_api_history_level(code_station)
    df_history = pd.DataFrame(json_data)
    df_history['date_mesure'] = pd.to_datetime(df_history['date_mesure'])
    return df_history
#_______

def graph_hystory_complete(df):
    fig = go.Figure()
    #fig.add_trace(go.Scatter(x=df['date_mesure'], y=df['profondeur_nappe'], mode='lines', name='Profondeur de nappe'))
    fig.add_trace(go.Scatter(x=df['date_mesure'], y=df['niveau_nappe_eau'], mode='lines', name='niveau_nappe_eau'))
    fig.update_layout(
    autosize=True,  # Utilisation de l'espace disponible
    # width=1075,
    # height=400,
    margin=dict(l=0, r=0, t=0, b=0),  # Définissez les marges du graphique à 0 pour supprimer la bordure
    paper_bgcolor="rgba(0,0,0,0)",  # Définissez la couleur de l'arrière-plan du graphique sur transparent
    plot_bgcolor="rgba(0,0,0,0)",  # Définissez la couleur de l'arrière-plan du tracé sur transparent
    modebar={'orientation': 'v'}
        )
    fig.update_layout(xaxis_title='Date de mesure', yaxis_title='Niveau') #/ Profondeur')
    fig.update_layout(xaxis=dict(rangeslider=dict(visible=True), type='date'))
    # fig.show()
    st.plotly_chart(fig)
    

def get_statistics_by_month(df_historique):
    # Définir la localisation en français
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    # Verification que la colonne de date est bien de type 'datetime'
    df_historique['date_mesure'] = pd.to_datetime(df_historique['date_mesure'])
    # Extraction du mois et de l'année de la colonne de date
    df_historique['month'] = df_historique['date_mesure'].dt.month
    df_historique['year'] = df_historique['date_mesure'].dt.year
    # Calcul des statistiques par mois
    statistics_by_month = round(df_historique.groupby('month')['niveau_nappe_eau'].agg(['min', 'max', 'mean', 'median',lambda x: np.percentile(x, 25), lambda x: np.percentile(x, 75)]),2).reset_index()
    # Conversion du numéro du mois en nom de mois français
    statistics_by_month['month'] = statistics_by_month['month'].apply(lambda x: calendar.month_name[x].capitalize())
    # Renommage des colonnes pour une meilleure lisibilité
    statistics_by_month.rename(columns={statistics_by_month.columns[5]: '1er_quartile'}, inplace=True)
    statistics_by_month.rename(columns={statistics_by_month.columns[6]: '3eme_quartile'}, inplace=True)
    return statistics_by_month


def plot_quartile_median(df_historique,df_statistics_by_month, year):
    # Définir la localisation en français
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    # Verification que la colonne de date est bien de type 'datetime'
    df_historique['date_mesure'] = pd.to_datetime(df_historique['date_mesure'])
    # Extraction du mois et de l'année de la colonne de date
    df_historique['month'] = df_historique['date_mesure'].dt.month
    df_historique['year'] = df_historique['date_mesure'].dt.year
    # Filtration des statistiques pour l'année en cours
    statistics_year = df_statistics_by_month[df_statistics_by_month['month'].isin(df_historique[df_historique['year'] == year]['month'].apply(lambda x: calendar.month_name[x].capitalize()))]
    # Calcl de  la moyenne par mois pour l'année en cours
    df_year_mean = df_historique[(df_historique['year'] == year)].groupby('month')['niveau_nappe_eau'].mean().reset_index()
    # Utiliser le style seaborn
    sns.set(style="whitegrid", palette="pastel")
    # Tracer les graphiques d'aire 2D du 1er quartile, de la médiane et du 3ème quartile
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(df_statistics_by_month['month'], df_statistics_by_month['1er_quartile'], df_statistics_by_month['3eme_quartile'], alpha=0.5, label='Quartiles')
    ax.fill_between(df_statistics_by_month['month'], df_statistics_by_month['min'], df_statistics_by_month['max'], alpha=0.2, color='pink', label='Extremes')
    ax.plot(df_statistics_by_month['month'], df_statistics_by_month['median'], label='Médiane', marker='', color='royalblue')
    ax.scatter(df_year_mean['month'].apply(lambda x: calendar.month_name[x].capitalize()), df_year_mean['niveau_nappe_eau'], color='red', label=f'Moyenne {year}', marker='o')
    ax.set_xlabel('Mois')
    ax.set_ylabel('Niveau de la nappe phréatique')
    ax.set_title(f'Évolution de la nappe phréatique pour l\'année {year}')
    ax.legend()
    ax.set_xticklabels(df_statistics_by_month['month'], rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
#_______
    
def top_10_lowest_average(df_historique):
    """ Fonction permettant de calculer le top 10 des années avec le niveau moyen le plus bas"""
    # Calculer la moyenne par année
    df_yearly_mean = round(df_historique.groupby(df_historique['date_mesure'].dt.year)['niveau_nappe_eau'].mean(),1).reset_index()
    # Convertir les années en chaînes de caractères pour éviter le formatage par milliers de Streamlit
    df_yearly_mean['date_mesure'] = df_yearly_mean['date_mesure'].astype(str)
    # Trier par ordre croissant
    df_yearly_mean_sorted = df_yearly_mean.sort_values('niveau_nappe_eau')
    # Sélectionner les 10 premières années avec le niveau moyen le plus bas
    top_10_years = df_yearly_mean_sorted.head(10)
    # Réinitialiser l'index pour obtenir le classement de 1 à 10 et ajouter +1 car l'index commence par 0 par défaut
    top_10_years = top_10_years.reset_index(drop=True)
    top_10_years.index = top_10_years.index + 1
    return top_10_years
#_______

def top_10_highest_average(df_historique):
    """ Fonction permettant de calculer le top 10 des années avec le niveau moyen le plus élevé """
    # Calculer la moyenne par année
    df_yearly_mean = round(df_historique.groupby(df_historique['date_mesure'].dt.year)['niveau_nappe_eau'].mean(),1).reset_index()
    # Convertir les années en chaînes de caractères pour éviter le formatage par milliers de Streamlit
    df_yearly_mean['date_mesure'] = df_yearly_mean['date_mesure'].astype(str)
    # Trier par ordre décroissant
    df_yearly_mean_sorted = df_yearly_mean.sort_values('niveau_nappe_eau', ascending=False)
    # Sélectionner les 10 premières années avec le niveau moyen le plus élevé
    top_10_years = df_yearly_mean_sorted.head(10)
    # Réinitialiser l'index pour obtenir le classement de 1 à 10 et ajouter +1 car l'index commence par 0 par défaut
    top_10_years = top_10_years.reset_index(drop=True)
    top_10_years.index = top_10_years.index + 1
    return top_10_years
#_______




#--------------------------------------------------Dashboard--------------------------------------------------

def main():
    # Titre de la page
    st.markdown("<h2 style='text-align: center; color: black; font-size: 36px;'>Relevés Piézométriques</h2>", unsafe_allow_html=True)
    
    # Verification que la ville a bien été saisie
    ville = st.session_state.get("ville", None)
    rayon_km = st.session_state.get("rayon_km", None)
    bbox = st.session_state.get("bbox", None)
    
    if not (ville and rayon_km and bbox):
        # Afficher un message d'erreur si la ville n'a pas été saisie
        st.error("Veuillez vous rendre sur la page d'accueil afin de choisir une Localité.")
        return  # Arrêter l'exécution de la foction

    # Initialisation de la variable stations et choix_station
    stations = None  
    choix_station = None  
    
    # Récupération des stations piézométriques dans la boîte de géolocalisation
    if bbox:
        stations = get_piezometric_stations_in_bbox(bbox)
        if stations and stations['data']:
            st.success("Stations récupérées avec succès !")
            choix_station = st.sidebar.radio("Choisissez une station :", [x["code_bss"] for x in stations["data"]])
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
            st.info("""Une station piézométrique est un dispositif spécialement conçu pour mesurer le niveau de l'eau souterraine à un endroit donné. 
                     Cet outil se compose généralement d'un tube inséré dans le sol jusqu'à la nappe phréatique, et d'instruments permettant de lire le niveau d'eau à l'intérieur. 
                     Les données recueillies sont essentielles pour comprendre le comportement des nappes souterraines, évaluer les ressources en eau disponibles et surveiller les variations du niveau d'eau dues aux prélèvements, 
                     à la recharge naturelle ou aux activités humaines. La surveillance piézométrique est ainsi d'une grande utilité pour les gestionnaires de ressources en eau, 
                     les urbanistes, les agriculteurs et toute personne concernée par la préservation et l'utilisation durable de l'eau souterraine.""")
        else:
            st.warning("Aucune station piézométrique trouvée dans la boîte de géolocalisation.")


    # Récupération des données récentes de niveau de la nappe
    if stations and choix_station:
        st.header("Mesures recentes de la station")
        fig= historique_recent(choix_station)
        st.plotly_chart(fig, use_container_width=True, config={'locale': 'fr'})
        st.write("📊 **À propos de la tendance :**")
        st.info("Ce graphique illustre les données les plus récentes concernant la station que vous avez sélectionnée.")
        
    # Afficher les informations sur la station dans la sidebar
        for station in stations['data']:
            if station['code_bss'] == choix_station:
                st.sidebar.markdown("---")  # Ajout d'une ligne horizontale
                st.sidebar.markdown(f"**Informations sur la station :** {choix_station}")
                info_text = f"""
                **Département :** {station['dep']}  
                **Commune :** {station['commune']}  
                **Date de début de mesure :** {station['date_debut_mesure']}  
                **Date de la dernière mesure :** {station['date_fin_mesure']}  
                **Nombre de mesures :** {station['nb_mesures_piezo']}  
                **Coordonnées :** {station['coordonnées']}  
                    """
                st.sidebar.markdown(info_text)
                break
            
#### Tendance a long terme ####

    
    # Initialisation de l'état du bouton
    if 'bouton_historique' not in st.session_state:
        st.session_state['bouton_historique'] = False 
        
    # Si la ville a changé, réinitialisez l'état du bouton
    if st.session_state.get('previous_ville') != ville:
        st.session_state['bouton_historique'] = False
    st.session_state['previous_ville'] = ville  # Mettez à jour la valeur de la ville précédente      
    
    # Si le rayon_km a changé, réinitialisation de l'état du bouton
    if st.session_state.get('previous_rayon_km') != rayon_km:
        st.session_state['bouton_historique'] = False
    st.session_state['previous_rayon_km'] = rayon_km  # Mettre à jour la valeur du rayon précédent 
            
    # Bouton "Historique des mesures de la station"       
    with st.sidebar:
        if st.sidebar.button("Plus d'information sur le point de mesure"):
            st.session_state['bouton_historique'] = True

    # Bouton "Historique des mesures de la station"
    if st.session_state['bouton_historique']:
        st.header("Tendance à long terme ", choix_station)
        
        get_api_history_level(choix_station)
        # Chargement des données dans un DataFrame
        df_historique = charger_donnees_historique(choix_station)
        # Calcul des statistiques par mois
        df_statistics_by_month = get_statistics_by_month(df_historique)
        
        # Sélectionner une année
        selected_year = None
        years = sorted(df_historique['year'].unique(), reverse=True)
        selected_year =st.selectbox("Sélectionnez une année pour comparer son profil à l'ensemble des données", years)
        
        if selected_year:
            plot_quartile_median(df_historique,df_statistics_by_month, selected_year)
            st.write("📊 **En observant ce graphique, vous pouvez :**")

            st.info("- Saisir les **Tendances Mensuelles** : Voyez comment la ligne médiane se déplace d'un mois à l'autre. Une ligne ascendante indique une augmentation du niveau de la nappe, tandis qu'une ligne descendante indique une baisse.\n"
                    "\n"
                    "- Comprendre la **Variabilité** : La largeur de la zone interquartile (zone bleue) montre à quel point les niveaux varient. Une zone plus large indique une plus grande variabilité.\n"
                    "\n"
                    "- Identifier les **Périodes Anormales** : Repérez les périodes où les niveaux sont exceptionnellement bas ou élevés, indiquées par des valeurs en dehors de la zone des extrêmes.\n"
                    "\n"
                    "- Comparer aux **Moyennes** : Les points rouges connectés marquent les moyennes mensuelles. Comparez-les avec la médiane pour comprendre si les valeurs sont généralement plus élevées ou plus basses que la moyenne.\n"
                    "\n"
                    "Ces indices vous offrent une meilleure compréhension des schémas de variation des niveaux de la nappe phréatique. Ils vous aident à décrypter les fluctuations et les conditions générales de l'eau souterraine tout au long de l'année.")

            # Afficher les statistiques par mois
            st.subheader("La station " + choix_station + " en chiffres...")
            st.write("\n\n")
       
            cola, colb= st.columns([1,1])
            #Afficher le top 10 des années les plus sèches
            with cola:
                st.write("📊 **Top 10 des années les plus seches**")
                top_10_lowest = top_10_lowest_average(df_historique)
                st.dataframe(top_10_lowest)
            #Afficher le top 10 des années les plus humides
            with colb:
                st.write("📊 **Top 10 des années les plus humides**")
                top_10_highest= top_10_highest_average(df_historique)
                st.dataframe(top_10_highest)
            st.write("\n\n")
            # Afficher les statistiques par mois
            st.write("📊 **Statistiques mensuelles**")
            st.dataframe(df_statistics_by_month)
            # Afficher le graphique de l'historique complet
            st.write("\n\n")
            if st.button("Voir l'historique complet du point de mesure"):
                graph_hystory_complete(df_historique)    
            


if __name__ == "__main__":
    main()


#--------------------------------------------------version sauvegarde--------------------------------------------------