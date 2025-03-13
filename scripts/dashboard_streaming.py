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
    aws_access_key_id='YOUR ACCESS KEY ID',
    aws_secret_access_key='YOUR SECRET ACCESS KEY',
    region_name='us-west-1'  # Change selon ta région AWS
)
bucket_name = "flight-simulator-data"
prefix = "data/"

st.set_page_config(page_title="Flight Simulator Dashboard", layout="wide")

st.title("🛫 Flight Simulator - Real-Time Dashboard")

# Récupérer les fichiers JSON les plus récents depuis S3
def get_latest_flight_data():
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    if 'Contents' not in response:
        return []
    
    latest_files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[:5]
    data = []
    
    for file in latest_files:
        file_key = file['Key']
        obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = obj['Body'].read().decode('utf-8')
        data.append(json.loads(file_content))
    
    return data

# Streamlit live update
placeholder = st.empty()

while True:
    flight_data = get_latest_flight_data()
    df = pd.DataFrame(flight_data)
    
    with placeholder.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Positions des avions")
            if not df.empty:
                fig = px.scatter_mapbox(df, 
                                        lat="latitude", lon="longitude", 
                                        hover_name="flight_id", 
                                        hover_data=["airline", "altitude", "speed", "status"], 
                                        zoom=2, height=500)
                fig.update_layout(mapbox_style="open-street-map")
                st.plotly_chart(fig)
            else:
                st.warning("Aucune donnée disponible.")
        
        with col2:
            st.subheader("Détails des vols")
            st.dataframe(df)
    
    time.sleep(5)  # Rafraîchissement toutes les 5 secondes
