import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
DB_DIR = os.path.join(DATA_DIR, 'database')
DB_PATH = os.path.join(DB_DIR, 'f1_data.db')

for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, DB_DIR]:
    os.makedirs(d, exist_ok=True)

# Centralized arguments for pipeline execution
YEAR = 2024
GRAND_PRIX = "Bahrain"
SESSION = "R"
