# 🌫️ Digital Twin AQI — Kerala

> **A real-time, physics-driven, AI-augmented Digital Twin for Air Quality monitoring and forecasting across the state of Kerala, India.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-black?logo=flask)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://reactjs.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06b6d4?logo=tailwindcss)](https://tailwindcss.com)
[![Data: Open-Meteo](https://img.shields.io/badge/Data-Open--Meteo-green)](https://open-meteo.com)

---

## 📑 Table of Contents

1. [Problem Definition](#-problem-definition)
2. [Project Objective](#-project-objective)
3. [Purpose and Need](#-purpose-and-need)
4. [Requirements](#-requirements)
   - [Functional Requirements](#functional-requirements)
   - [Non-Functional Requirements](#non-functional-requirements)
   - [System Requirements](#system-requirements)
   - [Data Requirements](#data-requirements)
5. [Quick Start](#-quick-start)
6. [Project Structure](#-project-structure)
7. [Contributors](#-contributors)

---

## 🚨 Problem Definition

### The Air Quality Crisis in Kerala

Air quality degradation is a growing crisis across urban and semi-urban India. Kerala, despite its green image, faces escalating pollution levels driven by:

- **Rapid urbanisation** in cities like Kochi (Ernakulam), Thrissur, and Thiruvananthapuram, leading to increased vehicular density and road dust.
- **Industrial corridors** — particularly in Eloor (Udyogamandal) near Kochi, one of India's most industrially dense zones, with paper mills, fertiliser plants, and petrochemical units releasing SO₂, NO₂, and particulate matter.
- **Coastal meteorology** — Kerala's geography as a narrow coastal strip sandwiched between the Arabian Sea and Western Ghats creates complex wind patterns that trap or disperse pollutants unpredictably.
- **Monsoon variability** — Seasonal rainfall washout of aerosols creates a false seasonal sense of safety, while post-monsoon months witness sharp AQI spikes.
- **Data blindspots** — India's official CPCB (Central Pollution Control Board) monitoring network has extremely limited coverage in Kerala, with most automated monitoring stations (CAAQMS) concentrated in Thiruvananthapuram and Ernakulam, leaving over 10 districts without real-time sensor infrastructure.

### The Measurement Gap

The consequence of sparse monitoring is a **systemic inability** to:
- Understand real-time pollution exposure for over 3.5 crore residents.
- Provide early warning of pollutant spikes to vulnerable populations (children, elderly, those with respiratory conditions).
- Correlate meteorological events (wind shifts, rain, temperature inversions) with pollutant behaviour in a physics-consistent manner.
- Generate future-looking forecasts needed for proactive urban governance, construction planning, and public health advisories.

### Why Current Solutions Fall Short

| Existing Approach | Limitation |
|---|---|
| Static CPCB monitors | Too sparse; delayed data; no forecasting |
| Satellite-based estimates (Sentinel-5P, MODIS) | Coarse spatial resolution (~3.5km); cloud-obscured during monsoon |
| Generic national AQI apps | India-wide models; lack regional meteorological precision for Kerala |
| Research models (CMAQ, WRF-Chem) | Computationally prohibitive; require supercomputing infrastructure |

This project directly addresses this gap by building a **lightweight but physics-grounded Digital Twin** that fuses real-time telemetry with machine learning and rule-based simulation.

---

## 🎯 Project Objective

The Digital Twin AQI Kerala project aims to build a **fully integrated, real-time, intelligent air quality monitoring and forecasting platform** for the state of Kerala. The specific objectives are:

### Primary Objectives

1. **Construct a real-time data pipeline** that continuously fetches live air quality (PM2.5, PM10, NO₂, SO₂, CO, O₃) and meteorological data (temperature, humidity, wind speed, wind direction, precipitation) for **12 key monitoring nodes** across Kerala using the Open-Meteo API.

2. **Implement a physics-driven Digital Twin engine** that simulates pollutant transport and transformation using an explainable rule-based system inspired by atmospheric science:
   - Wind dispersion and dilution
   - Rain washout of particulate matter
   - Stagnant air accumulation during low-wind conditions
   - Temperature-driven ozone photochemical formation
   - Coastal sea-breeze effects and marine aerosol loading
   - Traffic emission peaks during commute hours
   - Nocturnal boundary-layer accumulation

3. **Train and deploy a machine learning forecasting model** using historical CAMS/ERA5 reanalysis data to produce 24-hour ahead AQI forecasts using Random Forest and XGBoost regressors.

4. **Build an interactive, professional-grade web dashboard** that visualises:
   - Live pollutant concentrations per location
   - 24-hour AQI trajectory from the Digital Twin simulation
   - Physics-rule attribution panel (showing which atmospheric rule contributed how much to AQI change)
   - ML-based live neural network forecast
   - Spatial interpolated AQI heatmaps for the entire state of Kerala
   - Meteorological insights (temperature, humidity, wind) per node

5. **Compute Indian AQI** following the official CPCB sub-index breakpoint methodology for six pollutants: PM2.5, PM10, NO₂, SO₂, CO, and O₃.

### Secondary Objectives

- Provide **explainability** — users can see exactly which physical rule (e.g., "Wind Dispersion", "Marine Aerosol") contributed to an AQI change and by how many units.
- Ensure **graceful fallback** — if live API data is unavailable, the dashboard degrades gracefully with simulated fallback data.
- Build a **modular, extensible architecture** that can accommodate future sensors, ML models, or additional cities with minimal changes.

---

## 💡 Purpose and Need

### Societal Purpose

This system directly serves the public interest by:

- **Empowering citizens** with accurate, location-specific air quality information far beyond what commercial AQI apps provide for Kerala.
- **Enabling health-protective behaviour** — individuals with asthma, COPD, or cardiovascular conditions can plan outdoor activities based on the 24-hour forecast panel.
- **Supporting urban planners and municipal bodies** (e.g., GCDA, TRIDA) in identifying pollution hotspots and planning traffic management or green buffers.

### Scientific Purpose

- Demonstrates that a **Digital Twin paradigm** — traditionally applied to industrial equipment — can be adapted for atmospheric and environmental systems.
- Validates that a lightweight, physics-rule-based model faithfully approximates the behaviour of complex chemical transport models (CTMs) using only freely available meteorological data.
- Provides a reproducible, open-source framework for similar efforts in other Indian coastal cities (Mangalore, Mumbai, Visakhapatnam).

### Need for a Physics-Driven Digital Twin vs Pure ML

A purely statistical ML model, however accurate, is a **black box** — it cannot explain *why* AQI is rising or falling. This is critically important because:
- A health official needs to know if the spike is due to industrial emissions or a traffic surge.
- An urban planner needs to understand whether tree cover along a road would reduce PM2.5, and by how much.
- A researcher needs to validate model outputs against physical atmospheric theory.

The Digital Twin's rule engine provides this **causal attribution** — every simulated AQI step carries a full audit trail of which rules fired, what meteorological conditions triggered them, and what the quantified pollutant impact was.

---

## 📋 Requirements

### Functional Requirements

#### FR-1: Live Data Ingestion
- The system **shall** fetch live pollutant concentrations (PM2.5, PM10, NO₂, SO₂, CO, O₃) for at least 10 Kerala locations every 60 seconds.
- The system **shall** fetch concurrent meteorological variables: temperature (°C), relative humidity (%), wind speed (km/h), and precipitation (mm).
- Data shall be served through a REST API endpoint (`/api/live-aqi`) returning a structured JSON payload.
- The fetcher **shall** implement a 55-second in-memory cache to prevent API rate-limit violations.

#### FR-2: AQI Calculation
- The system **shall** compute the Indian National AQI using the CPCB sub-index breakpoint method for each of the six pollutants.
- The dominant pollutant driving the AQI **shall** be identified and reported.
- Computation **shall** require at least 3 pollutant sub-indices to be valid, with at least one being a particulate (PM2.5 or PM10).

#### FR-3: Digital Twin Simulation
- The Digital Twin **shall** simulate hourly AQI trajectories for a 24-hour period.
- Each simulation step **shall** apply the complete physics rule pipeline in sequence: wind dispersion → rain washout → stagnant accumulation → temperature-ozone photochemistry → coastal sea breeze → traffic emissions → night accumulation.
- All rules **shall** record their per-pollutant delta (change), enabling attributional explainability.
- Simulated states **shall** be initialised from live Open-Meteo data for the selected location.
- Weather inputs for future hours **shall** be sourced from Open-Meteo's hourly weather forecast API.
- The system **shall** expose simulated history, dominant pollutant, and rule effects via `/api/dt-insights`.

#### FR-4: Machine Learning Forecasting
- The ML pipeline **shall** train models on historical merged hourly CAMS/ERA5 data (`merged_hourly_data.csv`).
- Training **shall** use time-safe train/validation/test splits (75%/15%/10%) to prevent data leakage.
- Feature engineering **shall** include lag features (1h, 3h, 6h, 12h, 24h), rolling statistics (3h, 6h, 24h), and calendar features (hour, day-of-week).
- The live predictor **shall** use the pre-trained `statewide_model.joblib` to generate 24-hour ahead AQI forecasts.
- Forecast results **shall** be exposed via `/api/live-prediction?lat=&lon=`.

#### FR-5: Interactive Dashboard
- The dashboard **shall** display a panel for each of: Live Pollutants, Meteorological Insights, Synchronising Nodes, and Location Selection on the main view.
- A tab navigation **shall** allow switching between: Predictive Forecast, Twin Insights, 3D Hub, and Heatmap.
- The map **shall** display coloured markers for all monitored nodes, with AQI-based colour coding.
- The Twin Insights view **shall** show a 24-hour line chart of simulated AQI trajectory and a physics impact attribution list.
- The Predictive Panel **shall** show a line chart of ML-forecasted AQI for the next 24 hours.

#### FR-6: Heatmap
- The system **shall** generate a spatial interpolated heatmap of AQI across Kerala's 14 districts.
- Heatmaps **shall** be generated via `ml_prediction_digital_twin.py` and served from `dashboard/static/images/`.

---

### Non-Functional Requirements

#### NFR-1: Performance
- The live AQI API response (`/api/live-aqi`) **shall** respond within **3 seconds** under normal network conditions, leveraging in-memory caching.
- The Digital Twin simulation for 24 hours **shall** complete within **2 seconds** on a standard laptop CPU.
- The React frontend **shall** achieve a First Contentful Paint (FCP) below **2.5 seconds** on a modern browser.

#### NFR-2: Reliability & Resilience
- The system **shall** implement graceful fallback: if live data fetching fails, the frontend **shall** show the last known data with a "Live link disrupted" warning rather than crashing.
- The ML predictor **shall** fall back to a physics-based sinusoidal simulation if the `statewide_model.joblib` file is unavailable.
- All pollutant values **shall** be clamped to non-negative values and a maximum of 1000 µg/m³ to prevent nonsensical simulation outputs.

#### NFR-3: Explainability
- Every AQI change attributed to a rule **shall** be quantified in units of concentration change and exposed to the API consumer.
- The dominant pollutant driving the overall AQI **shall** be clearly identified at every simulation step.

#### NFR-4: Maintainability
- The codebase **shall** follow a clear module separation: `aqi_logic/`, `dt/`, `ml/`, `dashboard/`, and `sensors/`.
- Adding a new physics rule **shall** require only: implementing a function in `dt/rules/current_aqi_rules.py` and appending it to `RULE_PIPELINE`.
- Adding a new monitoring node **shall** require only editing the `get_kerala_locations()` method in `OpenMeteoAQIFetcher`.

#### NFR-5: Usability
- The dashboard **shall** be responsive and legible at a minimum resolution of 1280×720 pixels.
- The UI **shall** use a high-contrast white-background theme suitable for presentation in brightly lit environments such as classrooms or conference rooms.
- All colour-coded data (AQI bars, trend indicators) **shall** follow CPCB's green-yellow-orange-red-maroon colour scale.

---

### System Requirements

#### Hardware
| Component | Minimum | Recommended |
|---|---|---|
| CPU | Dual-core 2.0GHz | Quad-core 3.0GHz+ |
| RAM | 4 GB | 8 GB |
| Storage | 2 GB (for ML model & CSV) | 5 GB |
| Network | Stable internet (Open-Meteo API) | Broadband ≥10 Mbps |

#### Software
| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend runtime |
| Flask | 2.x | REST API server |
| Node.js | 18+ | Frontend build tool |
| npm | 9+ | Package manager |
| React | 18 | Frontend UI framework |
| Vite | 5 | Frontend bundler |
| TailwindCSS | 3 | Utility-first CSS |
| Pandas | ≥1.5 | Data processing |
| scikit-learn | ≥1.2 | ML training/inference |
| XGBoost | ≥1.7 | ML model (optional) |
| Joblib | ≥1.2 | Model serialisation |
| NumPy | ≥1.24 | Numerical computation |
| Matplotlib | ≥3.6 | Heatmap generation |
| Requests | ≥2.28 | HTTP API calls |

#### Python Dependencies (install via `pip`)
```
flask
numpy
pandas
scikit-learn
joblib
matplotlib
xgboost
requests
earthengine-api
google-auth
scipy
```

---

### Data Requirements

#### External APIs
| API | Endpoint | Variables Fetched | Rate Limit |
|---|---|---|---|
| Open-Meteo Air Quality | `air-quality-api.open-meteo.com/v1/air-quality` | PM10, PM2.5, CO, NO₂, SO₂, O₃, UV Index, Dust | Free tier |
| Open-Meteo Weather | `api.open-meteo.com/v1/forecast` | Temperature, Humidity, Wind Speed, Wind Direction, Precipitation | Free tier |

Both APIs are free and require no API key.

#### Historical Training Data
- **File:** `ml/merged_hourly_data.csv` (~4.3 MB)
- **Source:** Merged CAMS (Copernicus Atmosphere Monitoring Service) and ERA5 (ECMWF Reanalysis) reanalysis data.
- **Variables:** `pm2p5`, `pm10`, `co`, `no2`, `go3` (ozone), `so2`, `t2m` (temperature), `u10`/`v10` (wind components), latitude, longitude, time.
- **Coverage:** Hourly records spanning multiple years across Kerala coordinates.
- **Unit:** Raw values in kg/m³, converted to µg/m³ by multiplication by 1×10⁹.

#### Monitored Locations
| # | Location | Latitude | Longitude |
|---|---|---|---|
| 1 | Kochi (Vytilla) | 9.9312 | 76.2673 |
| 2 | Thiruvananthapuram | 8.5241 | 76.9366 |
| 3 | Kozhikode | 11.2588 | 75.7804 |
| 4 | Thrissur | 10.5276 | 76.2144 |
| 5 | Kollam | 8.8932 | 76.6141 |
| 6 | Palakkad | 10.7867 | 76.6547 |
| 7 | Alappuzha | 9.4981 | 76.3388 |
| 8 | Kottayam | 9.5916 | 76.5222 |
| 9 | Kannur | 11.8745 | 75.3704 |
| 10 | Malappuram | 11.0735 | 76.0740 |
| 11 | Eloor | 10.0754 | 76.2995 |
| 12 | Kakkanad | 10.0159 | 76.3419 |

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/psbuilds/Digital-Twin.git
cd Digital-Twin-Aqi-Kochi
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # On macOS/Linux
# .\venv\Scripts\activate  # On Windows

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd dashboard
npm install
npm run build
cd ..
```

### 4. (Optional) Train the ML Model
```bash
python3 ml_prediction_digital_twin.py
```
This generates heatmap images in `dashboard/static/images/`.

### 5. Run the Server
```bash
python3 dashboard/app.py
```

Open your browser at **http://127.0.0.1:5002**

---

## 📁 Project Structure

```
Digital-Twin-Aqi-Kochi/
├── aqi_logic/                   # AQI computation utilities
│   ├── open_meteo_fetcher.py    # Live data ingestion (12 Kerala nodes)
│   ├── current_aqi_rules.py     # CPCB sub-index calculator
│   └── status_mapping.py        # AQI → category/colour mapper
│
├── dt/                          # Digital Twin engine
│   ├── models/twin_state.py     # TwinState dataclass (all state variables)
│   ├── engine/state_updater.py  # 24h simulation loop
│   ├── features/feature_builder.py  # Meteorological feature extraction
│   └── rules/current_aqi_rules.py  # Physics rule pipeline (7 rules)
│
├── ml/                          # Machine Learning forecasting
│   ├── ml_pipeline.py           # Training pipeline (lag features + RF/XGBoost)
│   ├── live_predictor.py        # Real-time 24h AQI forecast
│   ├── predict_future_aqi.py    # District-level forecast aggregation
│   ├── statewide_model.joblib   # Trained model artifact
│   └── merged_hourly_data.csv   # Historical CAMS/ERA5 training data
│
├── dashboard/                   # Full-stack web application
│   ├── app.py                   # Flask REST API backend
│   ├── src/
│   │   ├── App.jsx              # Main React application shell
│   │   ├── components/
│   │   │   ├── PollutantPanel.jsx    # Live pollutant bars
│   │   │   ├── PredictivePanel.jsx   # ML 24h forecast chart
│   │   │   ├── TwinInsights.jsx      # DT simulation chart + rule impacts
│   │   │   ├── AtmosphericDNA.jsx    # Temperature/humidity/wind display
│   │   │   ├── MapViewer.jsx         # Leaflet interactive map
│   │   │   ├── LocationSelector.jsx  # Location dropdown
│   │   │   ├── SyncNodes.jsx         # Node sync status panel
│   │   │   └── HeatmapSection.jsx    # Statewide heatmap viewer
│   │   └── index.css            # Global Tailwind styles
│   └── static/images/           # Generated heatmap PNGs
│
├── ml_prediction_digital_twin.py  # Offline ML pipeline + heatmap generator
├── requirements.txt
├── README.md
└── docs/architecture.md
```

---

## 👤 Contributors

Developed as a Mini Project submission.

- **Ryan George** — Full-Stack Development, Digital Twin Engine, ML Integration

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
