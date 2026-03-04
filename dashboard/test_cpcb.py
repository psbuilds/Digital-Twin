import requests
import json

def fetch_kerala_aqi():
    url = "https://aqinow.org/aqi_dashboard/api/get_aqi_all_stations"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Filter for Kerala stations
            kerala_stations = [s for s in data.get('stations', []) if s.get('state') == 'Kerala']
            return kerala_stations
        else:
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    stations = fetch_kerala_aqi()
    if stations:
        print(f"Found {len(stations)} stations in Kerala.")
        for s in stations[:5]:
            print(f"{s.get('city')} - {s.get('station_name')}: {s.get('aqi')}")
    else:
        print("Failed to fetch data.")
