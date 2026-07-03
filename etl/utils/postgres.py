#gère la connexion 
from sqlalchemy import create_engine, text
from etl.utils.config import *


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@postgres:5432/{POSTGRES_DB}"
)

engine = create_engine(
    DATABASE_URL,
    future=True
)