import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class WebAQIFetcher:
    """
    Scrapes real-time air quality and weather data from reliable sources found via search.
    Focuses on aqi.in and aqicn.org which provide detailed pollutant breakdowns for Kochi.
    """
    def __init__(self):
        pass

    def fetch_current_details(self, city="Kochi"):
        # Sources for Kochi
        sources = [
            f"https://www.aqi.in/dashboard/india/kerala/{city.lower()}",
            f"https://aqicn.org/city/india/kerala/kochi/vytilla/"
        ]
        
        found_data = {
            'pollutants': {'pm25': None, 'pm10': None, 'no2': None, 'so2': None, 'co': None, 'o3': None},
            'weather': {'temp': None, 'humidity': None, 'wind': None}
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        for url in sources:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200: continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Strategy 1: Look in OG Description (Very reliable for aqi.in)
                og_desc = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
                if og_desc:
                    desc_text = og_desc.get('content', '')
                    self._parse_text(desc_text, found_data['pollutants'], found_data['weather'])
                
                # Strategy 2: Look for specific pollutant boxes in the HTML
                if not found_data['pollutants']['pm25'] or not found_data['weather']['temp']:
                    self._parse_html_boxes(soup, found_data['pollutants'], found_data['weather'])
                
                if found_data['pollutants']['pm25']:
                    break
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue

        return found_data

    def _parse_text(self, text, poll_dict, weather_dict):
        # Remove commas for easier parsing
        text = text.replace(',', '')
        
        # Pollutants
        # PM2.5 (113µg/m³), PM10 (128µg/m³) etc
        poll_patterns = {
            'pm25': r'PM2?\.5[^\d]{0,10}(\d+\.?\d*)',
            'pm10': r'PM10[^\d]{0,10}(\d+\.?\d*)',
            'no2': r'NO2[^\d]{0,10}(\d+\.?\d*)',
            'so2': r'SO2[^\d]{0,10}(\d+\.?\d*)',
            'co': r'CO[^\d]{0,10}(\d+\.?\d*)',
            'o3': r'O3[^\d]{0,10}(\d+\.?\d*)'
        }
        for k, v in poll_patterns.items():
            if poll_dict[k] is None:
                match = re.search(v, text, re.IGNORECASE)
                if match:
                    poll_dict[k] = float(match.group(1))

        # Weather
        weather_patterns = {
            'temp': r'Temperature[^\d]{0,10}(\d+\.?\d*)',
            'humidity': r'Humidity[^\d]{0,10}(\d+\.?\d*)',
            'wind': r'Wind[^\d]{0,10}(\d+\.?\d*)'
        }
        for k, v in weather_patterns.items():
            if weather_dict[k] is None:
                match = re.search(v, text, re.IGNORECASE)
                if match:
                    weather_dict[k] = float(match.group(1))

    def _parse_html_boxes(self, soup, poll_dict, weather_dict):
        # Specific selectors for aqi.in
        # Values are often in tags with classes like 'aqi-value' or similar
        all_text = soup.get_text(separator=' ')
        self._parse_text(all_text, poll_dict, weather_dict)

if __name__ == "__main__":
    fetcher = WebAQIFetcher()
    details = fetcher.fetch_current_details("Kochi")
    print(f"Extracted Details for Kochi:")
    print(f"  Pollutants: {details['pollutants']}")
    print(f"  Weather: {details['weather']}")
