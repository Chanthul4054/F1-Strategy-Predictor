import streamlit as st
import fastf1
import fastf1.plotting
import pandas as pd
import matplotlib.pyplot as plt

# 1. Page Configuration
st.set_page_config(page_title="PitWall | F1 Strategy Predictor", layout="wide")
st.title("🏎️ PitWall: F1 Race Strategy Predictor")

# 2. Setup FastF1 Caching (CRITICAL for performance)
cache_dir = 'cache'
fastf1.Cache.enable_cache(cache_dir) 

# 3. Sidebar: Race Selection
st.sidebar.header("Race Selection")
year = st.sidebar.selectbox("Year", [2024, 2023, 2022], index=0)
grand_prix = st.sidebar.selectbox("Grand Prix", ["Bahrain", "Saudi Arabia", "Monza", "Silverstone", "Monaco"], index=2)
session_type = st.sidebar.selectbox("Session", ["FP1", "FP2", "FP3", "Q", "R"], index=3)

# 4. Helper Function to Load Data
@st.cache_data
def load_session_data(year, gp, session_type):
    """
    Wrapper to load session data with Streamlit caching.
    """
    try:
        session = fastf1.get_session(year, gp, session_type)
        session.load()
        return session
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load the data when user interacts
if st.button("Load Session Data"):
    with st.spinner(f"Downloading Telemetry for {grand_prix} {year}..."):
        session = load_session_data(year, grand_prix, session_type)
        if session:
            st.success("Data Loaded Successfully!")
            st.session_state['session'] = session # Store in session state

