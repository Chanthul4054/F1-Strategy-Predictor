import logging
from config import YEAR, GRAND_PRIX, SESSION
from ingest import fetch_and_save_raw_data
from transform import clean_and_transform_data
from load import load_data_to_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_pipeline():
    """
    Orchestrator for the entire ETL data pipeline.
    Run this file to execute the pipeline end-to-end.
    """
    logging.info("=========================================")
    logging.info("🚀 Starting F1 Data Engineering Pipeline")
    logging.info("=========================================")
    
    # --- PHASE 1: EXTRACTION (Ingest) ---
    logging.info("--- Phase 1: Ingestion ---")
    try:
        raw_laps_path, raw_results_path = fetch_and_save_raw_data(YEAR, GRAND_PRIX, SESSION)
        if not raw_laps_path or not raw_results_path:
            raise ValueError("Ingestion failed to return valid paths.")
    except Exception as e:
        logging.error(f"Pipeline failed during ingestion: {e}")
        return

    # --- PHASE 2: TRANSFORMATION (Clean & Engineer Features) ---
    logging.info("--- Phase 2: Transformation ---")
    try:
        proc_laps, proc_results, proc_stints = clean_and_transform_data(raw_laps_path, raw_results_path)
        if not proc_laps or not proc_results or not proc_stints:
            raise ValueError("Transformation failed. No processed paths returned.")
    except Exception as e:
        logging.error(f"Pipeline failed during transformation: {e}")
        return

    # --- PHASE 3: LOADING (Database Storage) ---
    logging.info("--- Phase 3: Loading ---")
    try:
        load_data_to_db(proc_laps, proc_results, proc_stints)
    except Exception as e:
        logging.error(f"Pipeline failed during database loading: {e}")
        return

    logging.info("=========================================")
    logging.info("✅ F1 Data Pipeline Completed Successfully")
    logging.info("=========================================")

if __name__ == "__main__":
    run_pipeline()
