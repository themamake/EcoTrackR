import streamlit as st
import requests
import pandas as pd

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
max-width: 100%;  /* Modification ici pour s'étendre sur toute la largeur */
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


def fetch_data_from_api(ville):
    url_udi = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/communes_udi"
    params_udi = {
        "nom_commune": ville
    }
    
    response_udi = requests.get(url_udi, params=params_udi)
    
    if response_udi.status_code != 200 :
        return None

    data_udi = response_udi.json()
    df_udi = pd.DataFrame(data_udi['data'])  # Convert UDI data to DataFrame
    
    # Extract UDI codes for the selected city
    udi_codes = df_udi['code_reseau'].tolist()
    
    all_data = []
    for udi_code in udi_codes[:5]:  
        next_url = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/resultats_dis"
        params_analysis = {
            "code_reseau": udi_code,
            "nom_commune": ville,
            "page": 1,
            "size": 20
        }

        response_analysis = requests.get(next_url, params=params_analysis)
                
        if response_analysis.status_code in [200, 206]:
            data_analysis = response_analysis.json()
            all_data.extend(data_analysis['data'])

    df_analysis = pd.DataFrame(all_data)
    columns_to_remove = ['reference_analyse', 'code_installation_amont', 'nom_installation_amont', 'reseaux', 
                      'libelle_unite', 'libelle_parametre_web', 'code_type_parametre', 
                     'code_lieu_analyse', 'code_departement', 'nom_departement', 'code_prelevement', 
                     'code_parametre', 'code_parametre_se' ,'nom_uge',	'nom_distributeur','nom_moa','code_parametre_cas','reference_qualite_parametre',
                    'libelle_parametre',	'libelle_parametre_maj',	'resultat_alphanumerique',	'resultat_numerique',	'code_unite',	'limite_qualite_parametre'	]

    df_analysis = df_analysis.drop(columns=columns_to_remove)
    return df_analysis

def get_conformity_color(value, parameter):
    if parameter == "pH":
        if 6.5 <= value <= 9.5:
            return "green"
        elif 6.0 <= value <= 6.5 or 9.5 <= value <= 10:
            return "yellow"
        else:
            return "red"
    elif parameter == "Chlore libre":
        if 0.2 <= value <= 0.5:
            return "green"
        elif value < 0.2 or 0.5 <= value <= 1.0:
            return "yellow"
        else:
            return "red"
    else:
        return "gray"

def conformity_tooltip(parameter, value):
    if parameter == "pH":
        if 6.5 <= value <= 9.5:
            return "Conforme (6.5 à 9.5)"
        elif 6.0 <= value <= 6.5 or 9.5 <= value <= 10:
            return "Intermédiaire (6.0 à 6.5 ou 9.5 à 10)"
        else:
            return "Non conforme (< 6.0 ou > 10)"
    elif parameter == "Chlore libre":
        if 0.2 <= value <= 0.5:
            return "Conforme (0.2 à 0.5 mg/L)"
        elif value < 0.2 or 0.5 <= value <= 1.0:
            return "Intermédiaire (< 0.2 mg/L ou 0.5 à 1.0 mg/L)"
        else:
            return "Non conforme (> 1.0 mg/L)"
    else:
        return ""

def conformity_to_html(value):
    """
    Convert conformity letters to colored pills (HTML span elements)
    """
    mapping = {
        "C": "<span style='color: green;'>&#11044;</span>",
        "N": "<span style='color: red;'>&#11044;</span>",
        "D": "<span style='color: yellow;'>&#11044;</span>",
        "S": "<span style='color: grey;'>&#11044;</span>",
        "": "<span style='color: grey;'>&#11044;</span>"  # for empty value
    }
    return mapping.get(value, value)

def transform_conformity_columns(df):
    columns_to_transform = [
        'conformite_limites_bact_prelevement',
        'conformite_limites_pc_prelevement',
        'conformite_references_bact_prelevement',
        'conformite_references_pc_prelevement'
    ]
    for col in columns_to_transform:
        df[col] = df[col].apply(conformity_to_html)
    return df

def main():
    st.markdown("""<style>
    table.dataframe {
    border-collapse: collapse;
    border-spacing: 10px;
    width: 10%;
    table-layout: auto;
}
table.dataframe th, table.dataframe td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}
table.dataframe th {
    padding-top: 12px;
    padding-bottom: 12px;
    background-color: #f2f2f2;
    padding-left: 12px;
}
</style>
"""
, unsafe_allow_html=True)
    st.title("Qualité de l'eau potable - Résultats d'Analyses")
    ville = st.session_state.get("ville", None)
    df_analysis = fetch_data_from_api(ville)

    if df_analysis is not None:
        # Ajout des pastilles de conformité au dataframe
        df_analysis = transform_conformity_columns(df_analysis)
        
        # Affichage des données sous forme de tableau avec les pastilles de conformité
        st.write("Informations sur les résultats d'analyses pour la ville sélectionnée (5 premières lignes) :")
        st.markdown(df_analysis.head(5).to_html(escape=False), unsafe_allow_html=True)
        
        # Affichage des légendes
        st.subheader("Légende")
        legend_html = (
            "<span title='Conforme' style='color: green;'>&#11044;</span> Conforme "
            "<span title='Intermédiaire' style='color: yellow;'>&#11044;</span> Intermédiaire "
            "<span title='Non conforme' style='color: red;'>&#11044;</span> Non conforme <br> <br>"
            "conformite_limites_bact_prelevement:  Conformité bactériologique du prélèvement aux limites de qualité en vigueur au moment du prélèvement pour le type d'eau considéré. Valeurs possibles : vide / C : conforme / N : non conforme / D : conforme dans le cadre d’une dérogation / S : sans objet : lorsqu'aucun paramètre du type considéré (bactériologique ou chimique) n'a été mesuré <br> <br>" 
            "conformite_limites_pc_prelevement Conformité chimique du prélèvement aux limites de qualité en vigueur au moment du prélèvement pour le type d'eau considéré. Valeurs possibles : vide / C : conforme / N : non conforme / D : conforme dans le cadre d’une dérogation / S : sans objet : lorsqu'aucun paramètre du type considéré (bactériologique ou chimique) n'a été mesuré <br> <br> "
            "conformite_references_bact_prelevement Conformité bactériologique du prélèvement aux références de qualité en vigueur au moment du prélèvement pour le type d'eau considéré. Valeurs possibles : vide / C : conforme / N : non conforme / D : conforme dans le cadre d’une dérogation / S : sans objet : lorsqu'aucun paramètre du type considéré (bactériologique ou chimique) n'a été mesuré <br> <br>"
            "conformite_references_pc_prelevement Conformité chimique du prélèvement aux références de qualité en vigueur au moment du prélèvement pour le type d'eau considéré. Valeurs possibles : vide / C : conforme / N : non conforme / D : conforme dans le cadre d’une dérogation / S : sans objet : lorsqu'aucun paramètre du type considéré (bactériologique ou chimique) n'a été mesuré <br> <br>"
        
        
        
        
        )
        st.markdown(legend_html, unsafe_allow_html=True)
    else:
        st.error(f"Erreur lors de la récupération des informations.")

if __name__ == "__main__":
    main()





