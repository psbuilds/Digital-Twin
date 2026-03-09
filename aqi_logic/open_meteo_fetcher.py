import requests
import json
import time
from datetime import datetime

class OpenMeteoAQIFetcher:
    def __init__(self):
        self.aq_base_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        self.weather_base_url = "https://api.open-meteo.com/v1/forecast"
        
        self._cached_nodes = None
        self._last_fetch_time = 0
        self._cache_duration = 55 # 55 seconds

    def fetch_location_data(self, lat, lon):
        """
        Fetches air quality and weather data for a specific latitude and longitude using Open-Meteo.
        """
        # Try to use cached batch data first to save API calls
        all_nodes = self.fetch_all_nodes_data()
        for node in all_nodes:
            if abs(node['lat'] - lat) < 0.01 and abs(node['lon'] - lon) < 0.01:
                return {
                    'pollutants': node['pollutants'],
                    'metrics': node['metrics'],
                    'sync_time': node['sync_time'],
                    'raw_aq': {},
                    'raw_weather': {}
                }

        aq_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,dust,uv_index"
        }
        
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m"
        }
        
        try:
            # Fetch Air Quality
            aq_res = requests.get(self.aq_base_url, params=aq_params, timeout=10)
            aq_data = aq_res.json().get('current', {}) if aq_res.status_code == 200 else {}
            
            # Fetch Weather
            w_res = requests.get(self.weather_base_url, params=weather_params, timeout=10)
            w_data = w_res.json().get('current', {}) if w_res.status_code == 200 else {}
            
            # Open-Meteo CO is in ug/m3, Indian CPCB standards use mg/m3 for CO
            # 1000 ug/m3 = 1 mg/m3
            co_value = aq_data.get('carbon_monoxide')
            co_mg = co_value / 1000.0 if co_value is not None else None
            
            pollutants = {
                'pm25': aq_data.get('pm2_5'),
                'pm10': aq_data.get('pm10'),
                'no2': aq_data.get('nitrogen_dioxide'),
                'so2': aq_data.get('sulphur_dioxide'),
                'co': co_mg,
                'o3': aq_data.get('ozone')
            }
            
            return {
                'pollutants': pollutants,
                'metrics': {
                    'humidity': f"{w_data.get('relative_humidity_2m', 'N/A')}%",
                    'wind': f"{w_data.get('wind_speed_10m', 'N/A')} km/h",
                    'temp': f"{w_data.get('temperature_2m', 'N/A')}°C",
                    'uv_index': aq_data.get('uv_index'),
                    'dust': aq_data.get('dust')
                },
                'sync_time': aq_data.get('time', datetime.now().isoformat()),
                'raw_aq': aq_data,
                'raw_weather': w_data
            }
            
        except Exception as e:
            print(f"Exception during Open-Meteo fetch: {e}")
            return None

    def fetch_all_nodes_data(self):
        """
        Fetches air quality and weather data for all Kerala locations in batch.
        """
        current_time = time.time()
        if self._cached_nodes and (current_time - self._last_fetch_time < self._cache_duration):
            print("Returning cached Open-Meteo batch data...")
            return self._cached_nodes

        locations = self.get_kerala_locations()
        lats = ",".join([str(loc['lat']) for loc in locations])
        lons = ",".join([str(loc['lon']) for loc in locations])
        
        aq_params = {
            "latitude": lats,
            "longitude": lons,
            "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,dust,uv_index"
        }
        
        weather_params = {
            "latitude": lats,
            "longitude": lons,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m"
        }
        
        try:
            # Fetch All Air Quality
            print(f"Fetching batch AQ data for {len(locations)} locations...")
            aq_res = requests.get(self.aq_base_url, params=aq_params, timeout=10)
            if aq_res.status_code != 200:
                print(f"AQ Batch failed: {aq_res.text}")
                return []
            
            aq_results = aq_res.json()
            if not isinstance(aq_results, list): aq_results = [aq_results]
            
            # Fetch All Weather
            print(f"Fetching batch Weather data for {len(locations)} locations...")
            w_res = requests.get(self.weather_base_url, params=weather_params, timeout=10)
            w_results = w_res.json() if w_res.status_code == 200 else []
            if not isinstance(w_results, list): w_results = [w_results]
            
            final_nodes = []
            for i, loc in enumerate(locations):
                aq_data = aq_results[i].get('current', {}) if i < len(aq_results) else {}
                w_data = w_results[i].get('current', {}) if i < len(w_results) else {}
                
                if not aq_data: continue
                
                co_value = aq_data.get('carbon_monoxide')
                co_mg = co_value / 1000.0 if co_value is not None else None
                
                pollutants = {
                    'pm25': aq_data.get('pm2_5'),
                    'pm10': aq_data.get('pm10'),
                    'no2': aq_data.get('nitrogen_dioxide'),
                    'so2': aq_data.get('sulphur_dioxide'),
                    'co': co_mg,
                    'o3': aq_data.get('ozone')
                }
                
                final_nodes.append({
                    'name': loc['name'],
                    'lat': loc['lat'],
                    'lon': loc['lon'],
                    'pollutants': pollutants,
                    'metrics': {
                        'humidity': f"{w_data.get('relative_humidity_2m', 'N/A')}%",
                        'wind': f"{w_data.get('wind_speed_10m', 'N/A')} km/h",
                        'temp': f"{w_data.get('temperature_2m', 'N/A')}°C",
                        'uv_index': aq_data.get('uv_index'),
                        'dust': aq_data.get('dust')
                    },
                    'sync_time': aq_data.get('time', datetime.now().isoformat())
                })
            
            self._cached_nodes = final_nodes
            self._last_fetch_time = time.time()
            return final_nodes
            
        except Exception as e:
            print(f"Batch fetch error: {e}")
            return []

    def get_kerala_locations(self):
        """
        Returns a list of key locations in Kerala with their coordinates.
        Shared with Google fetcher for consistency.
        """
        return [
            {'name': 'Kochi (Vytilla)', 'lat': 9.9312, 'lon': 76.2673},
            {'name': 'Thiruvananthapuram', 'lat': 8.5241, 'lon': 76.9366},
            {'name': 'Kozhikode', 'lat': 11.2588, 'lon': 75.7804},
            {'name': 'Thrissur', 'lat': 10.5276, 'lon': 76.2144},
            {'name': 'Kollam', 'lat': 8.8932, 'lon': 76.6141},
            {'name': 'Palakkad', 'lat': 10.7867, 'lon': 76.6547},
            {'name': 'Alappuzha', 'lat': 9.4981, 'lon': 76.3388},
            {'name': 'Kottayam', 'lat': 9.5916, 'lon': 76.5222},
            {'name': 'Kannur', 'lat': 11.8745, 'lon': 75.3704},
            {'name': 'Malappuram', 'lat': 11.0735, 'lon': 76.0740},
            {'name': 'Eloor', 'lat': 10.0754, 'lon': 76.2995},
            {'name': 'Kakkanad', 'lat': 10.0159, 'lon': 76.3419}
        ]
