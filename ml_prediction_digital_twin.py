import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor
from sklearn.metrics import r2_score
import folium
from folium.plugins import HeatMap
import os
import sys
import io
import matplotlib.pyplot as plt

# Capture output
output_capture = io.StringIO()
sys.stdout = output_capture

# =========================================
# CONFIGURATION
# =========================================
DATA_FILE = 'ml/merged_hourly_data.csv'
BOUNDARY_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IND_1.json"

# Save outputs to dashboard static folder so Flask can serve them
OUTPUT_DIR = 'dashboard/static/images'
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_MAP = os.path.join(OUTPUT_DIR, 'aqi_heatmap_kerala.html')
OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, 'aqi_heatmap_kerala.png')
OUTPUT_LOG = os.path.join(OUTPUT_DIR, 'ml_output.txt')

# =========================================
# LOAD DATA
# =========================================
if not os.path.exists(DATA_FILE):
    # Fallback to local directory if run from within ml/
    DATA_FILE = 'merged_hourly_data.csv'

print(f"Loading data from {DATA_FILE}...")
df = pd.read_csv(DATA_FILE)

# =========================================
# DATA PREPROCESSING & SCALING
# =========================================
pollutant_cols = ['pm2p5', 'pm10', 'co', 'no2', 'go3', 'so2']
if df[pollutant_cols].max().max() < 1e-3:
    print("Detected units in kg/m^3. Scaling to mg/m^3 for better alignment with notebook logs...")
    for col in pollutant_cols:
        df[col] = df[col] * 1e6 

# =========================================
# TIME FEATURE ENGINEERING
# =========================================
df['time'] = pd.to_datetime(df['time'], dayfirst=True)
df['hour'] = df['time'].dt.hour
df['day'] = df['time'].dt.day
df['month'] = df['time'].dt.month
df['dayofweek'] = df['time'].dt.dayofweek
df = df.drop(columns=['time'])

# =========================================
# DEFINE FEATURES & TARGETS
# =========================================
features = ['latitude','longitude','u10','v10','t2m','sst','tp',
            'hour','day','month','dayofweek']

targets = ['pm2p5','pm10','co','no2','go3','so2']

# Fill NaNs if any
df = df.fillna(df.mean())

X = df[features]
y = df[targets]

# =========================================
# TRAIN TEST SPLIT
# =========================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

# =========================================
# TRAIN XGBOOST MODEL
# =========================================
print("Training XGBoost MultiOutputRegressor model...")
xgb = XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    objective='reg:squarederror'
)

model = MultiOutputRegressor(xgb)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("Model R2 Score:", r2_score(y_test, y_pred))

# =========================================
# LOAD KERALA BOUNDARY
# =========================================
print("Loading Kerala boundary...")
try:
    states = gpd.read_file(BOUNDARY_URL)
    kerala = states[states['NAME_1'] == 'Kerala']
    kerala = kerala.to_crs("EPSG:4326")
except Exception as e:
    print(f"Error loading boundary from URL: {e}")
    kerala = None

# =========================================
# CREATE HIGH RESOLUTION GRID (0.05° ≈ 5km)
# =========================================
print("Creating dense grid...")
lat_vals = np.arange(8.0, 12.6, 0.05)
lon_vals = np.arange(74.8, 77.2, 0.05)

grid_points = [(lat, lon) for lat in lat_vals for lon in lon_vals]
grid_df = pd.DataFrame(grid_points, columns=['latitude','longitude'])

geometry = [Point(xy) for xy in zip(grid_df['longitude'], grid_df['latitude'])]
grid_gdf = gpd.GeoDataFrame(grid_df, geometry=geometry, crs="EPSG:4326")

if kerala is not None:
    kerala_geom = kerala.union_all() if hasattr(kerala, 'union_all') else kerala.unary_union
    grid_gdf = grid_gdf[grid_gdf.within(kerala_geom)]
    print(f"Points inside Kerala: {len(grid_gdf)}")

# =========================================
# ADD REQUIRED FEATURES (Use Mean Met Values)
# =========================================
for col in ['u10','v10','t2m','sst','tp',
            'hour','day','month','dayofweek']:
    grid_gdf[col] = df[col].mean()

# =========================================
# PREDICT POLLUTANTS FOR DENSE GRID
# =========================================
print("Predicting pollutants for grid points...")
grid_features = grid_gdf[features]
grid_pred = model.predict(grid_features)

pred_df = pd.DataFrame(grid_pred, columns=targets)
pred_df = pred_df.clip(lower=0)

pred_df['latitude'] = grid_gdf['latitude'].values
pred_df['longitude'] = grid_gdf['longitude'].values

