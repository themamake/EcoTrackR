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
from datetime import datetime
import calendar
import locale


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

def convert_date_format(date_str):
    " Fonction permettant de convertir une date au format AAAA-MM-JJ en JJ-MM-AAAA"
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime('%d-%m-%Y')
#_______

def get_Hydrometric_stations_in_bbox(bbox):
    """ 
    Ce service permet d'interroger les stations du référentiel hydrométrique. Une station peut porter des observations de hauteur et/ou de débit (directement mesurés ou calculés à partir d'une courbe de tarage).
    Si la valeur du paramètre size n'est pas renseignée, la taille de page par défaut : 1000, taille max de la page : 10000.
    La profondeur d'accès aux résultats est : 20000, calcul de la profondeur = numéro de la page * nombre maximum de résultats dans une page.
    Trie par défaut : code_station asc
    """
    url = "https://hubeau.eaufrance.fr/api/v1/hydrometrie/referentiel/stations?"
    params = {"bbox": bbox, "size": "100"}  # Nombre maximal de stations à récupérer
    response = requests.get(url, params=params)
    # Vérifier si la requête a réussi
    if response.status_code == 200 or response.status_code == 206:
        contenu = response.json()
    # Vérifier si la réponse contient des données
        if "data" not in contenu or len(contenu["data"]) == 0:
            print("Il n'y a pas de stations Hydrologique dans la zone de recherche.")
            return None    
    # Filtrer les stations dont le champ 'en_service' est à True
        data = [{
            "code_station": x["code_station"],
            "libelle_station": x["libelle_station"],
            "commune": x["libelle_commune"],
            "dep" : x["code_departement"],
            "date_ouverture_station": x["date_ouverture_station"],
            "date_maj_station": x["date_maj_station"],
            "en_service": x["en_service"],
            "date_fermeture_station": x["date_fermeture_station"],
            "libelle_cours_eau": x["libelle_cours_eau"],
            "coordonnées": [x["longitude_station"], x["latitude_station"]]
        } for x in contenu["data"] if x["en_service"]] 
        nbre_station = len(data)
        resumed_info = {"nbre_station": nbre_station}
        resumed_info.update({ "data": data})
        if len(data) == 0:
            print("Il n'y a pas de stations piézométriques dans la zone de recherche.")
        return resumed_info
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
    geolocator = Nominatim(user_agent="geoapiExercises")
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

@st.cache_data()
def get_api_debit(code_station):
    """
    cette fonction permet de lister les observations dites "temps réel" portées par le référentiel (sites et stations hydrométriques), à savoir les séries de données de hauteur d'eau (H) et de débit (Q).
    Si la valeur du paramètre size n'est pas renseignée, la taille de page par défaut : 1000, taille max de la page : 20000.
    Il n'y a pas de limitation sur la profondeur d'accès aux résultats.
    Trie par défaut : date_obs desc
    """
    url = "http://hubeau.eaufrance.fr/api/v1/hydrometrie/observations_tr"
    params = {"code_entite": code_station, "size": 20000}
    # Récupérer les données
    response = requests.get(url, params=params)
    # Vérifier si la requête a réussi
    if response.status_code == 200 or response.status_code == 206:
        contenu = response.json()
        
    # Filtrage des données pour ne garder que celles où grandeur_hydro est 'H' (hauteur d'eau) 
        filtered_data = [{"date_mesure": observation["date_obs"], "Débit": observation["resultat_obs"]} 
                         for observation in contenu['data'] 
                        if observation['grandeur_hydro'] == 'Q']
        return filtered_data
    else:
        print("Erreur lors de la récupération des données. Statut de la réponse:", response.status_code)
#_______

