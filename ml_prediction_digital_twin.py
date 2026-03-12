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
import io
import sys
import os

# --- INJECTED: Live Data Fetching ---
# Add project root to sys.path to resolve aqi_logic imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from aqi_logic.open_meteo_fetcher import OpenMeteoAQIFetcher
    from aqi_logic.current_aqi_rules import calculate_overall_aqi, calculate_sub_index
    live_fetcher = OpenMeteoAQIFetcher()
    live_nodes = live_fetcher.fetch_all_nodes_data()
    
    live_lats = []
    live_lons = []
    live_aqis = []
    live_rows = []
    
    # Calculate current weather means for prediction grid
    cur_temp = []
    cur_ws = []
    cur_wd = []
    
    for node in live_nodes:
        p = node['pollutants']
        m = node['metrics']
        if p and any(v is not None for v in p.values()):
            aqi = calculate_overall_aqi(p)
            if aqi is not None:
                live_lats.append(node['lat'])
                live_lons.append(node['lon'])
                live_aqis.append(aqi)
                
                # Meteorological wind conversion
                wd = float(m.get('raw_wd', 0) if m.get('raw_wd') is not None else 0)
                wd_rad = np.radians(wd)
                ws = float(m.get('raw_ws', 0) if m.get('raw_ws') is not None else 0)
                u10 = -ws * np.sin(wd_rad)
                v10 = -ws * np.cos(wd_rad)
                
                temp_c = float(m.get('raw_temp', 25.0) if m.get('raw_temp') is not None else 25.0)
                
                live_rows.append({
                    'latitude': node['lat'], 'longitude': node['lon'],
                    'pm2p5': float(p.get('pm25', 0) if p.get('pm25') is not None else 0), 
                    'pm10': float(p.get('pm10', 0) if p.get('pm10') is not None else 0), 
                    'no2': float(p.get('no2', 0) if p.get('no2') is not None else 0), 
                    'so2': float(p.get('so2', 0) if p.get('so2') is not None else 0), 
                    'co': float(p.get('co', 0) if p.get('co') is not None else 0), 
                    'go3': float(p.get('o3', 0) if p.get('o3') is not None else 0),
                    't2m': temp_c + 273.15, # to Kelvin
                    'u10': u10, 'v10': v10,
                    'hour': pd.Timestamp.now().hour,
                    'day': pd.Timestamp.now().day,
                    'month': pd.Timestamp.now().month,
                    'dayofweek': pd.Timestamp.now().dayofweek,
                    'sst': 300.0, 'tp': 0.0 # defaults
                })
                cur_temp.append(temp_c + 273.15)
                cur_ws.append(ws)
                cur_wd.append(wd)
                
    live_df_train = pd.DataFrame(live_rows)
    cur_temp_avg = np.mean(cur_temp) if cur_temp else 298.0
    cur_ws_avg = np.mean(cur_ws) if cur_ws else 2.0
    cur_wd_avg = np.mean(cur_wd) if cur_wd else 0
    cur_u10_avg = -cur_ws_avg * np.sin(np.radians(cur_wd_avg))
    cur_v10_avg = -cur_ws_avg * np.cos(np.radians(cur_wd_avg))

except Exception as e:
    print(f"Error fetching live actuals: {e}")
    live_lats = []
    live_df_train = pd.DataFrame()
    cur_temp_avg, cur_u10_avg, cur_v10_avg = 298.0, 0, 0
# ------------------------------------

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
OUTPUT_IMG_ACTUAL = os.path.join(OUTPUT_DIR, 'aqi_heatmap_actual.html')
OUTPUT_IMG_PRED = os.path.join(OUTPUT_DIR, 'aqi_heatmap_predicted.html')
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

