import os
import json
from kafka import KafkaConsumer
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
# Charger les variables d'environnement du fichier .env depuis confif.py
#récupérer automatiquement l'utilisateur et le mot de passe depuis l'environnement (ou votre fichier .env chargé)
from etl.utils.config import *
from etl.utils.mongodb import db

collection = db["live_flights"]

# Configuration du Consumer Kafka
consumer = KafkaConsumer(
    "opensky-raw",
    bootstrap_servers=['kafka:29092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset="earliest"
)

print("--- 🎧 Consumer Kafka à l'écoute du topic 'opensky-raw' ---")

for message in consumer:
    raw_data = message.value
    states = raw_data.get("states", [])
    
    if states:
        # Création du document nettoyé (Logique ETL)
        snapshot = {
            "snapshot_time": datetime.utcnow(),
            "flights_count": len(states),
            "states": []
        }
        
        for s in states:
            # NETTOYAGE : Suppression des espaces sur le callsign (Ex: 'AFR123  ' -> 'AFR123')
            callsign = s[1].strip() if s[1] else None
            
            snapshot["states"].append({
                "icao24": s[0],
                "callsign": callsign,
                "longitude": s[5],
                "latitude": s[6],
                "baro_altitude": s[7],
                "velocity": s[9],
                "on_ground": s[8]
            })
            
        # Ingestion finale NoSQL
        collection.insert_one(snapshot)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 💾 {len(states)} avions nettoyés et stockés dans MongoDB.")


# rajout de la partie suivante pour rendre les scripts exécutables par l'orchestrateur
#def main():
    #print("Mongo Consumer lancé")
    #for message in consumer:
        #collection.insert_one(snapshot)


#if __name__ == "__main__":
    #main()