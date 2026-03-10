from flask import Flask, render_template, jsonify, send_from_directory, request
import os
import requests
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Add project root to path to import aqi_logic and other modules
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "ml"))

import predict_future_aqi
import live_predictor
from aqi_logic.current_aqi_rules import calculate_overall_aqi
from aqi_logic.status_mapping import get_aqi_status
from aqi_logic.open_meteo_fetcher import OpenMeteoAQIFetcher

# Digital Twin Module Imports
from dt.models.twin_state import TwinState
from dt.engine.state_updater import update_state

app = Flask(__name__, static_folder='dist', static_url_path='/')


@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('vite.svg') # assuming vite default icon is generated in dist

open_meteo_fetcher = OpenMeteoAQIFetcher()

@app.route('/api/open-meteo-aqi')
def get_open_meteo_aqi():
    raw_nodes = open_meteo_fetcher.fetch_all_nodes_data()
    nodes = []
    
    print(f"Processing {len(raw_nodes)} nodes for frontend...")
    for node in raw_nodes:
        pollutants = node['pollutants']
        aqi = calculate_overall_aqi(pollutants)
        status_info = get_aqi_status(aqi)
        
        nodes.append({
            'id': node['name'].lower().replace(' ', '_').replace('(', '').replace(')', '').replace(',', ''),
            'name': node['name'],
            'lat': node['lat'],
            'lon': node['lon'],
            'aqi': aqi,
            'pollutants': pollutants,
            'status': status_info['category'],
            'color': status_info['color'],
            'description': status_info['description'],
            'metrics': node['metrics'],
            'reasoning': f"Live telemetry from Open-Meteo. Primary pollutant: {max(pollutants, key=lambda k: pollutants[k] if pollutants[k] is not None else -1).upper()}.",
            'sync_time': node['sync_time']
        })

    print(f"Successfully prepared {len(nodes)} nodes. Sending to client.")

    return jsonify({
        'source': 'Open-Meteo Air Quality API (Batch Mode)',
        'sync_time': datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        'nodes': nodes
    })

@app.route('/api/live-aqi')
def get_live_aqi():
    # Repurposed to use Open-Meteo as the only live data source
    return get_open_meteo_aqi()

@app.route('/api/predictions')
def get_predictions():
    pollutant = request.args.get('pollutant', 'pm2p5')
    try:
        preds = predict_future_aqi.predict_horizons(pollutant)
        return jsonify(preds)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/heatmap')
def get_heatmap():
    pollutant = request.args.get('pollutant', 'pm2p5')
    horizon = int(request.args.get('horizon', 24))
    try:
        heatmap_data = predict_future_aqi.generate_district_forecasts(pollutant, horizon)
        return jsonify(heatmap_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live-prediction')
def get_live_prediction():
    try:
        lat = float(request.args.get('lat', 9.9312))
        lon = float(request.args.get('lon', 76.2673))
        # Use location data for meteorology context
        weather_data = open_meteo_fetcher.fetch_location_data(lat, lon)
        metrics = weather_data.get('metrics') if weather_data else None
        
        forecast = live_predictor.predictor.predict_forecast(lat, lon, metrics)
        if forecast:
            return jsonify(forecast)
        return jsonify({'error': 'Model not available'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dt-insights')
def get_dt_insights():
    try:
        lat = float(request.args.get('lat', 9.9312))
        lon = float(request.args.get('lon', 76.2673))
        
        # Get baseline from Open-Meteo
        live_data = open_meteo_fetcher.fetch_location_data(lat, lon)
        forecast_data = open_meteo_fetcher.fetch_hourly_forecast(lat, lon)
        
        if not live_data:
            return jsonify({'error': 'Source data unavailable'}), 503
            
        p = live_data['pollutants']
        m = live_data['metrics']
        
        # Initialize TwinState
        # Convert km/h to m/s for DT engine: 1 km/h = 1/3.6 m/s
        base_wind_kmh = float(m['wind'].split()[0]) if 'N/A' not in m['wind'] else 5.4 
        base_wind_ms = base_wind_kmh / 3.6
        
        state = TwinState(
            grid_id=f"node_{lat}_{lon}",
            timestamp=datetime.now(),
            latitude=lat,
            longitude=lon,
            wind_speed=base_wind_ms,
            wind_direction=270.0, # Defaulting if unknown
            temperature=float(m['temp'].replace('°C','')) if 'N/A' not in m['temp'] else 29.0,
            precipitation=float(m.get('precip', 0.0)),
            pm25=p['pm25'] or 30.0,
            pm10=p['pm10'] or 50.0,
            no2=p['no2'] or 20.0,
            o3=p['o3'] or 30.0,
            so2=p['so2'] or 5.0,
            co=p['co'] or 0.5,
            is_coastal=True
        )
        
        # Run 24h simulation using forecast data
        history = []
        current_state = state
        
        # We simulate 24 hours. The forecast usually starts from actual hour.
        for i in range(24):
            weather_input = None
            if forecast_data and i < len(forecast_data):
                f = forecast_data[i]
                weather_input = {
                    'temp': f['temp'],
                    'wind_speed': f['wind_speed'] / 3.6, # Convert to m/s
                    'wind_direction': f['wind_direction'],
                    'precip': f['precip']
                }
            
            current_state, report = update_state(current_state, weather_input=weather_input)
            
            history.append({
                'time': current_state.timestamp.strftime("%H:%M"),
                'aqi': report['aqi'],
                'dominant': report['dominant_pollutant'],
                'reasons': report.get('rule_reasons', {}),
                'effects': report.get('rule_effects', {}),
                'meteo': {
                    'temp': current_state.temperature,
                    'wind': current_state.wind_speed,
                    'precip': current_state.precipitation
                }
            })
            
        return jsonify({
            'history': history,
            'initial_state': {
                'aqi': calculate_overall_aqi(p),
                'metrics': m
            }
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml-results')
def get_ml_results():
    try:
        log_path = os.path.join(PROJECT_ROOT, 'dashboard/static/images/ml_output.txt')
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                content = f.read()
            return jsonify({'output': content})
        return jsonify({'output': 'No output log found.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/images/<path:filename>')
def serve_static_images(filename):
    return send_from_directory(os.path.join(PROJECT_ROOT, 'dashboard/static/images'), filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
