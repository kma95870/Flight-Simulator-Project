from kafka import KafkaProducer
import json
import time
import random
from faker import Faker
from kafka import KafkaAdminClient
from datetime import datetime
import boto3


try:
    admin_client = KafkaAdminClient(bootstrap_servers="localhost:9092")
    print("Connexion à Kafka réussie !")
except Exception as e:
    print("Impossible de se connecter à Kafka. Vérifie que le broker est bien lancé.")
    print(f"Erreur : {e}")
    exit(1)

# Initialisation
fake = Faker()

fake = Faker()
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',  # Remplace par ton serveur Kafka si besoin
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Configuration du client S3
s3_client = boto3.client(
    's3',
    aws_access_key_id='YOUR ACCESS KEY ID',
    aws_secret_access_key='YOUR SECRET ACCESS KEY',
    region_name='us-west-1'  # Change selon ta région AWS
)

bucket_name = "flight-simulator-data"

def generate_flight_data():
    return {
        "flight_id": fake.uuid4(),
        "airline": random.choice(["Air France", "Lufthansa", "Delta", "Emirates", "KLM"]),
        "latitude": round(random.uniform(-90, 90), 6),
        "longitude": round(random.uniform(-180, 180), 6),
        "altitude": random.randint(1000, 40000),
        "speed": random.randint(200, 900),
        "direction": random.randint(0, 360),
        "status": random.choice(["En vol", "Atterrissage", "Décollage", "Retard"]),
        "timestamp": time.time()
    }

def upload_to_s3(data):
    file_name = f"flight_data_{int(time.time())}.json"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=f"data/{file_name}",  # Stocke les fichiers dans un dossier "data" dans S3
        Body=json.dumps(data)
    )
    print(f"Données stockées sur S3 : {file_name}")

if __name__ == "__main__":
    topic_name = "flight_data"
    print(f"Envoi des données de vol vers Kafka sur le topic '{topic_name}' et S3...")
    while True:
        flight_data = generate_flight_data()
        producer.send(topic_name, flight_data)
        print(f"Données envoyées : {flight_data}")

        # Stockage sur S3
        upload_to_s3(flight_data)

        time.sleep(1)  # Fréquence d'envoi des messages
