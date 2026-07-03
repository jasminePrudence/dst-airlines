#Orchestre le changement 
# Exemple si la classe est dans un fichier nommé warehouse_loader.py dans le même dossier
from etl.load.warehouse_loader import WarehouseLoader
from datetime import datetime
import json
from kafka import KafkaConsumer
from sqlalchemy import text
from etl.utils.postgres import engine
from etl.load.dim_loader import (
    get_or_create_aircraft,
    get_or_create_date
)

consumer = KafkaConsumer(
    "opensky-raw",
    bootstrap_servers=["kafka:29092"],
    value_deserializer=lambda m: json.loads(m.decode())
)

loader = WarehouseLoader()
def load_postgres():
    print("🎧 PostgreSQL Consumer démarré...")

    for message in consumer:
        loader.process_snapshot(
            message.value
        )

if __name__ == "__main__":
    load_postgres()