def historique_recent(code_station):
    """ Cette fonction permet de tracer l'historique récent du débit d'une station hydrométrique."""
    json_data = get_api_debit(code_station)
    # Convertir les données en DataFrame
    df = pd.DataFrame(json_data)
    #  Convertir la colonne 'date_mesure' en datetime
    df['date_mesure'] = pd.to_datetime(df['date_mesure'])
    # Convertir la colonne 'Débit' en float et diviser par 1000 pour obtenir le débit en m3/s
    df['Débit'] = df['Débit'].div(1000)
    # Tracer le graphique
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date_mesure'], y=df['Débit'], mode='lines', name='Débit du cours d\'eau'))
    fig.update_layout(xaxis_title='Date de mesure', yaxis_title='Débit m3/s')
    fig.update_layout(xaxis=dict(rangeslider=dict(visible=True), type='date'))
    fig.update_layout(
    #autosize=True,  
    width=1075,
    height=400,
    margin=dict(l=0, r=0, t=0, b=0),  # Définition des marges du graphique à 0 pour supprimer la bordure
    paper_bgcolor="rgba(0,0,0,0)",  # Définition de la couleur de l'arrière-plan du graphique sur transparent
    plot_bgcolor="rgba(0,0,0,0)",  # Définition de la couleur de l'arrière-plan du tracé sur transparent
    modebar={'orientation': 'v'}
        )
    return fig
#                                                       --------------------------------------

def get_api_history_debit(code_station):
    """Cette fonction permet de récupérer les données historiques de débit moyen mensuel d'une station hydrométrique."""
    url = "http://hubeau.eaufrance.fr/api/v1/hydrometrie/obs_elab"
    params = {"code_entite": code_station,  "grandeur_hydro_elab":"QmM" , "size": 20000}
    # Récupération des données
    response = requests.get(url, params=params)
    # Vérification du statut de la réponse
    if response.status_code == 200 or response.status_code == 206:
        contenu = response.json()
    # Filtrage des données pour ne garder que celles où grandeur_hydro est 'QmM' et extraction seulement de la date et du résultat
        filtered_data = [{"date_mesure": observation["date_obs_elab"], "QmM": observation["resultat_obs_elab"]} 
                         for observation in contenu['data']]
        return filtered_data
    else:
        print("Erreur lors de la récupération des données. Statut de la réponse:", response.status_code)
#_______

def charger_donnees_historique(code_station):
    """ Cette fonction permet de charger les données historiques de débit d'une station hydrométrique."""
    json_data = get_api_history_debit(code_station)
    df_history = pd.DataFrame(json_data)
    # Convertir la colonne 'date_mesure' en datetime
    df_history['date_mesure'] = pd.to_datetime(df_history['date_mesure'])
    # Convertir la colonne 'Débit' en float et diviser par 1000 pour obtenir le débit en m3/s
    df_history['QmM'] = df_history['QmM'].div(1000)
    return df_history
#_______

def get_statistics_by_month(df_historique):
    """Fonction qui calcule les statistiques par mois  du débit moyen mensuel"""
    # Définir la localisation en français
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    # Convertir la colonne de date en datetime
    df_historique['date_mesure'] = pd.to_datetime(df_historique['date_mesure'])
    # Extraire le mois et l'année de la colonne de date
    df_historique['month'] = df_historique['date_mesure'].dt.month
    df_historique['year'] = df_historique['date_mesure'].dt.year
    # Calculer les statistiques par mois
    statistics_by_month = round(df_historique.groupby('month')['QmM'].agg(['min', 'max', 'mean', 'median',lambda x: np.percentile(x, 25), lambda x: np.percentile(x, 75)]),2).reset_index()
    # Convertir le numéro du mois en nom de mois en français
    statistics_by_month['month'] = statistics_by_month['month'].apply(lambda x: calendar.month_name[x].capitalize())
    # Renommer les colonne "<lambda>" en "1er  et 3eme quartile"
    statistics_by_month.rename(columns={statistics_by_month.columns[5]: '1er_quartile'}, inplace=True)
    statistics_by_month.rename(columns={statistics_by_month.columns[6]: '3eme_quartile'}, inplace=True)
    return statistics_by_month
#_______

