# 🏎️ PitWall – F1 Data Engineering & Strategy Predictor

**PitWall** is a full-stack data engineering and data science application that analyzes Formula 1 telemetry and race strategy in real-time. Originally a predictive dashboard, it now features a robust, end-to-end Data Engineering ETL pipeline designed to ingest, transform, and store F1 telemetry into an analytical data warehouse.

## 🚀 Features

### 1. ⚙️ End-to-End Data Pipeline (ETL)
* **Ingestion (Data Lake - Raw):** Extracts live FastF1 data and serializes it to columnar Parquet format for high-speed storage. Output: `laps_YYYY_GP_Session.parquet` and `results_YYYY_GP_Session.parquet`.
* **Transformation:** Cleanses missing lap times, drops duplicated records, engineers features (Tyre Age, Clean Lap Flags, Pit Indicators, Degradation Trends, Lap Delta), performs data quality logging, and calculates aggregations (Stint summaries) using Pandas. Output: `clean_laps_...`, `clean_results_...`, `stint_summary_...`.
* **Loading (Data Warehouse):** Structures the processed Parquet files into a relational SQLite Database (OLAP) using a Star/Snowflake schema suitable for BI consumption. Output: `f1_data.db` (tables: `f1_laps`, `f1_race_results`, `f1_stint_summaries`).

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

### 5. 🤖 Pit Strategy Predictor
* **The Problem:** Knowing exactly when to pit based on tire degradation and pace.
* **The Solution:** Uses a Random Forest Classifier trained on stint lengths to estimate the probability that a driver's pit window is open.
* **Insight:** "Is it time to box? Check if the driver is within their optimal pit window."

---

## ⚙️ How It Works (Application Architecture)

The application is split into two decoupled halves: **1) The Data Engineering ETL Pipeline** (Back-end) and **2) The Analytical Dashboard** (Front-end).

### Part 1: The ETL Data Pipeline (`data_pipeline/`)
This acts as your "Data Factory." Its entire job is to reliably pull messy data from the real world, clean it, engineer new metrics out of it, and organize it into a structured warehouse so the frontend can query it easily.

1. **Extraction (`ingest.py`)**: Connects to the official F1 API (via FastF1) using command-line parameters (Year, Grand Prix, Session). It extracts granular sets of lap times, track status, and compounds, immediately saving them as fast, columnar `.parquet` files in the **Data Lake** (`data/raw/`).
2. **Transformation (`transform.py`)**: The refinery script. It drops duplicates, logs Data Quality checks, handles missing out-lap times, and creates smart, calculated metrics (`TyreAge`, `LapDeltaToStintMean`, `DegradationTrend`, `IsPitLap`). It also rolls up thousands of laps into bite-sized "Stint Summaries" (`stint_summary_...`).
3. **Loading (`load.py`)**: Pushes the cleaned and modeled data into the final destination—a local **SQLite Database Data Warehouse** (`f1_data.db`). It creates structured relational tables (`f1_laps`, `f1_race_results`, `f1_stint_summaries`) ready for fast BI querying.

### Part 2: The Streamlit Dashboard (`f1App.py`)
This is the front-facing "Pit Wall" application that race engineers would theoretically look at. It utilizes Streamlit's caching to load massive amounts of data efficiently and hosts four main analytical tabs:
- **Telemetry Duel:** Aligns telemetry by track distance (not time) to accurately compare braking points and cornering speeds between two drivers.
- **Tyre Degradation:** Uses a Scikit-Learn Linear Regression model on "clean laps" to calculate the exact pace lost per lap per compound.
- **Undercut Detector:** Charts the "Gap to Leader" across the entire race. Pit stops appear as massive vertical drops, visually revealing undercut successes against traffic.
- **Pit Strategy Predictor:** Analyzes every stint in the race and dynamically trains a Random Forest Classifier. It evaluates a driver's live *Tyre Age* and outputs a percentage probability that the driver is in their optimal pit window to box.

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
    git clone https://github.com/Chanthul4054/F1-Strategy-Predictor.git
    cd F1-Strategy-Predictor
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Data Pipeline (ETL)**
    This will extract the latest data, transform it, and build the `f1_data.db` database. You can pass the year, GP, and session as arguments.
    ```bash
    cd data_pipeline
    python pipeline.py --year 2024 --gp Bahrain --session R
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

## 📊 ETL Pipeline Design Diagram

```mermaid
flowchart TD
    subgraph Data Sources
        API[FastF1 API / Ergast]
    end

    subgraph Phase 1: Ingest (ingest.py)
        A[fetch_and_save_raw_data]
        C[FastF1 Local Cache]
    end

    subgraph Raw Data Zone
        R1[(laps_*.parquet)]
        R2[(results_*.parquet)]
    end

    subgraph Phase 2: Transform (transform.py)
        T[clean_and_transform_data]
        
        subgraph Operations
            O1(Data Cleaning & Deduplication)
            O2(Feature Engineering)
            O3(Stint Summarization)
        end
    end

    subgraph Processed Data Zone
        P1[(clean_laps_*.parquet)]
        P2[(clean_results_*.parquet)]
        P3[(stint_summary_*.parquet)]
    end

    subgraph Phase 3: Load (load.py)
        L[load_data_to_db]
    end

    subgraph Database Storage
        DB[(f1_strategy.db\nSQLite Database)]
        TB1[Table: f1_laps]
        TB2[Table: f1_race_results]
        TB3[Table: f1_stint_summaries]
    end

    %% Flow Connections
    API -->|Fetch Session| A
    C -.->|Cache| A
    A -->|Save| R1
    A -->|Save| R2
    
    R1 -->|Read| T
    R2 -->|Read| T
    
    T --> O1
    O1 --> O2
    O2 --> O3
    
    O3 -->|Save| P1
    O3 -->|Save| P2
    O3 -->|Save| P3

    P1 -->|Read| L
    P2 -->|Read| L
    P3 -->|Read| L

    L -->|Write| DB
    DB --> TB1
    DB --> TB2
    DB --> TB3
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
