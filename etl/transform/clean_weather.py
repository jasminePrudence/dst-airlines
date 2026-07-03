import pandas as pd
from sqlalchemy import text
from etl.utils.postgres import engine

print("--- 🧹 Début de la transformation Météo (clean_weather) ---")

# Extraction des données brutes depuis dim_weather
query_extract = """
    SELECT airport_icao, observation_time, temperature, wind_speed, visibility
    FROM dim_weather;
"""

try:
    with engine.connect() as conn:
        df_raw = pd.read_sql(query_extract, conn)
        
    if df_raw.empty:
        print("ℹ️ Aucune donnée trouvée dans dim_weather. Fin du script.")
        exit()
        
    print(f"📋 {len(df_raw)} lignes extraites de dim_weather.")

    # Transformation / Nettoyage des données
    # Exemple : Conversion des vitesses de vent si nécessaire ou renommage des colonnes
    df_clean = pd.DataFrame()
    df_clean['airport_icao'] = df_raw['airport_icao']
    df_clean['observation_time'] = pd.to_datetime(df_raw['observation_time'])
    df_clean['temperature'] = df_raw['temperature'].astype(float)
    
    # Si les données de base sont en nœuds, conversion en km/h : 1 knot = 1.852 km/h
    df_clean['wind_speed_kmh'] = (df_raw['wind_speed'] * 1.852).round(2)
    
    # Si la donnée brute est en mètres, on divise simplement par 1000 pour avoir des km
    df_clean['visibility_km'] = (df_raw['visibility'] / 1000.0).round(2)
    # Chargement dans la table STG_AVWX
    # On utilise 'append' pour ajouter les nouvelles données, et on laisse Postgres gérer l'ID (SERIAL)
    with engine.begin() as conn:
        # Optionnel : On vide stg_avwx avant pour éviter les doublons à chaque run (Full Refresh)
        conn.execute(text("TRUNCATE TABLE STG_AVWX RESTART IDENTITY;"))
        
        df_clean.to_sql(
            name='stg_avwx',
            con=conn,
            if_exists='append',
            index=False
        )
        
    print(f"✅ Table STG_AVWX mise à jour avec succès ({len(df_clean)} lignes insérées) !")

except Exception as e:
    print(f"❌ Erreur durant l'exécution de clean_weather : {e}")