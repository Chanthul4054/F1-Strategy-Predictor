import fastf1
import pandas as pd
import os
import logging
from config import RAW_DATA_DIR, YEAR, GRAND_PRIX, SESSION

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_and_save_raw_data(year, gp, session_type):
    """
    Extract data from FastF1 API and save to Data Lake (raw Parquet files).
    """
    logging.info(f"Ingesting data for {year} {gp} ({session_type})")
    
    # Enable cache for FastF1
    cache_path = os.path.join(RAW_DATA_DIR, 'fastf1_cache')
    os.makedirs(cache_path, exist_ok=True)
    fastf1.Cache.enable_cache(cache_path)
    
    # 1. Fetch Session
    session = fastf1.get_session(year, gp, session_type)
    # Suppress output from FastF1 during script execution
    session.load(telemetry=False)  # We set telemetry=False here because full telemetry is massive.
                                   # Depending on needs, we could load it and extract car data.
    
    # 2. Extract Laps
    laps = session.laps
    laps_path = os.path.join(RAW_DATA_DIR, f"laps_{year}_{gp.replace(' ', '_')}_{session_type}.parquet")
    laps_df = pd.DataFrame(laps)
    
    # Convert FastF1 timedelta columns to numeric (seconds) for Parquet compatibility
    timedelta_cols = laps_df.select_dtypes(include=['timedelta64[ns]']).columns
    for col in timedelta_cols:
        laps_df[col] = laps_df[col].dt.total_seconds()
        
    laps_df.to_parquet(laps_path, index=False)
    logging.info(f"Saved raw laps data to {laps_path}")
    
    # 3. Extract Results
    results = session.results
    results_path = os.path.join(RAW_DATA_DIR, f"results_{year}_{gp.replace(' ', '_')}_{session_type}.parquet")
    results_df = pd.DataFrame(results)
    
    # Convert timedelta columns for results dataframe
    timedelta_cols = results_df.select_dtypes(include=['timedelta64[ns]']).columns
    for col in timedelta_cols:
        results_df[col] = results_df[col].dt.total_seconds()
        
    results_df.to_parquet(results_path, index=False)
    logging.info(f"Saved raw results data to {results_path}")
    
    return laps_path, results_path

if __name__ == "__main__":
    fetch_and_save_raw_data(YEAR, GRAND_PRIX, SESSION)
