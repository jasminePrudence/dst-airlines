import requests
import json
import time
from kafka import KafkaProducer
from etl.utils.logger import logger
import os
from dotenv import load_dotenv

load_dotenv()

def json_serializer(data):
    return json.dumps(data).encode("utf-8")

# Connexion au broker Kafka (Nom du service dans le réseau Docker : 'kafka:29092')
producer = KafkaProducer(
    bootstrap_servers=['kafka:29092'],
    value_serializer=json_serializer
)

CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID")
CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET")
TOKEN_URL = os.getenv("OPENSKY_TOKEN_URL")

def get_access_token():
    """Récupère un token OAuth2 valide auprès d'OpenSky"""
    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    response = requests.post(TOKEN_URL, data=payload, timeout=10)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Impossible d'obtenir le token OAuth2: {response.status_code} - {response.text}")
    

def fetch_opensky_data():
    """Récupère les données des vols en utilisant le token"""
    try:
        # Obtenir le token d'accès
        token = get_access_token()
        
        # Configurer les headers avec le token Bearer
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        # Zone d'exclusion (Axe Paris CDG - Genève GVA comme défini dans notre MVP)
        params = {'lamin': 45.0, 'lamax': 50.0, 'lomin': 1.5, 'lomax': 7.0}
        
        url = "https://opensky-network.org/api/states/all"

        print("--- Démarrage du Producer OpenSky (Kafka) ---")
        logger.info("Extraction OpenSky")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            raw_data = response.json()
            
            # On envoie l'événement brut dans le topic 'opensky-raw'
            producer.send("opensky-raw", raw_data)
            producer.flush()
            print(f"[{time.strftime('%H:%M:%S')}] ✈️ Données envoyées à Kafka successfully.")
        elif response.status_code == 429:
            print("Erreur 429 : Trop de requêtes (Même avec authentification, respectez les quotas).")
        else:
            print(f"Erreur API OpenSky: {response.status_code}")
            
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    data = fetch_opensky_data()