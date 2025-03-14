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
    aws_access_key_id='YOUR ACCESS KEY',
    aws_secret_access_key='YOUR SECRET KEY',
    region_name='us-west-1'  # Change selon ta région AWS
)

bucket_name = "flight-simulator-data"

# Limiter le nombre de vols
MAX_FLIGHTS = 50  # Limite maximale du nombre de vols actifs
flights_in_progress = {}  # Dictionnaire pour stocker les vols actifs

def generate_flight_data(flight_id):
    """
    Met à jour les informations du vol existant en utilisant son flight_id.
    Assure une cohérence dans les changements de statut et de position.
    """
    flight = flights_in_progress[flight_id]
    
    # 1. Mise à jour géographique (la latitude et la longitude doivent évoluer de manière réaliste)
    # Assurer que le vol se déplace de manière cohérente, pas un saut géographique trop brusque
    new_latitude = flight["latitude"] + random.uniform(-1, 1)
    new_longitude = flight["longitude"] + random.uniform(-1, 1)
    
    # 2. Mise à jour du statut (assurer que le statut est cohérent)
    # Le vol doit passer par "En vol" avant de pouvoir changer de "Décollage" ou "Atterrissage"
    if flight["status"] == "Atterrissage" and random.random() < 0.2:
        flight["status"] = "En vol"
    elif flight["status"] == "Décollage" and random.random() < 0.2:
        flight["status"] = "En vol"
    elif flight["status"] == "En vol" and random.random() < 0.1:
        flight["status"] = random.choice(["Atterrissage", "Décollage"])

    # 3. Mise à jour de la vitesse, altitude et direction de manière réaliste
    flight["latitude"] = new_latitude
    flight["longitude"] = new_longitude
    flight["altitude"] = random.randint(1000, 40000)
    flight["speed"] = random.randint(200, 900)
    flight["direction"] = random.randint(0, 360)
    flight["timestamp"] = time.time()

    return flight


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

    # Générer 50 vols au démarrage et les ajouter au dictionnaire
    if not flights_in_progress:
        for _ in range(MAX_FLIGHTS):
            flight_id = fake.uuid4()
            flights_in_progress[flight_id] = {
                "flight_id": flight_id,
                "airline": random.choice(["Air France", "Lufthansa", "Delta", "Emirates", "KLM"]),
                "latitude": round(random.uniform(-90, 90), 6),
                "longitude": round(random.uniform(-180, 180), 6),
                "altitude": random.randint(1000, 40000),
                "speed": random.randint(200, 900),
                "direction": random.randint(0, 360),
                "status": "En vol",  # Tous les vols commencent en vol
                "timestamp": time.time()
            }

    # Mettre à jour ces 50 vols à chaque itération
    while True:
        for flight_id in list(flights_in_progress.keys()):
            # Mettre à jour les données du vol
            flight_data = generate_flight_data(flight_id)

            # Envoyer les données de vol vers Kafka
            producer.send(topic_name, flight_data)
            print(f"Données envoyées : {flight_data}")

            # Stockage sur S3
            upload_to_s3(flight_data)

        time.sleep(10)  # Fréquence d'envoi des messages