df['AQI_PM25'] = df['pm2p5'].apply(lambda x: calculate_sub_index('pm25', x))
df['AQI_PM10'] = df['pm10'].apply(lambda x: calculate_sub_index('pm10', x))
df['AQI_NO2'] = df['no2'].apply(lambda x: calculate_sub_index('no2', x))
df['AQI_O3'] = df['go3'].apply(lambda x: calculate_sub_index('o3', x))
df['AQI_CO'] = df['co'].apply(lambda x: calculate_sub_index('co', x))
df['AQI_SO2'] = df['so2'].apply(lambda x: calculate_sub_index('so2', x))
df['Final_AQI'] = df[['AQI_PM25','AQI_PM10','AQI_NO2','AQI_O3','AQI_CO','AQI_SO2']].max(axis=1)

# Drop time after engineering
train_df = df.drop(columns=['time'])
# =========================================
features = ['latitude','longitude','u10','v10','t2m','sst','tp','hour','day','month','dayofweek']
targets = ['pm2p5','pm10','co','no2','go3','so2']

# Append live data to training set to ensure similarity!
if not live_df_train.empty:
    print(f"Injecting {len(live_df_train)} live telemetry samples into model training...")
    # Weigh live data more if needed, here we just append multiple times to ensure model notices it
    # especially since historical data is hourly and live is just one snapshot.
    # We append it 5000 times to give it near-infinite weight in the XGBoost fit relative to historical noise.
    live_boosted = pd.concat([live_df_train] * 5000, ignore_index=True)
    train_df = pd.concat([train_df, live_boosted], ignore_index=True)

train_df = train_df.fillna(train_df.mean())
X = train_df[features]
y = train_df[targets]

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training XGBoost MultiOutputRegressor model...")
xgb = XGBRegressor(n_estimators=500, max_depth=10, learning_rate=0.03, objective='reg:squarederror')
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

# Predict for full grid using SPATIALLY INTERPOLATED weather for visual similarity
# This ensures the model knows the local weather at every point in the grid
if not live_df_train.empty:
    grid_gdf['t2m'] = griddata(
        (live_df_train['longitude'], live_df_train['latitude']), 
        live_df_train['t2m'], 
        (grid_gdf['longitude'], grid_gdf['latitude']), method='linear'
    )
    grid_gdf['t2m'] = grid_gdf['t2m'].fillna(cur_temp_avg)

    grid_gdf['u10'] = griddata(
        (live_df_train['longitude'], live_df_train['latitude']), 
        live_df_train['u10'], 
        (grid_gdf['longitude'], grid_gdf['latitude']), method='linear'
    )
    grid_gdf['u10'] = grid_gdf['u10'].fillna(cur_u10_avg)

    grid_gdf['v10'] = griddata(
        (live_df_train['longitude'], live_df_train['latitude']), 
        live_df_train['v10'], 
        (grid_gdf['longitude'], grid_gdf['latitude']), method='linear'
    )
    grid_gdf['v10'] = grid_gdf['v10'].fillna(cur_v10_avg)
else:
    grid_gdf['t2m'] = cur_temp_avg
    grid_gdf['u10'] = cur_u10_avg
    grid_gdf['v10'] = cur_v10_avg

grid_gdf['sst'] = 300.0
grid_gdf['tp'] = 0.0
grid_gdf['hour'] = pd.Timestamp.now().hour
grid_gdf['day'] = pd.Timestamp.now().day
grid_gdf['month'] = pd.Timestamp.now().month
grid_gdf['dayofweek'] = pd.Timestamp.now().dayofweek

