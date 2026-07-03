import requests
import polars as pl
import psycopg2
from etl.utils.logger import logger
import os
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv(dotenv_path="/app/.env")

def extract_aviationstack():
    url = "http://api.aviationstack.com/v1/flights"
    
    # Récupérer la clé depuis le .env
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    
    params = {
        'access_key': api_key,
        'arr_iata': 'GVA', # Filtrage sur l'aéroport d'arrivée Genève (GVA)
    }
    
    logger.info("Extraction aviationstack")
    print("--- Début de l'extraction AviationStack ---")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json().get('data', [])
        
        if not data:
            print("Aucune donnée reçue de l'API AviationStack.")
            return
            
        rows = []
        for flight in data:
            # Gestion et normalisation préventive des codes IATA (Consigne : Toujours en majuscules)
            dep_iata = flight.get("departure", {}).get("iata")
            arr_iata = flight.get("arrival", {}).get("iata")
            airline_iata = flight.get("airline", {}).get("iata")

            rows.append({
                "flight_date": flight.get("flight_date"),
                "flight_number": flight.get("flight", {}).get("number"),
                "airline_name": flight.get("airline", {}).get("name"),
                "airline_iata": airline_iata.upper() if airline_iata else None,
                "aircraft_icao24": flight.get("aircraft", {}).get("icao24") if flight.get("aircraft") else None,
                "departure_iata": dep_iata.upper() if dep_iata else None,
                "arrival_iata": arr_iata.upper() if arr_iata else None,
                "scheduled_departure": flight.get("departure", {}).get("scheduled"),
                "actual_departure": flight.get("departure", {}).get("actual"),
                "scheduled_arrival": flight.get("arrival", {}).get("scheduled"),
                "actual_arrival": flight.get("arrival", {}).get("actual"),
                "departure_delay": flight.get("departure", {}).get("delay"),
                "arrival_delay": flight.get("arrival", {}).get("delay"),
                "status": flight.get("flight_status")
            })
            
        # Déduplication efficace avec Polars
        df = pl.DataFrame(rows)
        df = df.unique(subset=["flight_number", "scheduled_departure"])
        
        # Connexion à PostgreSQL (Spécification explicite du port interne Docker)
        conn = psycopg2.connect(
            host="postgres", 
            database="dst_airlines", 
            user="postgres", 
            password="postgres123",
            port=5432
        )
        cursor = conn.cursor()
        
        print(f"Insertion de {len(df)} vols dans la table stg_aviationstack...")
        
        # Mapping explicite et sécurisé pour éviter les décalages de colonnes
        for r in df.iter_rows(named=True):
            cursor.execute("""
                INSERT INTO stg_aviationstack (
                    flight_date, flight_number, airline_name, airline_iata, aircraft_icao24, 
                    departure_iata, arrival_iata, scheduled_departure, actual_departure, 
                    scheduled_arrival, actual_arrival, departure_delay, arrival_delay, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                r["flight_date"], r["flight_number"], r["airline_name"], r["airline_iata"], r["aircraft_icao24"],
                r["departure_iata"], r["arrival_iata"], r["scheduled_departure"], r["actual_departure"],
                r["scheduled_arrival"], r["actual_arrival"], r["departure_delay"], r["arrival_delay"], r["status"]
            ))
            
        conn.commit()
        cursor.close()
        conn.close()
        print("✓ Staging AviationStack mis à jour avec succès.")
    else:
        print(f"Erreur lors du requêtage API : {response.status_code} - {response.text}")

if __name__ == "__main__":
    extract_aviationstack()