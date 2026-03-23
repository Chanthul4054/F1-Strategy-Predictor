import logging
import argparse
from ingest import fetch_and_save_raw_data
from transform import clean_and_transform_data
from load import load_data_to_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_pipeline(year, gp, session):
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
        raw_laps_path, raw_results_path = fetch_and_save_raw_data(year, gp, session)
        if not raw_laps_path or not raw_results_path:
            raise ValueError("Ingestion failed to return valid paths.")
    except Exception as e:
        logging.error(f"Pipeline failed during ingestion: {e}")
        return

    # --- PHASE 2: TRANSFORMATION (Clean & Engineer Features) ---
    logging.info("--- Phase 2: Transformation ---")
    try:
        proc_laps, proc_results, proc_stints = clean_and_transform_data(raw_laps_path, raw_results_path, year, gp, session)
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
    parser = argparse.ArgumentParser(description="Run F1 Data Engineering Pipeline")
    parser.add_argument("--year", type=int, default=2024, help="Championship year (e.g., 2024)")
    parser.add_argument("--gp", type=str, default="Bahrain", help="Grand Prix name (e.g., Bahrain)")
    parser.add_argument("--session", type=str, default="R", help="Session type (e.g., FP1, Q, R)")
    args = parser.parse_args()
    
    run_pipeline(args.year, args.gp, args.session)
