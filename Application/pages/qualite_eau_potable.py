import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

@st.cache  # Caching the function to speed up subsequent calls
def fetch_data_from_api(ville):
    url_udi = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/communes_udi"
    params_udi = {
        "nom_commune": ville
    }
    
    response_udi = requests.get(url_udi, params=params_udi)
    
    if response_udi.status_code != 200:
        return None

    data_udi = response_udi.json()
    df_udi = pd.DataFrame(data_udi['data'])  # Convert UDI data to DataFrame
    
    # Extract UDI codes for the selected city
    udi_codes = df_udi['code_reseau'].tolist()
    
    all_data = []
    # Limiting to the first 5 UDI codes
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
    return df_analysis

def main():
    st.title("Qualité de l'eau potable - Résultats d'Analyses")
    
    # Retrieve session state values
    ville = st.session_state.get("ville", None)
    rayon_km = st.session_state.get("rayon_km", None)
    
    st.write(f"Ville sélectionnée: {ville}")
    st.write(f"Rayon sélectionné: {rayon_km} km")

    df_analysis = fetch_data_from_api(ville)
    
    if df_analysis is not None:
        # Display the data as a table
        st.write("Informations sur les résultats d'analyses pour la ville sélectionnée :")
        st.dataframe(df_analysis)
        
        # Plotting the temperature over time
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(x=df_analysis[df_analysis['libelle_parametre'] == "Température de l'eau"]['date_prelevement'], 
                                      y=df_analysis[df_analysis['libelle_parametre'] == "Température de l'eau"]['resultat_numerique'],
                                      mode='lines+markers', name='Température'))
        fig_temp.update_layout(title='Évolution de la Température de l\'eau au fil du temps',
                               xaxis_title='Date de Prélèvement', yaxis_title='Température (°C)')
        st.plotly_chart(fig_temp)

        # Plotting the pH over time
        fig_ph = go.Figure()
        fig_ph.add_trace(go.Scatter(x=df_analysis[df_analysis['libelle_parametre'] == "pH"]['date_prelevement'], 
                                    y=df_analysis[df_analysis['libelle_parametre'] == "pH"]['resultat_numerique'],
                                    mode='lines+markers', name='pH'))
        fig_ph.update_layout(title='Évolution du pH de l\'eau au fil du temps',
                             xaxis_title='Date de Prélèvement', yaxis_title='pH')
        st.plotly_chart(fig_ph)
        
    else:
        st.error(f"Erreur lors de la récupération des informations.")

if __name__ == "__main__":
    main()
