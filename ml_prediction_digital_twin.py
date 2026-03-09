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
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import PathPatch
import matplotlib.path as mpath
import joblib
import json
from scipy.interpolate import griddata

# Capture output
output_capture = io.StringIO()
sys.stdout = output_capture
# =========================================
DATA_FILE = 'ml/merged_hourly_data.csv'
BOUNDARY_FILE = 'dashboard/static/data/kerala_districts.json'

# Save outputs to dashboard static folder so Flask can serve them
OUTPUT_DIR = 'dashboard/static/images'
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_MAP = os.path.join(OUTPUT_DIR, 'aqi_heatmap_interactive.html')
# We will generate TWO static images now
OUTPUT_IMG_ACTUAL = os.path.join(OUTPUT_DIR, 'aqi_heatmap_actual.png')
OUTPUT_IMG_PRED = os.path.join(OUTPUT_DIR, 'aqi_heatmap_predicted.png')
OUTPUT_LOG = os.path.join(OUTPUT_DIR, 'ml_output.txt')
MODEL_PATH = 'ml/statewide_model.joblib'
# =========================================
if not os.path.exists(DATA_FILE):
    DATA_FILE = 'merged_hourly_data.csv'

print(f"Loading data from {DATA_FILE}...")
df = pd.read_csv(DATA_FILE)
# =========================================
pollutant_cols = ['pm2p5', 'pm10', 'co', 'no2', 'go3', 'so2']
if df[pollutant_cols].max().max() < 1e-3:
    print("Detected units in kg/m^3. Scaling to ug/m^3 (multiplier 1e9)...")
    for col in pollutant_cols:
        df[col] = df[col] * 1e9

# Adjustment for CO: breakpoints are in mg/m^3, CAMS CO is in kg/m^3
# so for CO, 1e9 gives ug/m^3, we need mg/m^3 for the subindex function
# 1 kg/m^3 = 1e6 mg/m^3
df['co'] = df['co'] / 1000.0 # From ug/m^3 to mg/m^3

# =========================================
df['time'] = pd.to_datetime(df['time'], dayfirst=True)
df['hour'] = df['time'].dt.hour
df['day'] = df['time'].dt.day
df['month'] = df['time'].dt.month
df['dayofweek'] = df['time'].dt.dayofweek

# Breakpoints and subindex (PM2.5: ug/m^3, CO: mg/m^3, others: ug/m^3)
def subindex(conc, breakpoints):
    if conc <= 0: return 0
    for Clow, Chigh, Ilow, Ihigh in breakpoints:
        if conc <= Chigh:
            return ((Ihigh - Ilow)/(Chigh - Clow)) * (conc - Clow) + Ilow
    return 500

pm25_bp = [(0,30,0,50),(30,60,50,100),(60,90,100,200),(90,120,200,300),(120,250,300,400),(250,500,400,500)]
pm10_bp = [(0,50,0,50),(50,100,50,100),(100,250,100,200),(250,350,200,300),(350,430,300,400),(430,600,400,500)]
no2_bp = [(0,40,0,50),(40,80,50,100),(80,180,100,200),(180,280,200,300),(280,400,300,400),(400,800,400,500)]
o3_bp = [(0,50,0,50),(50,100,50,100),(100,168,100,200),(168,208,200,300),(208,748,300,400),(748,1000,400,500)]
co_bp = [(0,1,0,50),(1,2,50,100),(2,10,100,200),(10,17,200,300),(17,34,300,400),(34,50,400,500)]
so2_bp = [(0,40,0,50),(40,80,50,100),(80,380,100,200),(380,800,200,300),(800,1600,300,400),(1600,2000,400,500)]

