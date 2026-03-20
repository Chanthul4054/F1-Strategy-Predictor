import pandas as pd
import sqlite3
import os
import logging
from config import PROCESSED_DATA_DIR, DB_PATH, YEAR, GRAND_PRIX, SESSION

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data_to_db(proc_laps_path, proc_results_path, proc_stints_path):
    """
    Load data from the processed layer into final storage (SQLite Database).
    """
    logging.info(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # 1. Read Processed Parquet Files
        logging.info("Reading processed parquet files for DB loading")
        df_laps = pd.read_parquet(proc_laps_path)
        df_results = pd.read_parquet(proc_results_path)
        df_stints = pd.read_parquet(proc_stints_path)
        
        # 2. Write DataFrames to SQLite Tables
        # Using if_exists='replace' for simplicity. 
        # A true production system might use 'append' and handle UPSERT.
        df_laps.to_sql('f1_laps', conn, if_exists='replace', index=False)
        df_results.to_sql('f1_race_results', conn, if_exists='replace', index=False)
        df_stints.to_sql('f1_stint_summaries', conn, if_exists='replace', index=False)
        
        logging.info("Data successfully loaded into 'f1_laps', 'f1_race_results', and 'f1_stint_summaries' tables")
        
        # 3. Validation / Audit
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logging.info(f"Final Database Tables: {[t[0] for t in tables]}")
        
    except Exception as e:
        logging.error(f"Error during database load: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    base_name = f"{YEAR}_{GRAND_PRIX.replace(' ', '_')}_{SESSION}"
    lp = os.path.join(PROCESSED_DATA_DIR, f"clean_laps_{base_name}.parquet")
    rp = os.path.join(PROCESSED_DATA_DIR, f"clean_results_{base_name}.parquet")
    sp = os.path.join(PROCESSED_DATA_DIR, f"stint_summary_{base_name}.parquet")
    load_data_to_db(lp, rp, sp)
