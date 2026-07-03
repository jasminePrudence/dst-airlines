import json
import os
import time
import requests
from kafka import KafkaProducer
from dotenv import load_dotenv
from etl.utils.logger import logger

# 1. Chargement explicite du fichier .env
load_dotenv(dotenv_path="/app/.env")

API_KEY = os.getenv("AVWX_API_KEY")

AIRPORTS = [
    "LFPG",
    "LFPO",
    "EGLL",
    "EHAM",
    "LEMD"
]

def extract():
    logger.info("--- Démarrage du Producer AVWX (Kafka) ---")
    
    # Vérification de sécurité pour la clé API
    if not API_KEY:
        logger.error("❌ Erreur : AVWX_API_KEY est introuvable. Vérifiez votre fichier .env")
        return

    try:
        producer = KafkaProducer(
            bootstrap_servers="kafka:29092",
            value_serializer=lambda x: json.dumps(x).encode()
        )
    except Exception as e:
        logger.error(f"❌ Impossible de se connecter à Kafka : {e}")
        return

    while True:
        for airport in AIRPORTS:
            url = f"https://avwx.rest/api/metar/{airport}"
            headers = {
                "Authorization": f"BEARER {API_KEY}" if not API_KEY.startswith("BEARER") else API_KEY
            }
            
            logger.info(f"Extraction AVWX pour l'aéroport : {airport}")
            
            try:
                r = requests.get(url, headers=headers, timeout=10)
                
                if r.status_code == 200:
                    producer.send("weather-raw", r.json())
                    print(f"✔ METAR envoyé avec succès à Kafka : {airport}")
                else:
                    logger.warning(f"⚠️ Échec API pour {airport} : Code {r.status_code} - {r.text}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors de la requête sur {airport} : {e}")

        producer.flush()
        logger.info("😴 Pause de 5 minutes avant la prochaine extraction...")
        time.sleep(300)

def main():
    extract()

if __name__ == "__main__":
    main()