# =========================================
# AQI SUBINDEX FUNCTION
# =========================================
def subindex(conc, breakpoints):
    for Clow, Chigh, Ilow, Ihigh in breakpoints:
        if conc <= Chigh:
            return ((Ihigh - Ilow)/(Chigh - Clow)) * (conc - Clow) + Ilow
    return 500

pm25_bp = [(0,30,0,50),(30,60,50,100),(60,90,100,200),
           (90,120,200,300),(120,250,300,400),(250,500,400,500)]
pm10_bp = [(0,50,0,50),(50,100,50,100),(100,250,100,200),
           (250,350,200,300),(350,430,300,400),(430,600,400,500)]
no2_bp = [(0,40,0,50),(40,80,50,100),(80,180,100,200),
          (180,280,200,300),(280,400,300,400),(400,800,400,500)]
o3_bp = [(0,50,0,50),(50,100,50,100),(100,168,100,200),
         (168,208,200,300),(208,748,300,400),(748,1000,400,500)]
co_bp = [(0,1,0,50),(1,2,50,100),(2,10,100,200),
         (10,17,200,300),(17,34,300,400),(34,50,400,500)]
so2_bp = [(0,40,0,50),(40,80,50,100),(80,380,100,200),
          (380,800,200,300),(800,1600,300,400),(1600,2000,400,500)]

# =========================================
# CALCULATE AQI
# =========================================
print("Calculating AQI...")
pred_df['AQI_PM25'] = pred_df['pm2p5'].apply(lambda x: subindex(x, pm25_bp))
pred_df['AQI_PM10'] = pred_df['pm10'].apply(lambda x: subindex(x, pm10_bp))
pred_df['AQI_NO2'] = pred_df['no2'].apply(lambda x: subindex(x, no2_bp))
pred_df['AQI_O3'] = pred_df['go3'].apply(lambda x: subindex(x, o3_bp))
pred_df['AQI_CO'] = pred_df['co'].apply(lambda x: subindex(x, co_bp))
pred_df['AQI_SO2'] = pred_df['so2'].apply(lambda x: subindex(x, so2_bp))

pred_df['Final_AQI'] = pred_df[
    ['AQI_PM25','AQI_PM10','AQI_NO2','AQI_O3','AQI_CO','AQI_SO2']
].max(axis=1)

print("Final AQI Range:", pred_df['Final_AQI'].min(), "to", pred_df['Final_AQI'].max())

# =========================================
# CREATE HIGH-RESOLUTION HEATMAP (INTERACTIVE)
# =========================================
print(f"Generating interactive heatmap and saving to {OUTPUT_MAP}...")
m = folium.Map(location=[10.5, 76.5], zoom_start=7)

if kerala is not None:
    folium.GeoJson(kerala, name="Kerala Boundary").add_to(m)

aqi_min = pred_df['Final_AQI'].min()
aqi_max = pred_df['Final_AQI'].max()

if aqi_max > aqi_min:
    pred_df['AQI_norm'] = (pred_df['Final_AQI'] - aqi_min) / (aqi_max - aqi_min)
else:
    pred_df['AQI_norm'] = 0.5

heat_data = [[row['latitude'], row['longitude'], row['AQI_norm']] for _, row in pred_df.iterrows()]

HeatMap(
    heat_data,
    radius=20,
    blur=15,
    min_opacity=0.4
).add_to(m)

m.save(OUTPUT_MAP)

# =========================================
# CREATE STATIC IMAGE (MATPLOTLIB)
# =========================================
print(f"Generating static image and saving to {OUTPUT_IMAGE}...")

plt.figure(figsize=(10, 12))
ax = plt.gca()

if kerala is not None:
    kerala_geom = kerala.union_all() if hasattr(kerala, 'union_all') else kerala.unary_union
    kerala.plot(ax=ax, color='lightgrey', edgecolor='black', alpha=0.5)

scatter = ax.scatter(
    pred_df['longitude'], 
    pred_df['latitude'], 
    c=pred_df['Final_AQI'], 
    cmap='RdYlGn_r', 
    s=20, 
    alpha=0.6,
    edgecolors='none'
)

plt.colorbar(scatter, label='Final AQI')
plt.title('Kerala Air Quality Index (AQI) Heatmap')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.grid(True, linestyle='--', alpha=0.5)

plt.savefig(OUTPUT_IMAGE, dpi=300, bbox_inches='tight')
plt.close()

print("Done!")

# Restore stdout and save log
sys.stdout = sys.__stdout__
with open(OUTPUT_LOG, 'w') as f:
    f.write(output_capture.getvalue())
print(output_capture.getvalue())