# 5. Main Application Logic
if 'session' in st.session_state:
    session = st.session_state['session']
    
    # Create Tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs(["⚡ Telemetry Duel", "🛞 Tyre Analysis", "🏁 Race Strategy", "🤖 Pit Strategy Predictor"])

    # --- FEATURE 1: TELEMETRY DUEL ---
    with tab1:
        st.header("Driver Speed Comparison")
        
        # Driver Selection
        drivers = sorted(session.results['Abbreviation'].unique())
        col1, col2 = st.columns(2)
        with col1:
            driver1 = st.selectbox("Driver 1", drivers, index=0)
        with col2:
            driver2 = st.selectbox("Driver 2", drivers, index=1)

        if st.button("Compare Telemetry"):
            # Get Fastest Laps
            d1_lap = session.laps.pick_driver(driver1).pick_fastest()
            d2_lap = session.laps.pick_driver(driver2).pick_fastest()

            # Get Telemetry Data (Speed, RPM, Gear, etc.)
            d1_tel = d1_lap.get_car_data().add_distance()
            d2_tel = d2_lap.get_car_data().add_distance()

            # Plotting
            fastf1.plotting.setup_mpl() 
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Plot Driver 1
            d1_color = fastf1.plotting.get_driver_color(driver1, session=session)
            ax.plot(d1_tel['Distance'], d1_tel['Speed'], color=d1_color, label=driver1)
            
            # Plot Driver 2
            d2_color = fastf1.plotting.get_driver_color(driver2, session=session)
            ax.plot(d2_tel['Distance'], d2_tel['Speed'], color=d2_color, label=driver2)

            ax.set_xlabel('Distance in Lap (m)')
            ax.set_ylabel('Speed (km/h)')
            ax.legend()
            st.pyplot(fig)

    # --- FEATURE 2: TYRE ANALYSIS ---
    with tab2:
        st.header("Tyre Degradation Analysis")
        st.markdown("Use Machine Learning to calculate how much pace a driver loses per lap due to tyre wear.")

        # 1. Select Driver and Compound
        col1, col2 = st.columns(2)
        with col1:
            driver_deg = st.selectbox("Select Driver", sorted(session.results['Abbreviation'].unique()), key="deg_driver")
        
        # Get all laps for this driver
        driver_laps = session.laps.pick_driver(driver_deg)
        
        # Find which compounds were used
        used_compounds = driver_laps['Compound'].unique()
        with col2:
            compound = st.selectbox("Select Compound", used_compounds, key="deg_compound")

        if st.button("Analyze Degradation"):
            from sklearn.linear_model import LinearRegression
            import numpy as np

            # 2. Data Pre-processing 
            stint_laps = driver_laps.pick_tyre(compound)
            
            stint_laps = stint_laps.pick_quicklaps().pick_track_status('1') 
            
            if len(stint_laps) > 5: # Need at least a few laps to make a prediction
                
                # Prepare Data for Scikit-Learn
                # X = Lap Number (Reshaped for sklearn)
                X = stint_laps['LapNumber'].values.reshape(-1, 1)
                
                # y = Lap Time in Seconds
                y = stint_laps['LapTime'].dt.total_seconds().values
                
                # 3. Linear Regression Model
                model = LinearRegression()
                model.fit(X, y)
                
                # Calculate predictions (Line of Best Fit)
                deg_rate = model.coef_[0] # The slope (m)
                y_pred = model.predict(X)

                # 4. Visualization
                fig, ax = plt.subplots(figsize=(10, 5))
                
                # Scatter plot of actual lap times
                ax.scatter(X, y, color='white', edgecolor='red', s=50, label='Actual Laps')
                
                # Line of Best Fit
                ax.plot(X, y_pred, color='red', linewidth=2, label=f'Degradation Model')
                
                ax.set_xlabel("Lap Number")
                ax.set_ylabel("Lap Time (s)")
                ax.set_title(f"{driver_deg} - {compound} Tyre Pace")
                ax.legend()
                
                # Dark background for F1 style
                ax.set_facecolor('black')
                fig.patch.set_facecolor('black')
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                ax.title.set_color('white')
                
                st.pyplot(fig)

                # Display Metrics
                st.metric(label="Estimated Degradation", value=f"+{deg_rate:.3f} sec/lap")
                
                if deg_rate < 0:
                    st.warning("⚠️ Negative degradation detected! This usually means fuel burn effect (car getting lighter) is stronger than tyre wear, or the track is evolving rapidly.")
            else:
                st.warning("Not enough clean laps data for this compound to run a regression analysis.")
        

    # --- FEATURE 3: RACE STRATEGY  ---
    with tab3:
        st.header("The Undercut Detector (Gap to Leader)")
        st.markdown("Analyze pit windows and traffic. A sharp rise in the line indicates a pit stop.")

        # Calculate Gap to Leader
        
        # Get the race winner
        winner_name = session.results.iloc[0]['Abbreviation']
        winner_laps = session.laps.pick_driver(winner_name)
        
        # Calculate the winner's cumulative time per lap
        winner_laps['RaceTime'] = winner_laps['LapTime'].cumsum()
        winner_trace = winner_laps[['LapNumber', 'RaceTime']].set_index('LapNumber')

        # 2. User Selection:
        top_5 = session.results['Abbreviation'].iloc[:5].tolist()
        selected_drivers = st.multiselect("Select Drivers to Trace", 
                                          options=sorted(session.results['Abbreviation'].unique()),
                                          default=top_5)

        if st.button("Generate Race Trace"):
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for driver in selected_drivers:
                driver_laps = session.laps.pick_driver(driver)
                
                # Calculate Driver's Race Time
                driver_laps['RaceTime'] = driver_laps['LapTime'].cumsum()
                
                # Merge with Winner's Time on LapNumber to calculate the gap
                df_merged = pd.merge(driver_laps[['LapNumber', 'RaceTime']], 
                                     winner_trace, 
                                     on='LapNumber', 
                                     suffixes=('_driver', '_winner'))
                
                # Calculate Gap (Driver Time - Winner Time)
                df_merged['GapToLeader'] = (df_merged['RaceTime_driver'] - df_merged['RaceTime_winner']).dt.total_seconds()
                
                # Plotting
                d_color = fastf1.plotting.get_driver_color(driver, session=session)
                ax.plot(df_merged['LapNumber'], df_merged['GapToLeader'], label=driver, color=d_color)

            # 3. Styling the Chart
            ax.set_ylabel("Gap to Leader (seconds)")
            ax.set_xlabel("Lap Number")
            ax.set_title(f"Race Trace: Gap to {winner_name}")
            
            # Invert Y-axis? 
            ax.invert_yaxis() 
            ax.legend()
            
            # Dark Mode Styling
            ax.set_facecolor('black')
            fig.patch.set_facecolor('black')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.5)

            st.pyplot(fig)
            
            st.info("""
            **How to read this chart:**
            - **The Baseline (Top):** The horizontal line at 0 is the Race Leader.
            - **Sloping Down:** The driver is losing time to the leader.
            - **Vertical Drop:** This is a **Pit Stop**. The size of the drop is the time lost in the pits (~20-25s).
            - **Traffic:** If a driver pits (drops) and their line lands *below* another driver's line, they have exited into traffic.
            """)

    # --- FEATURE 4: PIT STRATEGY PREDICTOR ---
    with tab4:
        st.header("Pit Strategy Predictor")
        st.markdown("Predicts if a driver is entering their pit window based on their current tyre age using a RandomForestClassifier trained on session stint data.")
        
        col1, col2 = st.columns(2)
        with col1:
            driver_pred = st.selectbox("Select Driver to Predict", sorted(session.results['Abbreviation'].unique()), key="pred_driver")
        
        # Prepare dataset of all stints for all drivers
        stints_data = []
        for d in session.results['Abbreviation'].unique():
            dlaps = session.laps.pick_driver(d)
            for stint, st_laps in dlaps.groupby('Stint'):
                if not st_laps.empty and pd.notna(st_laps['Compound'].iloc[0]):
                    max_laps = st_laps['LapNumber'].max()
                    compound = st_laps['Compound'].iloc[0]
                    stints_data.append({'Compound': compound, 'MaxTyreLife': len(st_laps)})
        
        if len(stints_data) > 0 and st.button("Predict Pit Window"):
            from sklearn.ensemble import RandomForestClassifier
            import numpy as np
            
            df_stints = pd.DataFrame(stints_data).dropna()
            
            # Synthetic dataset logic:
            # Generate laps 1 to MaxTyreLife. Pit window opens ~2 laps before the maximum life.
            train_data = []
            for _, row in df_stints.iterrows():
                comp = str(row['Compound'])
                max_life = row['MaxTyreLife']
                for lap in range(1, int(max_life) + 2):
                    is_pit_window = 1 if lap >= max_life - 2 else 0
                    train_data.append({'Compound': comp, 'TyreAge': lap, 'PitWindowOpen': is_pit_window})
            
            train_df = pd.DataFrame(train_data)
            
            # Feature Encoding
            train_df = pd.get_dummies(train_df, columns=['Compound'])
            X = train_df.drop('PitWindowOpen', axis=1)
            y = train_df['PitWindowOpen']
            
            # Train model
            rf_model = RandomForestClassifier(n_estimators=50, random_state=42)
            rf_model.fit(X, y)
            
            # Get Current data for driver
            current_laps = session.laps.pick_driver(driver_pred)
            if not current_laps.empty:
                last_lap = current_laps.iloc[-1]
                current_stint = last_lap['Stint']
                current_compound = str(last_lap['Compound'])
                current_tyre_age = len(current_laps[current_laps['Stint'] == current_stint])
                
                # Inference row
                inf_row = {'TyreAge': current_tyre_age}
                for c in X.columns:
                    if c.startswith('Compound_'):
                        inf_row[c] = 1 if c == f"Compound_{current_compound}" else 0
                
                inf_df = pd.DataFrame([inf_row])
                for c in X.columns: # Ensure exact same columns
                    if c not in inf_df.columns:
                        inf_df[c] = 0
                inf_df = inf_df[X.columns]
                
                prob = rf_model.predict_proba(inf_df)[0][1] * 100
                st.subheader(f"Strategy Prediction for {driver_pred}")
                
                col3, col4, col5 = st.columns(3)
                col3.metric(label="Probability of Pit Window", value=f"{prob:.1f}%")
                col4.metric(label="Current Compound", value=current_compound)
                col5.metric(label="Tyre Age", value=f"{current_tyre_age} laps")
                
                if prob > 70:
                    st.error(f"🚨 High probability! Pit window is OPEN for {driver_pred}. Recommended to box soon.")
                elif prob > 40:
                    st.warning(f"⚠️ Nearing pit window. Degradation is likely becoming an issue.")
                else:
                    st.success(f"✅ Tyre life is good. Keep pushing.")

            else:
                st.warning("No lap data available for this driver yet.")

else:
    st.info("👈 Please select a race and click 'Load Session Data' to begin.")