df['AQI_PM25'] = df['pm2p5'].apply(lambda x: subindex(x, pm25_bp))
df['AQI_PM10'] = df['pm10'].apply(lambda x: subindex(x, pm10_bp))
df['AQI_NO2'] = df['no2'].apply(lambda x: subindex(x, no2_bp))
df['AQI_O3'] = df['go3'].apply(lambda x: subindex(x, o3_bp))
df['AQI_CO'] = df['co'].apply(lambda x: subindex(x, co_bp))
df['AQI_SO2'] = df['so2'].apply(lambda x: subindex(x, so2_bp))
df['Final_AQI'] = df[['AQI_PM25','AQI_PM10','AQI_NO2','AQI_O3','AQI_CO','AQI_SO2']].max(axis=1)

# Drop time after engineering
train_df = df.drop(columns=['time'])
# =========================================
features = ['latitude','longitude','u10','v10','t2m','sst','tp','hour','day','month','dayofweek']
targets = ['pm2p5','pm10','co','no2','go3','so2']

train_df = train_df.fillna(train_df.mean())
X = train_df[features]
y = train_df[targets]

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training XGBoost MultiOutputRegressor model...")
xgb = XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, objective='reg:squarederror')
model = MultiOutputRegressor(xgb)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
score = r2_score(y_test, y_pred)
print("Model R2 Score:", score)

# Save model
print(f"Saving model to {MODEL_PATH}...")
joblib.dump({'model': model, 'features': features, 'targets': targets, 'r2_score': score}, MODEL_PATH)

# =========================================
print("Loading Kerala boundary...")
try:
    kerala_districts = gpd.read_file(BOUNDARY_FILE)
    kerala_boundary = kerala_districts.dissolve()
    kerala_geom = kerala_boundary.geometry.iloc[0]
except Exception as e:
    print(f"Error: {e}")
    kerala_geom = None

# Create DENSE Kerala grid points for smooth heatmap
lat_min, lat_max = 8.0, 12.8
lon_min, lon_max = 74.5, 77.5
grid_res = 0.02
lat_vals = np.arange(lat_min, lat_max, grid_res)
lon_vals = np.arange(lon_min, lon_max, grid_res)
grid_points = [(lat, lon) for lat in lat_vals for lon in lon_vals]
grid_df_full = pd.DataFrame(grid_points, columns=['latitude','longitude'])
grid_gdf = gpd.GeoDataFrame(grid_df_full, geometry=[Point(xy) for xy in zip(grid_df_full['longitude'], grid_df_full['latitude'])], crs="EPSG:4326")
if kerala_geom:
    grid_gdf = grid_gdf[grid_gdf.within(kerala_geom)]

# Predict for full grid
for col in ['u10','v10','t2m','sst','tp', 'hour','day','month','dayofweek']:
    grid_gdf[col] = train_df[col].mean()
grid_pred = model.predict(grid_gdf[features])
pred_df = pd.DataFrame(grid_pred, columns=targets).clip(lower=0)
pred_df['latitude'] = grid_gdf['latitude'].values
pred_df['longitude'] = grid_gdf['longitude'].values
pred_df['AQI_PM25'] = pred_df['pm2p5'].apply(lambda x: subindex(x, pm25_bp))
pred_df['AQI_PM10'] = pred_df['pm10'].apply(lambda x: subindex(x, pm10_bp))
pred_df['AQI_NO2'] = pred_df['no2'].apply(lambda x: subindex(x, no2_bp))
pred_df['AQI_O3'] = pred_df['go3'].apply(lambda x: subindex(x, o3_bp))
pred_df['AQI_CO'] = pred_df['co'].apply(lambda x: subindex(x, co_bp))
pred_df['AQI_SO2'] = pred_df['so2'].apply(lambda x: subindex(x, so2_bp))
pred_df['Final_AQI'] = pred_df[['AQI_PM25','AQI_PM10','AQI_NO2','AQI_O3','AQI_CO','AQI_SO2']].max(axis=1)

