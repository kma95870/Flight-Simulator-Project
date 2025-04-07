import streamlit as st
import pandas as pd
import plotly.express as px
import boto3
import json
import time
from io import BytesIO

# Configuration du client S3
s3_client = boto3.client(
    's3',
    aws_access_key_id='YOUR ACCESS KEY',
    aws_secret_access_key='YOUR SECRET KEY',
    region_name='us-west-1'  # Change selon ta région AWS
)
bucket_name = "flight-simulator-data"
prefix = "data/"

st.set_page_config(page_title="Flight Simulator Dashboard", layout="wide")

st.title("🛫 Flight Simulator - Real-Time Dashboard")

# Récupérer TOUS les fichiers JSON depuis S3
def get_all_flight_data():
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' not in response:
            st.warning("Aucun fichier trouvé dans le bucket.")
            return []
        
        data = []
        for file in response['Contents']:
            file_key = file['Key']
            obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            file_content = obj['Body'].read().decode('utf-8')
            data.append(json.loads(file_content))
        
        return data
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return []

# Fonction pour obtenir le vol avec le timestamp le plus récent pour chaque flight_id
def get_latest_flight_per_id(flight_data):
    # Créer un dictionnaire pour stocker les dernières données de chaque vol
    latest_flights = {}
    
    for entry in flight_data:
        flight_id = entry['flight_id']
        timestamp = entry['timestamp']
        
        # Si le vol n'existe pas encore ou si le timestamp est plus récent, on met à jour
        if flight_id not in latest_flights or timestamp > latest_flights[flight_id]['timestamp']:
            latest_flights[flight_id] = entry

    return list(latest_flights.values())

# Ajouter une couleur unique pour chaque vol (en fonction du flight_id)
def add_color_column(df):
    # Générer une couleur unique pour chaque flight_id en utilisant le hash
    df['color'] = df['flight_id'].apply(lambda x: f'#{hash(x) & 0xFFFFFF:06x}')
    return df

# Streamlit live update
placeholder = st.empty()

while True:
    flight_data = get_all_flight_data()
    
    # Obtenir les dernières données pour chaque vol
    latest_flight_data = get_latest_flight_per_id(flight_data)
    df = pd.DataFrame(latest_flight_data)
    
    # Ajouter des couleurs uniques pour chaque vol
    df = add_color_column(df)

    with placeholder.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌍 Positions des avions (Vue large et fixe)")
            if not df.empty:
                # Utilisation de hover_data pour ajouter des informations supplémentaires
                fig = px.scatter_mapbox(df, 
                                        lat="latitude", lon="longitude", 
                                        hover_name="flight_id", 
                                        hover_data=["airline", "altitude", "speed", "status"], 
                                        zoom=1,  # Zoom global sur le monde
                                        height=600,  # Ajuste la hauteur pour meilleure visibilité
                                        color="color",  # Utilisation de la colonne 'color' pour l'attribution des couleurs
                                        color_discrete_map="identity")  # Utilise les couleurs assignées

                # 🔹 Fixer la carte avec une vue mondiale
                fig.update_layout(
                    mapbox_style="open-street-map",
                    mapbox_center={"lat": 20, "lon": 0},  # Centrage sur l'Atlantique
                    dragmode=False  # Empêche la carte de bouger automatiquement
                )
                
                # Ajout d'un `key` unique pour le graphique Plotly
                st.plotly_chart(fig, key=f"flight_map_{int(time.time())}")  # Utilisation du timestamp comme clé unique
            else:
                st.warning("Aucune donnée disponible.")
        
        with col2:
            st.subheader("📋 Détails des vols")
            st.dataframe(df)

    time.sleep(30)  # Rafraîchissement toutes les 30 secondes