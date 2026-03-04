# Setup Instructions for Digital Twin Kerala AQI

This application provides a real-time air quality dashboard for Kerala, featuring XGBoost-based pollution forecasting and spatial heatmap visualizations.

## Prerequisites

Ensure you have the following installed:
- **Python 3.10+**
- **Node.js 18+** & **npm**

## 1. Backend Setup

1.  **Extract/Clone the repository** (if not already done).
2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If you encounter "externally-managed-environment" error on macOS, use a virtual environment:*
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Required OS Libraries**:
    Some geospatial libraries (for `geopandas`) might require system updates:
    ```bash
    brew install gdal  # macOS
    ```

## 2. Frontend Setup

1.  Navigate to the dashboard directory:
    ```bash
    cd dashboard
    ```
2.  **Install Node dependencies**:
    ```bash
    npm install
    ```
3.  **Build the production bundle**:
    ```bash
    npm run build
    ```

## 3. Running the Application

### Step A: Generate Forecasting Data
Run the ML pipeline script to train the model and generate the spatial heatmap files needed for the dashboard.
```bash
python3 ml_prediction_digital_twin.py
```
*Outputs will be saved in `dashboard/static/images/`.*

### Step B: Launch the Dashboard
Start the Flask application:
```bash
python3 dashboard/app.py
```
By default, the application will be available at: **http://127.0.0.1:5002**

## 4. Features Guide
- **Predictive Panel**: View 24h/168h forecasts for selected locations.
- **Meteorological Insights**: Real-time Temperature, Humidity, and Wind data.
- **Heatmap Tab**: A dedicated full-page view showing the spatial distribution of pollutants across Kerala.
- **3D Hub**: Volumetric visualization of pollution data.