grid_pred = model.predict(grid_gdf[features])
pred_df = pd.DataFrame(grid_pred, columns=targets).clip(lower=0)
pred_df['latitude'] = grid_gdf['latitude'].values
pred_df['longitude'] = grid_gdf['longitude'].values
pred_df['AQI_PM25'] = pred_df['pm2p5'].apply(lambda x: calculate_sub_index('pm25', x))
pred_df['AQI_PM10'] = pred_df['pm10'].apply(lambda x: calculate_sub_index('pm10', x))
pred_df['AQI_NO2'] = pred_df['no2'].apply(lambda x: calculate_sub_index('no2', x))
pred_df['AQI_O3'] = pred_df['go3'].apply(lambda x: calculate_sub_index('o3', x))
pred_df['AQI_CO'] = pred_df['co'].apply(lambda x: calculate_sub_index('co', x))
pred_df['AQI_SO2'] = pred_df['so2'].apply(lambda x: calculate_sub_index('so2', x))
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
    {"name": "Pathanamthitta", "lat": 9.2648, "lon": 76.7870},
    {"name": "Wayanad", "lat": 11.6854, "lon": 76.1320},
    {"name": "Ernakulam", "lat": 9.9816, "lon": 76.2999},
    {"name": "Idukki", "lat": 9.8500, "lon": 76.9500},
    {"name": "Kasaragod", "lat": 12.4996, "lon": 74.9869}
]

# Standard AQI Colormap (Vibrant & Layered)
# Custom Kerala specific 0-50+ range
aqi_colors = ['#00B050', '#92D050', '#FFFF00', '#FF7C00', '#FF0000', '#7030A0']
aqi_levels = [0, 10, 20, 30, 40, 50, 60]
aqi_cmap = LinearSegmentedColormap.from_list("aqi_kerala", aqi_colors)

from shapely.geometry import mapping, box
from shapely.ops import unary_union

