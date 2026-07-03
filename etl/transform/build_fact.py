import polars as pl
import psycopg2

def calculate_co2(distance_km=400):
    # Facteur d'émission court-courrier type (0.15 kg CO2 / km / passager)
    # On peut imaginer un calcul basé sur un remplissage moyen ou un avion type
    return distance_km * 0.15

def build_fact():
    conn_uri = "postgresql://postgres:postgres123@postgres:5432/dst_airlines"
    print("--- Début de la construction de FACT_FLIGHTS ---")
    
    # Charger la table de staging et les dimensions référentielles dans Polars
    df_stg = pl.read_database_uri("SELECT * FROM stg_aviationstack;", conn_uri)
    df_dim_airports = pl.read_database_uri("SELECT airport_key, iata_code FROM dim_airports;", conn_uri)
    df_dim_airlines = pl.read_database_uri("SELECT airline_key, iata_code FROM dim_airlines;", conn_uri)
    
    if df_stg.is_empty():
        print("Staging vide. Fin du processus.")
        return

    # Normalisation pré-jointure
    df_stg = df_stg.with_columns([
        pl.col("departure_iata").str.to_uppercase(),
        pl.col("arrival_iata").str.to_uppercase(),
        pl.col("airline_iata").str.to_uppercase()
    ])

    # JOINTURES avec Polars pour récupérer les clés de substitution (Surrogate Keys)
    # Jointure pour le départ
    df_joined = df_stg.join(df_dim_airports, left_on="departure_iata", right_on="iata_code", how="left") \
                      .rename({"airport_key": "departure_airport_key"})
                      
    # Jointure pour l'arrivée
    df_joined = df_joined.join(df_dim_airports, left_on="arrival_iata", right_on="iata_code", how="left") \
                      .rename({"airport_key": "arrival_airport_key"})
                      
    # Jointure pour la compagnie
    df_joined = df_joined.join(df_dim_airlines, left_on="airline_iata", right_on="iata_code", how="left")

    # CALCUL DU CO2 (Eco-conception / Consigne RSE)
    # L'axe CDG-GVA fait environ 400 km à vol d'oiseau
    df_final = df_joined.with_columns(
        pl.lit(calculate_co2(400)).alias("estimated_co2_kg")
    )

    # Insertion dans la table de faits FACT_FLIGHTS
    conn = psycopg2.connect(host="postgres", database="dst_airlines", user="postgres", password="postgres123")
    cursor = conn.cursor()
    
    print(f"Historisation de {len(df_final)} vols dans la table de faits...")
    for row in df_final.iter_rows(named=True):
        cursor.execute("""
            INSERT INTO fact_flights (
                flight_number, flight_status, departure_airport_key, arrival_airport_key, 
                airline_key, scheduled_departure, actual_departure, departure_delay_min, estimated_co2_kg
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            row["flight_number"],
            row["status"],
            row["departure_airport_key"],
            row["arrival_airport_key"],
            row["airline_key"],
            row["scheduled_departure"],
            row["actual_departure"],
            row["departure_delay"],
            row["estimated_co2_kg"]
        ))
        
    conn.commit()
    cursor.close()
    conn.close()
    print("✓ Table de faits FACT_FLIGHTS consolidée avec succès !")

if __name__ == "__main__":
    build_fact()