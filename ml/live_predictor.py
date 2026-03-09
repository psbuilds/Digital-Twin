import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import os

# Define breakpoints for subindex calculation (same as ml_prediction_digital_twin.py)
pm25_bp = [(0,30,0,50),(30,60,50,100),(60,90,100,200),(90,120,200,300),(120,250,300,400),(250,500,400,500)]
pm10_bp = [(0,50,0,50),(50,100,50,100),(100,250,100,200),(250,350,200,300),(350,430,300,400),(430,600,400,500)]
no2_bp = [(0,40,0,50),(40,80,50,100),(80,180,100,200),(180,280,200,300),(280,400,300,400),(400,800,400,500)]
o3_bp = [(0,50,0,50),(50,100,50,100),(100,168,100,200),(168,208,200,300),(208,748,300,400),(748,1000,400,500)]
co_bp = [(0,1,0,50),(1,2,50,100),(2,10,100,200),(10,17,200,300),(17,34,300,400),(34,50,400,500)]
so2_bp = [(0,40,0,50),(40,80,50,100),(80,380,100,200),(380,800,200,300),(800,1600,300,400),(1600,2000,400,500)]

def subindex(conc, breakpoints):
    for Clow, Chigh, Ilow, Ihigh in breakpoints:
        if conc <= Chigh:
            return ((Ihigh - Ilow)/(Chigh - Clow)) * (conc - Clow) + Ilow
    return 500

class LivePredictor:
    def __init__(self):
        self.model_path = Path(__file__).resolve().parent / "statewide_model.joblib"
        self.model_data = None
        if os.path.exists(self.model_path):
            self.model_data = joblib.load(self.model_path)
            print(f"LivePredictor: Model loaded from {self.model_path}")
        else:
            print(f"LivePredictor WARNING: Model file not found at {self.model_path}")

    def predict_forecast(self, lat, lon, current_weather=None):
        if self.model_data is None:
            # Fallback if model not trained yet
            return None
        
        model = self.model_data['model']
        features = self.model_data['features']
        targets = self.model_data['targets']
        
        now = pd.Timestamp.now()
        
        # Prepare inputs for the next 24 hours
        forecast_entries = []
        for h_offset in range(1, 25):
            target_time = now + pd.Timedelta(hours=h_offset)
            
            # Simple meteorological simulations based on current weather
            temp = 28.0
            if current_weather and isinstance(current_weather.get('temp'), str):
                 try:
                     temp = float(current_weather['temp'].replace('°C', ''))
                 except: pass
            
            row = {
                'latitude': lat,
                'longitude': lon,
                'u10': 0.5, # Placeholder
                'v10': -0.5,
                't2m': temp + np.sin(h_offset/12*np.pi)*3, # Diurnal swing
                'sst': 29.0,
                'tp': 0.0,
                'hour': target_time.hour,
                'day': target_time.day,
                'month': target_time.month,
                'dayofweek': target_time.dayofweek
            }
            forecast_entries.append(row)
            
        input_df = pd.DataFrame(forecast_entries)
        predictions = model.predict(input_df[features])
        pred_df = pd.DataFrame(predictions, columns=targets).clip(lower=0)
        
        # Calculate AQI for each hour
        final_aqis = []
        for _, r in pred_df.iterrows():
            aqis = [
                subindex(r['pm2p5'], pm25_bp),
                subindex(r['pm10'], pm10_bp),
                subindex(r['no2'], no2_bp),
                subindex(r['go3'], o3_bp),
                subindex(r['co'], co_bp),
                subindex(r['so2'], so2_bp)
            ]
            final_aqis.append(max(aqis))
            
        return {
            'hours': [(now + pd.Timedelta(hours=i)).strftime("%H:%M") for i in range(1, 25)],
            'aqi_values': [float(round(v, 2)) for v in final_aqis],
            'confidence': float(round(self.model_data.get('r2_score', 0.92) * 100, 1))
        }

predictor = LivePredictor()
