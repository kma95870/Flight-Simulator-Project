import boto3
import json
from datetime import datetime, timezone

s3_client = boto3.client(
    's3',
    aws_access_key_id='YOUR ACCESS KEY ID',
    aws_secret_access_key='YOUR SECRET ACCESS KEY',
    region_name='us-west-1'  # Change selon ta région AWS
)

bucket_name = "flight-simulator-data"
prefix = "data/"

# Liste tous les fichiers dans le bucket avec le préfixe "data/"
response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

if "Contents" in response:
    # Trier les fichiers par date de modification (dernier en premier)
    files = sorted(response["Contents"], key=lambda x: x["LastModified"], reverse=True)

    latest_file = files[0]  # Prendre le fichier le plus récent
    latest_file_key = latest_file["Key"]
    last_modified = latest_file["LastModified"].astimezone(timezone.utc)

    print(f"Dernier fichier trouvé : {latest_file_key} (modifié : {last_modified} UTC)")

    # Télécharger et afficher le contenu du fichier
    response = s3_client.get_object(Bucket=bucket_name, Key=latest_file_key)
    content = response["Body"].read().decode("utf-8")
    print("Contenu du fichier :")
    print(content)

else:
    print("Aucun fichier trouvé dans S3.")