from pymongo import MongoClient
from etl.utils.config import MONGO_USER, MONGO_PASSWORD, MONGO_DB

client = MongoClient(
    f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@mongo:27017/?authSource=admin"
)

db = client[MONGO_DB]