import pandas as pd
import os
import logging
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_and_transform_data(laps_path, results_path, year, gp, session_type):
    """
    ETL Transformation layer:
    - Load raw Parquet files
    - Remove duplicates & log data quality metrics
    - Handle missing values (LapTime logic)
    - Engineer features (Tyre Age, Lap Delta, Trends, Pit Indicators)
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

    # 2. Data Quality & Duplicate Removal
    logging.info(f"Raw Lap records: {len(df_laps)} | Raw Results records: {len(df_results)}")
    df_laps = df_laps.drop_duplicates()
    df_results = df_results.drop_duplicates()
    logging.info(f"After duplicate removal - Laps: {len(df_laps)} | Results: {len(df_results)}")
    
    # Log Missing values
    missing_lap_time = df_laps['LapTime'].isna().sum()
    logging.info(f"Identified {missing_lap_time} laps with missing LapTime (likely In/Out laps or Retirements).")

    # 3. Handle Missing Values / Data Cleaning
    df_laps['TrackStatus'] = df_laps['TrackStatus'].astype(str)
    # flag for a clean lap
    df_laps['IsCleanLap'] = df_laps['LapTime'].notna() & (df_laps['TrackStatus'] == '1')
    
    # ffill compound info
    df_laps['Compound'] = df_laps.groupby('Driver')['Compound'].ffill()
    
    # 4. Feature Engineering
    logging.info("Engineering new features: Tyre Age, Pit Indicators, Deltas...")
    df_laps['LapNumber'] = df_laps['LapNumber'].astype(int)
    
    # Tyre Age: Cumulative laps on the current stint
    df_laps['TyreAge'] = df_laps.groupby(['Driver', 'Stint']).cumcount() + 1
    
    # Pit Indicators
    df_laps['IsPitLap'] = df_laps['PitInTime'].notna() | df_laps['PitOutTime'].notna()
    
    # Lap Delta to Stint Average
    # First, calculate mean only for clean laps
    clean_laps = df_laps[df_laps['IsCleanLap']].copy()
    stint_means = clean_laps.groupby(['Driver', 'Stint'])['LapTime'].transform('mean')
    clean_laps['LapDeltaToStintMean'] = clean_laps['LapTime'] - stint_means
    
    # Join back using index
    df_laps['LapDeltaToStintMean'] = clean_laps['LapDeltaToStintMean']
    
    # Degradation Trend: 3-lap rolling average of lap times (only on clean laps)
    clean_laps['DegradationTrend'] = clean_laps.groupby(['Driver', 'Stint'])['LapTime'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df_laps['DegradationTrend'] = clean_laps['DegradationTrend']
    
    # Fill remaining NaNs for output compatibility
    if 'LapDeltaToStintMean' in df_laps.columns:
        df_laps['LapDeltaToStintMean'] = df_laps['LapDeltaToStintMean'].fillna(0)
    if 'DegradationTrend' in df_laps.columns:
        df_laps['DegradationTrend'] = df_laps['DegradationTrend'].fillna(0)
        
    # Summarize stints
    logging.info("Calculating stint summaries")
    stint_summary = df_laps.groupby(['Driver', 'Stint', 'Compound']).agg(
        TotalLaps=('LapNumber', 'count'),
        MeanLapTime=('LapTime', lambda x: x[x.notna()].mean() if len(x[x.notna()]) > 0 else None),
        FastestLapTime=('LapTime', lambda x: x[x.notna()].min() if len(x[x.notna()]) > 0 else None),
        MaxLapNumber=('LapNumber', 'max')
    ).reset_index()

    # (Removed unnecessary .dt.total_seconds() calls for MeanLapTime and FastestLapTime because they are already float)

    # 5. Clean Results Data
    missing_points = df_results['Points'].isna().sum()
    if missing_points > 0:
        logging.info(f"Imputing {missing_points} missing Points records with 0")
        df_results['Points'] = df_results['Points'].fillna(0)
    
    # 6. Save Processed Data
    base_name = f"{year}_{gp.replace(' ', '_')}_{session_type}"
    
    proc_laps_path = os.path.join(PROCESSED_DATA_DIR, f"clean_laps_{base_name}.parquet")
    proc_results_path = os.path.join(PROCESSED_DATA_DIR, f"clean_results_{base_name}.parquet")
    proc_stints_path = os.path.join(PROCESSED_DATA_DIR, f"stint_summary_{base_name}.parquet")
    
    # Ensure LapTime is numeric if it isn't already before saving for easier downstream usage
    if df_laps['LapTime'].dtype != 'float64' and df_laps['LapTime'].dtype != 'int64':
        df_laps['LapTime'] = df_laps['LapTime'].dt.total_seconds()
        
    df_laps.to_parquet(proc_laps_path, index=False)
    df_results.to_parquet(proc_results_path, index=False)
    stint_summary.to_parquet(proc_stints_path, index=False)
    
    logging.info(f"Saved processed data to {PROCESSED_DATA_DIR}")
    return proc_laps_path, proc_results_path, proc_stints_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--gp", type=str, default="Bahrain")
    parser.add_argument("--session", type=str, default="R")
    args = parser.parse_args()
    
    base_name = f"{args.year}_{args.gp.replace(' ', '_')}_{args.session}"
    laps_file = os.path.join(RAW_DATA_DIR, f"laps_{base_name}.parquet")
    results_file = os.path.join(RAW_DATA_DIR, f"results_{base_name}.parquet")
    clean_and_transform_data(laps_file, results_file, args.year, args.gp, args.session)