def plot_quartile_median(df_historique,statistics_by_month, year):
    """Fonction permettant de tracer les graphiques d'aire 2D du 1er quartile, de la médiane et du 3ème quartile. """
    # Définir la localisation en français
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    # Verification que la colonne de date est bien de type 'datetime'
    df_historique['date_mesure'] = pd.to_datetime(df_historique['date_mesure'])
    # Extraction du mois et de l'année de la colonne de date
    df_historique['month'] = df_historique['date_mesure'].dt.month
    df_historique['year'] = df_historique['date_mesure'].dt.year
    # Calcl de  la moyenne par mois pour l'année en cours
    df_year_mean = df_historique[(df_historique['year'] == year)].groupby('month')['QmM'].mean().reset_index()
    # Utiliser le style seaborn
    sns.set(style="whitegrid", palette="pastel")
    # Tracer les graphiques d'aire 2D du 1er quartile, de la médiane et du 3ème quartile
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(statistics_by_month['month'], statistics_by_month['1er_quartile'], statistics_by_month['3eme_quartile'], alpha=0.5, label='Quartiles')
    ax.fill_between(statistics_by_month['month'], statistics_by_month['min'], statistics_by_month['max'], alpha=0.2, color='pink', label='Extremes')
    ax.plot(statistics_by_month['month'], statistics_by_month['median'], label='Médiane', marker='', color='royalblue')
    ax.scatter(df_year_mean['month'].apply(lambda x: calendar.month_name[x].capitalize()), df_year_mean['QmM'], color='red', label=f'Moyenne {year}', marker='o')
    ax.set_xlabel('Mois')
    ax.set_ylabel('Débits (m3/s)')
    ax.set_title(f'Évolution des debits mesurés sur la station pour l\'année {year}')
    ax.legend()
    ax.set_xticklabels(statistics_by_month['month'], rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

#_______

def top_10_lowest_average(df_historique):
    """ Fonction permettant de calculer le top 10 des années avec le debit moyen le plus bas"""""
    # Calculer la moyenne par année
    df_yearly_mean = round(df_historique.groupby(df_historique['date_mesure'].dt.year)['QmM'].mean(),1).reset_index()
    # Convertir les années en chaînes de caractères pour éviter le formatage par milliers de Streamlit
    df_yearly_mean['date_mesure'] = df_yearly_mean['date_mesure'].astype(str)
    # Convertir la colonne 'QmM' en chaîne de caractères
    df_yearly_mean['QmM'] = df_yearly_mean['QmM'].astype(str)
    # Trier par ordre croissant
    df_yearly_mean_sorted = df_yearly_mean.sort_values('QmM')
    # Sélectionner les 10 premières années avec le niveau moyen le plus bas
    top_10_years = df_yearly_mean_sorted.head(10)
    # Réinitialiser l'index pour obtenir le classement de 1 à 10 et ajouter +1 car l'index commence par 0 par défaut
    top_10_years = top_10_years.reset_index(drop=True)
    top_10_years.index = top_10_years.index + 1
    return top_10_years
#_______

def top_10_highest_average(df_historique):
    """ Fonction permettant de calculer le top 10 des années avec le debit moyen le plus élevé"""
    # Calculer la moyenne par année
    df_yearly_mean = round(df_historique.groupby(df_historique['date_mesure'].dt.year)['QmM'].mean(),1).reset_index()
    # Convertir les années en chaînes de caractères pour éviter le formatage par milliers de Streamlit
    df_yearly_mean['date_mesure'] = df_yearly_mean['date_mesure'].astype(str)
    # Convertir la colonne 'QmM' en chaîne de caractères
    df_yearly_mean['QmM'] = df_yearly_mean['QmM'].astype(str)
    # Trier par ordre décroissant
    df_yearly_mean_sorted = df_yearly_mean.sort_values('QmM', ascending=False)
    # Sélectionner les 10 premières années avec le niveau moyen le plus élevé
    top_10_years = df_yearly_mean_sorted.head(10)
    # Réinitialiser l'index pour obtenir le classement de 1 à 10 et ajouter +1 car l'index commence par 0 par défaut
    top_10_years = top_10_years.reset_index(drop=True)
    top_10_years.index = top_10_years.index + 1
    return top_10_years
#_______

def graph_hystory_complete(df):
    fig = go.Figure()
    #fig.add_trace(go.Scatter(x=df['date_mesure'], y=df['profondeur_nappe'], mode='lines', name='Profondeur de nappe'))
    fig.add_trace(go.Scatter(x=df['date_mesure'], y=df['QmM'], mode='lines', name='Débit moyen mensuel'))
    fig.update_layout(
    autosize=True,  # Utilisez l'espace disponible
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
    

#--------------------------------------------------Dashboard--------------------------------------------------


def main():
    # Titre de la page
    st.markdown("<h2 style='text-align: center; color: black; font-size: 36px;'>Relevés Hydrometriques</h2>", unsafe_allow_html=True)
    
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
    # Récupération des stations hydrométriques dans la boîte de géolocalisation
    if bbox:
        stations = get_Hydrometric_stations_in_bbox(bbox)
        if stations and stations['data']:
            st.success("Stations récupérées avec succès !")
            
    # Création d'une liste d'options pour le selectbox
            #options = [(x['libelle_station'], x['code_station']) for x in stations["data"]]
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
            st.info("""Les stations hydrométriques jouent un rôle essentiel dans la surveillance et la gestion des ressources en eau d'un pays ou d'une région. 
                     Ces stations sont spécialement conçues pour mesurer le débit des rivières, des cours d'eau et des canaux.  
                     Le débit est une mesure du volume d'eau qui s'écoule à travers une section de la rivière par unité de temps, généralement exprimé en mètres cubes par seconde (m³/s).
                     Le débit des rivières peut varier en fonction des précipitations, de la fonte des neiges, des barrages, des retraits pour l'irrigation ou d'autres utilisations, 
                     et même des interventions humaines comme les dérivations ou les rejets. Surveiller ces variations est donc crucial pour optimiser la gestion des ressources en eau
                    prevenir les innondations ou proteger les ecosystèmes aquatiques.""")
        else:
            st.warning("Aucune station piézométrique trouvée dans la boîte de géolocalisation.")
            
    # Récupération des données récentes de niveau de la nappe
    if stations and choix_station:
        data = get_api_debit(choix_station)
        if not data:   #  si data est une liste vide
            st.warning("Pas de mesure disponible durant les 30 derniers jours, veuillez choisir une autre station.")
        else:
            st.header("Mesures recentes de la station")
            fig= historique_recent(choix_station)
            st.plotly_chart(fig, use_container_width=True)
            st.write("📊 **À propos de la tendance :**")
            st.info("Ce graphique illustre les données les plus récentes concernant la station que vous avez sélectionnée.") 
        
            
    # Afficher les informations sur la station dans la sidebar
        for station in stations['data']:
            if station['code_station'] == choix_station:
                st.sidebar.markdown("---")  # Ajout d'une ligne horizontale
                st.sidebar.markdown(f"**Informations sur la station :** {choix_station}")
                # Reformater les dates
                date_ouverture = datetime.strptime(station['date_ouverture_station'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d-%m-%Y')
                date_maj = datetime.strptime(station['date_maj_station'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d-%m-%Y')
                info_text = f"""
                **Département :** {station['dep']}  
                **Commune :** {station['commune']}  
                **Cours d'eau:** {station["libelle_cours_eau"]}  
                **Date de début de mesure :** {date_ouverture}  
                **Date de mise à jour de la station:** {date_maj}   
                **Coordonnées :** {station['coordonnées']}  
                    """
                st.sidebar.markdown(info_text)
                break
            
#### Tendance a long terme ####

    # Initialisation de l'état du bouton
    if 'bouton_historique_hydro' not in st.session_state:
        st.session_state['bouton_historique_hydro'] = False 
        
    # Si la ville a changé, réinitialisation de l'état du bouton
    if st.session_state.get('previous_ville') != ville:
        st.session_state['bouton_historique_hydro'] = False
    st.session_state['previous_ville'] = ville  # Mettre à jour la valeur de la ville précédente    
    
    # Si le rayon_km a changé, réinitialisation de l'état du bouton
    if st.session_state.get('previous_rayon_km') != rayon_km:
        st.session_state['bouton_historique_hydro'] = False
    st.session_state['previous_rayon_km'] = rayon_km  # Mettre à jour la valeur du rayon précédent 
            
            
    # Bouton "Historique des mesures de la station"       
    with st.sidebar:
        if st.sidebar.button("Plus d'information sur le point de mesure"):
            st.session_state['bouton_historique_hydro'] = True

    # Bouton "Historique des mesures de la station"
    if st.session_state['bouton_historique_hydro']:
        st.header("Tendance à long terme ", choix_station)
        
        data= get_api_history_debit(choix_station)
        if not data:   #  si data est une liste vide
            st.warning("Pas d'historique disponible, veuillez choisir une autre station.")
        else:
        # Chargement des données dans un DataFrame
            df_historique = charger_donnees_historique(choix_station)
            statistics_by_month = get_statistics_by_month(df_historique)

            # Sélectionner une année
            selected_year = None
            years = sorted(df_historique['year'].unique(), reverse=True)
            selected_year =st.selectbox("Sélectionnez une année pour comparer son profil à l'ensemble des données", years)
            
            if selected_year:
                plot_quartile_median(df_historique,statistics_by_month, selected_year)
                st.write("📊 **En observant ce graphique, vous pouvez :**")

                st.info("- Saisir les **Tendances Mensuelles** : Voyez comment la ligne médiane se déplace d'un mois à l'autre. Une ligne ascendante indique une augmentation du débit du cours d'eau, tandis qu'une ligne descendante indique une baisse.\n"
                    "\n"
                    "- Comprendre la **Variabilité** : La largeur de la zone interquartile (zone bleue) montre à quel point les débits varient. Une zone plus large indique une plus grande variabilité.\n"
                    "\n"
                    "- Identifier les **Périodes Anormales** : Repérez les périodes où les debits sont exceptionnellement bas ou élevés, indiquées par des valeurs en dehors ou proche de la zone des extrêmes.\n"
                    "\n"
                    "- Comparer aux **Moyennes** : Les points rouges marquent les moyennes mensuelles. Comparez-les avec la médiane pour comprendre si les valeurs sont généralement plus élevées ou plus basses que la moyenne.\n"
                    "\n"
                    "Ces indices vous offrent une meilleure compréhension des schémas de variation des debits d un cours d'eau. Ils vous aident à décrypter les fluctuations et les conditions générales de l'eau de surface tout au long de l'année.")
                

                st.write("\n\n")
                st.header("La station " + choix_station + " en chiffres...")
                st.write("\n\n")
            
            cola, colb= st.columns([1,1])
            with cola:
                st.write("📊 **Top 10 des années les plus seches**")
                top_10_lowest = top_10_lowest_average(df_historique)
                st.dataframe(top_10_lowest)
            with colb:
                st.write("📊 **Top 10 des années les plus humides**")
                top_10_highest= top_10_highest_average(df_historique)
                st.dataframe(top_10_highest)
            st.write("\n\n")
            
            st.write("📊 **Statistiques mensuelles**")
            # Convertir les colonnes numériques concernées en chaînes de caractères
            df_display = statistics_by_month.copy()
            for column in ['min', 'max', 'mean', 'median', '1er_quartile', '3eme_quartile']:
                df_display[column] = df_display[column].astype(str)
            st.dataframe(df_display)
            
            st.write("\n\n")
            if st.button("Voir l'historique complet du point de mesure"):
                graph_hystory_complete(df_historique)    
            
               
            
if __name__ == "__main__":
    main()
