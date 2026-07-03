import polars as pl
import psycopg2

def build_dimensions():
    # Chaîne de connexion PostgreSQL Docker
    conn_uri = "postgresql://postgres:postgres123@postgres:5432/dst_airlines"
    
    print("--- 🚀 Début du peuplement des Dimensions ---")
    
    # Lecture de la table de staging globale via Polars
    query_stg = "SELECT departure_iata, arrival_iata, airline_name, airline_iata, aircraft_icao24 FROM stg_aviationstack"
    df_stg = pl.read_database_uri(query_stg, conn_uri)
    
    if df_stg.is_empty():
        print("❌ La table de Staging est vide. Abandon du processus.")
        return

    # --- TRAITEMENT DIM_AIRPORTS ---
    dep_codes = df_stg.select("departure_iata").rename({"departure_iata": "iata_code"})
    arr_codes = df_stg.select("arrival_iata").rename({"arrival_iata": "iata_code"})
    df_airports_stg = pl.concat([dep_codes, arr_codes]).drop_nulls().unique()
    df_airports_stg = df_airports_stg.with_columns(pl.col("iata_code").str.to_uppercase())

    # --- TRAITEMENT DIM_AIRLINES ---
    df_airlines_stg = df_stg.select(["airline_iata", "airline_name"]).drop_nulls().unique(subset=["airline_iata"])
    df_airlines_stg = df_airlines_stg.with_columns(pl.col("airline_iata").str.to_uppercase())

    # --- TRAITEMENT DIM_AIRCRAFT ---
    # On extrait les codes ICAO24 uniques des avions qui ont réellement volé
    df_aircraft_stg = df_stg.select("aircraft_icao24").rename({"aircraft_icao24": "icao24"}).drop_nulls().unique()
    df_aircraft_stg = df_aircraft_stg.with_columns(pl.col("icao24").str.to_lowercase())

    # Connexion classique avec Psycopg2 pour l'insertion sécurisée (ON CONFLICT DO NOTHING)
    conn = psycopg2.connect(host="postgres", database="dst_airlines", user="postgres", password="postgres123")
    cursor = conn.cursor()
    
    # Insertion dans DIM_AIRPORTS
    print(f"🔹 Insertion de {len(df_airports_stg)} aéroports potentiels...")
    for row in df_airports_stg.iter_rows(named=True):
        cursor.execute("""
            INSERT INTO dim_airports (iata_code, airport_name, city, country)
            VALUES (%s, 'Unknown Airport', 'Unknown City', 'Unknown Country')
            ON CONFLICT (iata_code) DO NOTHING;
        """, (row["iata_code"],))
        
    # Insertion dans DIM_AIRLINES
    print(f"🔹 Insertion de {len(df_airlines_stg)} compagnies potentielles...")
    for row in df_airlines_stg.iter_rows(named=True):
        cursor.execute("""
            INSERT INTO dim_airlines (iata_code, airline_name)
            VALUES (%s, %s)
            ON CONFLICT (iata_code) DO NOTHING;
        """, (row["airline_iata"], row["airline_name"]))
        
    # Insertion dans DIM_AIRCRAFT ✈️
    print(f"🔹 Insertion de {len(df_aircraft_stg)} avions uniques dans dim_aircraft...")
    for row in df_aircraft_stg.iter_rows(named=True):
        cursor.execute("""
            INSERT INTO dim_aircraft (icao24, model, manufacturer, registration)
            VALUES (%s, 'Unknown Model', 'Unknown Manufacturer', 'Unknown Reg')
            ON CONFLICT (icao24) DO NOTHING;
        """, (row["icao24"],))
        
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Toutes les dimensions (Aéroports, Compagnies, Avions) ont été mises à jour avec succès.")

if __name__ == "__main__":
    build_dimensions()