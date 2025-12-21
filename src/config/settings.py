import os

DATA_PATH = os.getenv("DATA_PATH", "data")
BRONZE_PATH = f"{DATA_PATH}/bronze"
SILVER_PATH = f"{DATA_PATH}/silver"
GOLD_PATH = f"{DATA_PATH}/gold"