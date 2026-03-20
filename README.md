# 🏎️ PitWall – F1 Data Engineering & Strategy Predictor

**PitWall** is a full-stack data engineering and data science application that analyzes Formula 1 telemetry and race strategy in real-time. Originally a predictive dashboard, it now features a robust, end-to-end Data Engineering ETL pipeline designed to ingest, transform, and store F1 telemetry into an analytical data warehouse.

## 🚀 Features

### 1. ⚙️ End-to-End Data Pipeline (ETL)
* **Ingestion (Data Lake - Raw):** Extracts live FastF1 data and serializes it to columnar Parquet format for high-speed storage.
* **Transformation:** Cleanses missing lap times, drops duplicated records, engineers features (Clean Lap Flags), and calculates mathematical aggregations (Stint summaries) using Pandas.
* **Loading (Data Warehouse):** Structures the processed Parquet files into a relational SQLite Database (OLAP) using a Star/Snowflake schema suitable for BI consumption.

### 2. ⚡ Telemetry Duel
* **The Problem:** Comparing driver speeds is difficult because tracks have different lengths and corner profiles.
* **The Solution:** Aligns driver telemetry traces by **Distance** (not time) to overlay speed profiles perfectly.
* **Insight:** "See exactly where Verstappen brakes later than Norris at Turn 1."

### 3. 🛞 Tyre Degradation Analysis
* **The Problem:** Raw lap times are noisy due to traffic and fuel burn.
* **The Solution:** Filters data using the **107% Rule** (removing Safety Car/In-laps) and fits a **Linear Regression** model (Scikit-Learn) to calculate the seconds lost per lap due to wear.
* **Insight:** "The Hard tyre is losing 0.12s of pace per lap."

### 4. 🏁 The Undercut Detector
* **The Problem:** TV broadcasts rarely show the "Gap to Leader" effectively during pit windows.
* **The Solution:** Visualizes the entire race trace, highlighting vertical drops (Pit Stops) and relative track position.
* **Insight:** "Did the undercut strategy work? See where the driver exited relative to traffic."

---

## 🛠️ Tech Stack

* **Data Source:** [FastF1](https://github.com/theOehrly/Fast-F1) (Official F1 Live Timing API wrapper)
* **ETL Pipeline:** Python, Pandas, Parquet
* **Data Warehouse / Storage:** SQLite (Relational DB), Parquet (Data Lake)
* **App Framework:** Streamlit
* **Machine Learning:** Scikit-Learn (Linear Regression)
* **Visualization:** Matplotlib, Seaborn

---

## 💻 Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/pitwall-f1.git
    cd pitwall-f1
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Data Pipeline (ETL)**
    This will extract the latest data, transform it, and build the `f1_data.db` database.
    ```bash
    cd data_pipeline
    python pipeline.py
    cd ..
    ```

4.  **Run the application**
    ```bash
    streamlit run f1App.py
    ```

---

## 📂 Project Structure & Architecture

```text
pitwall-f1/
├── data_pipeline/                # ⚙️ The ETL Pipeline Module
│   ├── config.py                 # Central configuration for paths and variables
│   ├── ingest.py                 # Phase 1: Extractions from FastF1 API to Parquet Data Lake
│   ├── transform.py              # Phase 2: Data Cleaning, Missing Values, and Aggregations
│   ├── load.py                   # Phase 3: Loads processed Parquet records into SQLite
│   └── pipeline.py               # The Orchestrator execution script
│
├── data/                         # 🗄️ Data Storage Ecosystem
│   ├── raw/                      # Data Lake Zone 1 (Raw Parquet files from API)
│   ├── processed/                # Data Lake Zone 2 (Cleaned & Engineered Parquet files)
│   └── database/                 # Data Warehouse Zone 
│       └── f1_data.db            # Final SQLite Database (Analytical Tables)
│
├── f1App.py                      # Main Streamlit logic
├── requirements.txt              # Python dependencies
└── README.md                     # Project documentation
```

---

## 🗄️ Database Design (Warehouse)

The SQLite Database uses an analytical schema to support the Streamlit Dashboard:
* **`f1_race_results`** (Dimension Table): Holds Driver Abbreviation, Team Name, Starting Grid Position, Final Position, and Points.
* **`f1_laps`** (Fact Table): Granular event data. Contains `LapNumber`, `LapTime` (seconds), `Driver`, `Sector Times`, `IsCleanLap` (custom flag), and `Compound`.
* **`f1_stint_summaries`** (Aggregated Fact Table): Computed in the transformation phase. Columns include `Driver`, `Stint`, `TotalLaps`, `MeanLapTime`, and `FastestLapTime`.

---

## 🧠 Key Technical Challenges Solved

- **Data Engineering & ETL:** Converting heavy, nested JSON/API responses with complex Python `<Timedelta>` objects into flat, columnar Parquet files using numeric scalar values (Total Seconds) for downstream analytical compatibility.
- **Idempotency & Cleanliness:** Implemented explicit duplicate removal and forward-fill (`ffill()`) imputation for missing tyre compound metrics during outlaps.
- **API Optimization:** Implemented `st.cache_data` and raw `Data Lake` caching to prevent re-downloading heavy telemetry files (50MB+) on every interaction, reducing load times by a massive margin.

---

## 🔮 Future Improvements

- **Orchestration Tooling:** Migrate `pipeline.py` to Apache Airflow or Dagster for CRON scheduling on race weekends.
- **Machine Learning:** Implement a Random Forest Regressor to predict "Box Lap" based on tyre life using the processed database features.
- **Live Mode:** Connect the pipeline to stream live telemetry updates via Kafka.

---

Built with ❤️ by **Chanthul**