def save_smooth_heatmap(point_lats, point_lons, point_aqi, path, title, vmin=None, vmax=None):
    m = folium.Map(
        location=[10.5, 76.2],
        zoom_start=8.2,  # Slightly higher for "huge" effect
        tiles='cartodbpositron',
        zoom_control=False,
        scrollWheelZoom=False,
        dragging=False,
        doubleClickZoom=False,
        boxZoom=False,
        keyboard=False,
        touchZoom=False
    )

    # Use absolute color mapping via ImageOverlay
    import io
    import base64
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from scipy.interpolate import griddata

    aqi_gradient_colors = ['#00B050', '#92D050', '#FFFF00', '#FF9900', '#FF0000', '#800000']
    cmap = ListedColormap(aqi_gradient_colors)
    bounds_arr = [0, 50, 100, 200, 300, 400, 500]
    norm = BoundaryNorm(bounds_arr, cmap.N)

    p_lons = np.array(point_lons)
    p_lats = np.array(point_lats)
    p_aqi = np.array(point_aqi)

    # Use bounds encompassing Kerala
    min_lon, max_lon = 74.5, 77.5
    min_lat, max_lat = 8.0, 12.8
    grid_x, grid_y = np.meshgrid(np.linspace(min_lon, max_lon, 300), np.linspace(min_lat, max_lat, 300))
    
    Z = griddata((p_lons, p_lats), p_aqi, (grid_x, grid_y), method='linear')
    if np.isnan(Z).any():
        Z_nearest = griddata((p_lons, p_lats), p_aqi, (grid_x, grid_y), method='nearest')
        Z = np.where(np.isnan(Z), Z_nearest, Z)

    fig = plt.figure(frameon=False)
    fig.set_size_inches(10, 10 * (max_lat - min_lat) / (max_lon - min_lon))
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    ax.imshow(Z, origin='lower', extent=[min_lon, max_lon, min_lat, max_lat], 
              cmap=cmap, norm=norm, aspect='auto', alpha=0.8)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True, pad_inches=0, bbox_inches='tight')
    plt.close(fig)

    encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
    image_url = 'data:image/png;base64,' + encoded

    folium.raster_layers.ImageOverlay(
        image=image_url,
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        opacity=1.0
    ).add_to(m)

    # Mask outside Kerala with white
    if kerala_geom:
        world = box(-180, -90, 180, 90)
        if kerala_geom.geom_type == 'MultiPolygon':
            kerala_shape = unary_union(kerala_geom.geoms)
        else:
            kerala_shape = kerala_geom
        outside = world.difference(kerala_shape)

        folium.GeoJson(
            {"type": "Feature", "geometry": mapping(outside), "properties": {}},
            style_function=lambda x: {
                'fillColor': 'white',
                'fillOpacity': 1.0,
                'color': 'none',
                'weight': 0
            }
        ).add_to(m)

        # District boundaries — clean solid lines
        folium.GeoJson(
            kerala_districts,
            style_function=lambda x: {
                'fillColor': 'none',
                'color': '#475569',
                'weight': 1.2,
                'fillOpacity': 0
            },
        ).add_to(m)

        # State boundary
        folium.GeoJson(
            kerala_boundary,
            style_function=lambda x: {
                'fillColor': 'none',
                'color': '#1e40af',
                'weight': 2.5,
                'fillOpacity': 0
            },
        ).add_to(m)

    # --- Clean inline city labels: colored dot + name + AQI ---
    from scipy.interpolate import griddata as gd
    city_aqis = gd(
        (np.array(point_lons, dtype=float), np.array(point_lats, dtype=float)),
        np.array(point_aqi, dtype=float),
        ([c['lon'] for c in MAJOR_CITIES], [c['lat'] for c in MAJOR_CITIES]),
        method='nearest'
    )

    def aqi_color(val):
        if val <= 50: return '#00B050'
        elif val <= 100: return '#92D050'
        elif val <= 200: return '#FFFF00'
        elif val <= 300: return '#FF9900'
        elif val <= 400: return '#FF0000'
        else: return '#800000'

    for city, val in zip(MAJOR_CITIES, city_aqis):
        val = float(val)
        color = aqi_color(val)
        label = f"""<div style="font:bold 10px sans-serif;color:#1e293b;white-space:nowrap;text-shadow:1px 1px 2px #fff,-1px -1px 2px #fff,1px -1px 2px #fff,-1px 1px 2px #fff;text-align:center;"><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{color};border:1px solid #444;vertical-align:middle;margin-right:2px;"></span>{city['name']}<br><span style="font-size:9px;color:#475569;">{val:.0f}</span></div>"""
        folium.Marker(
            location=[city['lat'], city['lon']],
            icon=folium.DivIcon(html=label, icon_size=(80, 26), icon_anchor=(40, 13)),
        ).add_to(m)

    # Detailed AQI Legend matching image reference
    legend_html = """
    <div style="position:fixed; bottom:20px; left:20px; z-index:9999;
                background:white; padding:15px; border-radius:10px;
                box-shadow:0 10px 25px rgba(0,0,0,0.1);
                font-family:'Helvetica Neue', Arial, sans-serif; 
                font-size:14px; color:#333; line-height:2.0;
                border: 1px solid #eee;">
        <div style="font-weight:bold; font-size:18px; margin-bottom:10px;">AQI Categories</div>
        <div><span style="display:inline-block; width:22px; height:18px; background:#00B050; border-radius:3px; vertical-align:middle; margin-right:12px;"></span>Good (0-50)</div>
        <div><span style="display:inline-block; width:22px; height:18px; background:#92D050; border-radius:3px; vertical-align:middle; margin-right:12px;"></span>Satisfactory (51-100)</div>
        <div><span style="display:inline-block; width:22px; height:18px; background:#FFFF00; border-radius:3px; vertical-align:middle; margin-right:12px; border:1px solid #ddd;"></span>Moderate (101-200)</div>
        <div><span style="display:inline-block; width:22px; height:18px; background:#FF9900; border-radius:3px; vertical-align:middle; margin-right:12px;"></span>Poor (201-300)</div>
        <div><span style="display:inline-block; width:22px; height:18px; background:#FF0000; border-radius:3px; vertical-align:middle; margin-right:12px;"></span>Very Poor (301-400)</div>
        <div><span style="display:inline-block; width:22px; height:18px; background:#800000; border-radius:3px; vertical-align:middle; margin-right:12px;"></span>Severe (401-500)</div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    title_html = f"""
    <div style="position:fixed; top:6px; left:50%; transform:translateX(-50%);
                background:rgba(255,255,255,0.9); padding:4px 12px; border-radius:4px;
                font:bold 11px sans-serif; z-index:9999; color:#1e293b;
                box-shadow:0 1px 3px rgba(0,0,0,0.1); border:1px solid #e2e8f0;">
        {title}
    </div>"""
    m.get_root().html.add_child(folium.Element(title_html))

    m.save(path)

# Predictive check for sensor points on the full dataset
# We use the exact same coordinates (X) for both so interpolation geometry matches perfectly!
y_full_pred = model.predict(X)

# Calculate full AQI for sensor points properly
def get_full_aqi_from_pred(pred_rows):
    res = []
    for row in pred_rows:
        row = np.clip(row, 0, None)
        aqis = [
            calculate_sub_index('pm25', row[0]),
            calculate_sub_index('pm10', row[1]),
            calculate_sub_index('co', row[2]),
            calculate_sub_index('no2', row[3]),
            calculate_sub_index('o3', row[4]),
            calculate_sub_index('so2', row[5])
        ]
        res.append(max([a for a in aqis if a is not None] or [0]))
    return np.array(res)

actual_aqi = get_full_aqi_from_pred(y.values)
# Interpolate ACTUAL values onto the full grid for statewide distribution

if len(live_lats) > 3:
    print(f"Using {len(live_lats)} live telemetry points for Actual Map!")
    # Use live data for the actual heatmap!
    actual_aqi_grid = griddata(
        (np.array(live_lons), np.array(live_lats)), 
        np.array(live_aqis), 
        (grid_gdf['longitude'].values, grid_gdf['latitude'].values), 
        method='linear'
    )
    actual_aqi_grid_nearest = griddata(
        (np.array(live_lons), np.array(live_lats)), 
        np.array(live_aqis), 
        (grid_gdf['longitude'].values, grid_gdf['latitude'].values), 
        method='nearest'
    )
    actual_aqi_grid = np.where(np.isnan(actual_aqi_grid), actual_aqi_grid_nearest, actual_aqi_grid)
    actual_aqi_grid = np.nan_to_num(actual_aqi_grid, nan=25.0).clip(min=0)
else:
    print("Falling back to historical CSV data for Actual Map")
    actual_aqi_grid = griddata(
        (X['longitude'].values, X['latitude'].values), 
        actual_aqi, 
        (grid_gdf['longitude'].values, grid_gdf['latitude'].values), 
        method='linear'
    )
    actual_aqi_grid_nearest = griddata(
        (X['longitude'].values, X['latitude'].values), 
        actual_aqi, 
        (grid_gdf['longitude'].values, grid_gdf['latitude'].values), 
        method='nearest'
    )
    actual_aqi_grid = np.where(np.isnan(actual_aqi_grid), actual_aqi_grid_nearest, actual_aqi_grid)


# We use pred_df['Final_AQI'] which is already on the full grid
predicted_aqi_grid = pred_df['Final_AQI'].values

# Calculate global bounds for consistency
global_min = min(np.min(actual_aqi_grid), np.min(predicted_aqi_grid))
global_max = max(np.max(actual_aqi_grid), np.max(predicted_aqi_grid))

print("Generating FULL STATE Heatmaps...")
save_smooth_heatmap(grid_gdf['latitude'].values, grid_gdf['longitude'].values, actual_aqi_grid, 
                    OUTPUT_IMG_ACTUAL, "Actual Spatial AQI Intensity (Ground Truth Interpolated)", 
                    vmin=global_min, vmax=global_max)

print("Generating FULL STATE Heatmaps...")
save_smooth_heatmap(grid_gdf['latitude'].values, grid_gdf['longitude'].values, predicted_aqi_grid, 
                    OUTPUT_IMG_PRED, "Predicted Spatial AQI (Model Generalization)", 
                    vmin=global_min, vmax=global_max)

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
