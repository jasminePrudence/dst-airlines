import json
import os
from kafka import KafkaConsumer
from sqlalchemy import text
from etl.utils.postgres import engine

consumer = KafkaConsumer(
    "weather-raw",
    bootstrap_servers=["kafka:29092"],
    value_deserializer=lambda m: json.loads(m.decode()),
    auto_offset_reset="earliest"
)

def load_weather():
    print("--- 🌦️ Consumer Météo à l'écoute du topic 'weather-raw' ---")

    # Requête SQL optimisée avec gestion native des conflits (UPSERT)
    query_insert = text("""
        INSERT INTO dim_weather(
            airport_icao, observation_time, temperature, pressure, 
            wind_speed, wind_direction, visibility, metar
        )
        VALUES(
            :airport, :obs, :temp, :pressure, 
            :wind, :direction, :visibility, :metar
        )
        ON CONFLICT (airport_icao, observation_time) 
        DO NOTHING
        RETURNING weather_key; -- Renvoie la clé générée si l'insertion a lieu
    """)

    for message in consumer:
        weather = message.value
        station = weather.get("station")
        obs_time = weather.get("time", {}).get("dt")
        
        print(f"📦 Message reçu pour la station : {station}")
        
        # engine.begin() ouvre une transaction et gère automatiquement le commit/rollback
        with engine.begin() as conn:
            try:
                result = conn.execute(
                    query_insert,
                    {
                        "airport": station,
                        "obs": obs_time,
                        "temp": weather.get("temperature", {}).get("value"),
                        "pressure": weather.get("altimeter", {}).get("value"),
                        "wind": weather.get("wind_speed", {}).get("value"),
                        "direction": weather.get("wind_direction", {}).get("value"),
                        "visibility": weather.get("visibility", {}).get("value"),
                        "metar": weather.get("raw")
                    }
                ).fetchone()

                # Si la ligne a été insérée, result contiendra la nouvelle clé (weather_key)
                if result:
                    print(f"💾 Météo pour {station} insérée avec succès ! (Clé : {result[0]})")
                else:
                    # Si l'insertion a été ignorée par le ON CONFLICT, result sera vide (None)
                    print(f"ℹ️ Météo déjà existante pour {station} à {obs_time} (ignorée proprement)")
                    
            except Exception as e:
                print(f"❌ Erreur lors du traitement de la station {station} : {e}")

if __name__ == "__main__":
    load_weather()