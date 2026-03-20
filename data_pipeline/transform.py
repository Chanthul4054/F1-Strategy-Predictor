import pandas as pd
import os
import logging
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, YEAR, GRAND_PRIX, SESSION

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_and_transform_data(laps_path, results_path):
    """
    ETL Transformation layer:
    - Load raw Parquet files
    - Remove duplicates
    - Handle missing values (LapTime logic)
    - Engineer features (Stint summaries)
    - Convert data types where applicable
    - Save to processed data zone
    """
    logging.info("Starting Data Transformation Phase")
    
    # 1. Load Data
    try:
        df_laps = pd.read_parquet(laps_path)
        df_results = pd.read_parquet(results_path)
    except Exception as e:
        logging.error(f"Failed to read Parquet files: {e}")
        return None, None, None

    # 2. Duplicate Removal
    df_laps = df_laps.drop_duplicates()
    df_results = df_results.drop_duplicates()
    
    # 3. Handle Missing Values / Data Cleaning
    # For tire degradation analysis later, track status '1' means green flag (clean lap)
    # FastF1 track status is often string, so match '1' or '1.0'
    df_laps['TrackStatus'] = df_laps['TrackStatus'].astype(str)
    
    # Let's create an 'IsCleanLap' flag: not missing laptime and track is green (1)
    df_laps['IsCleanLap'] = df_laps['LapTime'].notna() & (df_laps['TrackStatus'] == '1')
    
    # Forward fill compound info for drivers since pit in/out laps might miss it in some APIs
    # Grouping by Driver to correctly ffill
    df_laps['Compound'] = df_laps.groupby('Driver')['Compound'].ffill()
    
    # Handle NaNs in numeric columns by replacing with 0 or keeping them if they have meaning
    # e.g., PitOutTime is NaN if they didn't pit
    
    # 4. Feature Engineering: Stint Summaries
    # A single driver usually has 1-4 stints per race.
    logging.info("Calculating stint summaries")
    df_laps['LapNumber'] = df_laps['LapNumber'].astype(int)
    
    stint_summary = df_laps.groupby(['Driver', 'Stint', 'Compound']).agg(
        TotalLaps=('LapNumber', 'count'),
        # Mean Lap Time taking only non-null laptimes
        MeanLapTime=('LapTime', lambda x: x[x.notna()].mean() if len(x[x.notna()]) > 0 else None),
        # Fastest Lap Time in the Stint
        FastestLapTime=('LapTime', lambda x: x[x.notna()].min() if len(x[x.notna()]) > 0 else None),
        # Final lap in the stint
        MaxLapNumber=('LapNumber', 'max')
    ).reset_index()

    # 5. Clean Results Data
    # Fill missing points with 0
    if 'Points' in df_results.columns:
        df_results['Points'] = df_results['Points'].fillna(0)
    
    # 6. Save Processed Data
    base_name = f"{YEAR}_{GRAND_PRIX.replace(' ', '_')}_{SESSION}"
    
    proc_laps_path = os.path.join(PROCESSED_DATA_DIR, f"clean_laps_{base_name}.parquet")
    proc_results_path = os.path.join(PROCESSED_DATA_DIR, f"clean_results_{base_name}.parquet")
    proc_stints_path = os.path.join(PROCESSED_DATA_DIR, f"stint_summary_{base_name}.parquet")
    
    df_laps.to_parquet(proc_laps_path, index=False)
    df_results.to_parquet(proc_results_path, index=False)
    stint_summary.to_parquet(proc_stints_path, index=False)
    
    logging.info(f"Saved processed data to {PROCESSED_DATA_DIR}")
    return proc_laps_path, proc_results_path, proc_stints_path

if __name__ == "__main__":
    base_name = f"{YEAR}_{GRAND_PRIX.replace(' ', '_')}_{SESSION}"
    laps_file = os.path.join(RAW_DATA_DIR, f"laps_{base_name}.parquet")
    results_file = os.path.join(RAW_DATA_DIR, f"results_{base_name}.parquet")
    clean_and_transform_data(laps_file, results_file)