# =========================================
# =========================================
# CITY LABELS FOR ENHANCED VISUALS
MAJOR_CITIES = [
    {"name": "Trivandrum", "lat": 8.5241, "lon": 76.9366},
    {"name": "Quilon", "lat": 8.8932, "lon": 76.6141},
    {"name": "Kochi", "lat": 9.9312, "lon": 76.2673},
    {"name": "Thrissur", "lat": 10.5276, "lon": 76.2144},
    {"name": "Kozhikode", "lat": 11.2588, "lon": 75.7804},
    {"name": "Kannur", "lat": 11.8745, "lon": 75.3704},
    {"name": "Palakkad", "lat": 10.7867, "lon": 76.6547},
    {"name": "Malappuram", "lat": 11.0735, "lon": 76.0740},
    {"name": "Nilambur", "lat": 11.2775, "lon": 76.2272},
    {"name": "Kottayam", "lat": 9.5916, "lon": 76.5222},
    {"name": "Pathanamthitta", "lat": 9.2648, "lon": 76.7870}
]

# Standard AQI Colormap (Vibrant & Layered)
# We map the colors to the specific Indian Standard breakpoints
aqi_colors = ['#00E400', '#FFFF00', '#FF7E00', '#FF0000', '#8F3F97', '#7E0023']
aqi_levels = [0, 50, 100, 200, 300, 400, 500]
aqi_cmap = LinearSegmentedColormap.from_list("aqi_vibrant", aqi_colors)

