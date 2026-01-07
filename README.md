# 🏎️ PitWall – F1 Race Strategy Predictor

**PitWall** is a full-stack data science application that analyzes Formula 1 telemetry and race strategy in real-time. Unlike generic predictors, it functions like a Race Engineer's dashboard, visualizing tyre degradation, cornering speeds, and pit stop windows using official timing data.

## 🚀 Features

### 1. ⚡ Telemetry Duel
* **The Problem:** Comparing driver speeds is difficult because tracks have different lengths and corner profiles.
* **The Solution:** Aligns driver telemetry traces by **Distance** (not time) to overlay speed profiles perfectly.
* **Insight:** "See exactly where Verstappen brakes later than Norris at Turn 1."

### 2. 🛞 Tyre Degradation Analysis
* **The Problem:** Raw lap times are noisy due to traffic and fuel burn.
* **The Solution:** Filters data using the **107% Rule** (removing Safety Car/In-laps) and fits a **Linear Regression** model (Scikit-Learn) to calculate the seconds lost per lap due to wear.
* **Insight:** "The Hard tyre is losing 0.12s of pace per lap."

### 3. 🏁 The Undercut Detector
* **The Problem:** TV broadcasts rarely show the "Gap to Leader" effectively during pit windows.
* **The Solution:** Visualizes the entire race trace, highlighting vertical drops (Pit Stops) and relative track position.
* **Insight:** "Did the undercut strategy work? See where the driver exited relative to traffic."

---

## 🛠️ Tech Stack

* **Data Source:** [FastF1](https://github.com/theOehrly/Fast-F1) (Official F1 Live Timing API wrapper)
* **App Framework:** Streamlit
* **Data Processing:** Pandas, NumPy
* **Machine Learning:** Scikit-Learn (Linear Regression)
* **Visualization:** Matplotlib, Seaborn
* **Deployment:** AWS EC2 (Ubuntu Linux)

---

## 💻 Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/yourusername/pitwall-f1.git](https://github.com/yourusername/pitwall-f1.git)
    cd pitwall-f1
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**
    ```bash
    streamlit run app.py
    ```

---

## 📂 Project Structure

```text
pitwall-f1/
├── app.py                # Main application logic
├── requirements.txt      # Python dependencies
├── cache/                # Local cache for FastF1 data (auto-generated)
└── README.md             # Project documentation
```

---

## 🧠 Key Technical Challenges Solved

- **Data Synchronization:** Telemetry streams often have different sampling rates. I used interpolation to map speed traces to a common distance metric.

- **API Optimization:** Implemented st.cache_data to prevent re-downloading heavy telemetry files (50MB+) on every user interaction, reducing load times by 90%.

- **Noise Filtering:** Developed a robust filtering algorithm to exclude VSC (Virtual Safety Car) and Pit Laps from the regression model to ensure accurate degradation predictions.

---

## 🔮 Future Improvements

- **Machine Learning:** Implement a Random Forest Regressor to predict "Box Lap" based on tyre life.

- **Live Mode:** Connect to the live session stream for real-time race weekend analysis.

---

Built with ❤️ by **Chanthul**