def save_smooth_heatmap(point_lats, point_lons, point_aqi, path, title):
    plt.figure(figsize=(12, 14), facecolor='#0f172a')
    ax = plt.gca()
    ax.set_facecolor('#0f172a')
    
    # 1. Base Interpolation to dense grid
    zi = griddata((point_lons, point_lats), point_aqi, 
                  (grid_gdf['longitude'].values, grid_gdf['latitude'].values), method='linear')
    zi_nearest = griddata((point_lons, point_lats), point_aqi, 
                          (grid_gdf['longitude'].values, grid_gdf['latitude'].values), method='nearest')
    zi = np.where(np.isnan(zi), zi_nearest, zi)

    # 2. Create Clipping Path for Precisely the Kerala Boundary
    if kerala_geom:
        def geom_to_path(geom):
            if geom.geom_type == 'Polygon':
                return mpath.Path(np.array(geom.exterior.coords))
            elif geom.geom_type == 'MultiPolygon':
                paths = [mpath.Path(np.array(poly.exterior.coords)) for poly in geom.geoms]
                return mpath.Path.make_compound_path(*paths)
            return None

        kerala_path = geom_to_path(kerala_geom)
        patch = PathPatch(kerala_path, transform=ax.transData, facecolor='none', edgecolor='none')
        ax.add_patch(patch)
    else:
        patch = None

    # 3. Layered Heatmap Layer (Z-order 3)
    im = ax.tricontourf(grid_gdf['longitude'].values, grid_gdf['latitude'].values, zi, 
                        levels=aqi_levels, cmap=aqi_cmap, alpha=0.9, zorder=3, extend='both')
    
    if patch:
        im.set_clip_path(patch)

    # 4. Draw District Boundaries ON TOP (Z-order 5-6)
    if kerala_geom:
        kerala_districts.plot(ax=ax, color='none', edgecolor='#ffffff', alpha=0.3, linewidth=0.6, zorder=5)
        # Bolder state boundary
        kerala_boundary.plot(ax=ax, color='none', edgecolor='#ffffff', alpha=0.6, linewidth=1.2, zorder=6)

    # 5. City Labels with Predicted AQI (Z-order 10)
    city_aqis = griddata((grid_gdf['longitude'].values, grid_gdf['latitude'].values), zi,
                         ([c['lon'] for c in MAJOR_CITIES], [c['lat'] for c in MAJOR_CITIES]), method='nearest')
    
    import matplotlib.patheffects as PathEffects
    for city, val in zip(MAJOR_CITIES, city_aqis):
        txt = ax.text(city['lon'], city['lat'], f"{city['name']}\n{int(val)}", 
                     color='white', fontsize=9, fontweight='bold', ha='center', va='center',
                     zorder=10)
        txt.set_path_effects([PathEffects.withStroke(linewidth=3, foreground='black', alpha=0.7)])

    # 6. Legend and Aesthetics
    plt.title(title, color='white', fontsize=20, pad=30, fontweight='bold')
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, ticks=aqi_levels)
    cbar.set_label('Final AQI Index (Spatial Layered)', color='white', fontsize=12, labelpad=10)
    cbar.ax.yaxis.set_tick_params(colors='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    ax.tick_params(colors='#94a3b8', labelsize=9)
    for spine in ax.spines.values(): spine.set_visible(False)
    plt.xlabel('Longitude', color='#64748b', fontsize=11)
    plt.ylabel('Latitude', color='#64748b', fontsize=11)
    ax.set_xlim(74.5, 77.6)
    ax.set_ylim(8.0, 13.0)
    ax.grid(color='#334155', linestyle='--', alpha=0.2, zorder=0)
    
    plt.savefig(path, dpi=300, bbox_inches='tight', transparent=False)
    plt.close()

# Predictive check for sensor points
y_train_pred = model.predict(X_train)
# Calculate full AQI for sensor points properly
def get_full_aqi_from_pred(pred_rows):
    res = []
    for row in pred_rows:
        row = np.clip(row, 0, None)
        # CO adjustment
        co_mg = row[2] / 1000.0
        aqis = [
            subindex(row[0], pm25_bp),
            subindex(row[1], pm10_bp),
            subindex(co_mg, co_bp),
            subindex(row[3], no2_bp),
            subindex(row[4], o3_bp),
            subindex(row[5], so2_bp)
        ]
        res.append(max(aqis))
    return np.array(res)

train_aqi = get_full_aqi_from_pred(y_train_pred)
y_test_pred = model.predict(X_test)
test_aqi = get_full_aqi_from_pred(y_test_pred)

print("Generating Layered Boundary Heatmaps...")
save_smooth_heatmap(X_train['latitude'].values, X_train['longitude'].values, train_aqi, 
                    OUTPUT_IMG_ACTUAL, "Model Training: Spatial AQI Intensity")

print("Generating Layered Boundary Heatmaps...")
save_smooth_heatmap(X_test['latitude'].values, X_test['longitude'].values, test_aqi, 
                    OUTPUT_IMG_PRED, "Model Testing: Spatial AQI Generalization")

# Interactive Map Update
print("Generating Interactive Folium Map...")
m = folium.Map(location=[10.5, 76.5], zoom_start=7, tiles='cartodbpositron')
if kerala_geom:
    folium.GeoJson(kerala_districts, style_function=lambda x: {'fillColor': 'transparent', 'color': '#334155', 'weight': 1}).add_to(m)
# For web interactive, we use the smooth heatmap (folium HeatMap plugin is radial)
HeatMap([[float(r['latitude']), float(r['longitude']), float(r['Final_AQI'])/500.0] for _, r in pred_df.iterrows()], 
        radius=15, blur=10).add_to(m)
m.save(OUTPUT_MAP)

# Hourly Forecast
print("Calculating hourly forecast JSON...")
hourly_trends = []
for h in range(24):
    temp = grid_gdf.copy()
    temp['hour'] = h
    h_pred = model.predict(temp[features])
    aqis = get_full_aqi_from_pred(h_pred)
    hourly_trends.append(float(np.mean(aqis)))

with open(os.path.join(OUTPUT_DIR, 'aqi_hourly_forecast.json'), 'w') as f:
    json.dump({
        'hours': list(range(24)), 
        'aqi_values': [round(float(v), 2) for v in hourly_trends], 
        'model_r2': round(float(score), 4), 
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    }, f)

print("Done!")
sys.stdout = sys.__stdout__
with open(OUTPUT_LOG, 'w') as f: f.write(output_capture.getvalue())
print(output_capture.getvalue())
