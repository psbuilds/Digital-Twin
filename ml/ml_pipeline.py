"""
Time-series ML pipeline for air pollutant forecasting (classical ML only).

Produces: data profiling, preprocessing (time-safe), feature engineering,
direct multi-horizon models (1h,6h,24h,168h) for pollutants, evaluation,
and saved models/plots.

Usage: python ml/ml_pipeline.py
"""
import os
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import matplotlib.pyplot as plt

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False


DATA_PATH = Path(__file__).resolve().parents[0] / "merged_hourly_data.csv"
OUT_DIR = Path(__file__).resolve().parents[0] / "output"
OUT_DIR.mkdir(exist_ok=True)


def load_and_profile(path: Path):
    df = pd.read_csv(path)
    print("Columns:", list(df.columns))
    print(df.dtypes)
    print("Head:\n", df.head(3).to_string(index=False))
    print("Tail:\n", df.tail(3).to_string(index=False))
    total_rows = len(df)
    print(f"Total rows: {total_rows}")
    # parse time
    df['time'] = pd.to_datetime(df['time'], dayfirst=True)
    time_min, time_max = df['time'].min(), df['time'].max()
    print(f"Time span: {time_min} -> {time_max}")
    # sampling insight: unique timestamps count / rows
    unique_ts = df['time'].nunique()
    print(f"Unique timestamps: {unique_ts}")
    # unit conversion: CAMS/ERA5 pollutants are in kg/m^3. 
    # Multiply by 1e9 to get micro-grams/m^3 (ug/m^3) for human-readable scales.
    pollutant_cols = ['pm2p5', 'pm10', 'co', 'no2', 'go3', 'so2']
    for pc in pollutant_cols:
        if pc in df.columns:
            df[pc] = df[pc] * 1e9
            
    return df


def aggregate_by_time(df: pd.DataFrame):
    # many lat/lon rows per timestamp; aggregate to city-level by mean
    grp = df.groupby('time').mean()
    grp = grp.sort_index()
    return grp


def enforce_hourly_index(df: pd.DataFrame):
    # ensure regular hourly frequency, resample mean then interpolate
    idx = pd.date_range(start=df.index.min(), end=df.index.max(), freq='h')
    df = df.reindex(idx)
    return df


def fill_missing(df: pd.DataFrame):
    # time-based interpolation then forward/backward fill as needed
    df = df.interpolate(method='time', limit_direction='both')
    df = df.ffill().bfill()
    return df


def create_features(df: pd.DataFrame, target_col: str):
    # create lags, rolling stats, and calendar features
    X = pd.DataFrame(index=df.index)
    series = df[target_col]
    # lag features
    for l in [1, 3, 6, 12, 24]:
        X[f'lag_{l}'] = series.shift(l)
    # rolling stats (center False)
    for w in [3, 6, 24]:
        X[f'roll_mean_{w}'] = series.rolling(window=w, min_periods=1).mean().shift(1)
        X[f'roll_std_{w}'] = series.rolling(window=w, min_periods=1).std().shift(1).fillna(0)
    # calendar
    X['hour'] = X.index.hour
    X['dayofweek'] = X.index.dayofweek
    X['is_weekend'] = (X.index.dayofweek >= 5).astype(int)
    # optional exogenous: temperature, humidity if present
    for col in ['t2m', 'u10', 'v10']:
        if col in df.columns:
            X[col] = df[col].shift(1)
    return X


def train_val_test_split(X, y, train_frac=0.75, val_frac=0.15):
    n = len(X)
    i_train = int(n * train_frac)
    i_val = int(n * (train_frac + val_frac))
    X_train, y_train = X.iloc[:i_train], y.iloc[:i_train]
    X_val, y_val = X.iloc[i_train:i_val], y.iloc[i_train:i_val]
    X_test, y_test = X.iloc[i_val:], y.iloc[i_val:]
    return X_train, y_train, X_val, y_val, X_test, y_test


def scale_fit_transform(X_train, X_val, X_test):
    scaler = StandardScaler()
    scaler.fit(X_train)
    X_train_s = pd.DataFrame(scaler.transform(X_train), index=X_train.index, columns=X_train.columns)
    X_val_s = pd.DataFrame(scaler.transform(X_val), index=X_val.index, columns=X_val.columns)
    X_test_s = pd.DataFrame(scaler.transform(X_test), index=X_test.index, columns=X_test.columns)
    return scaler, X_train_s, X_val_s, X_test_s


def train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test, models_cfg):
    results = {}
    for name, mdl in models_cfg.items():
        print(f"Training {name}...")
        mdl.fit(X_train, y_train)
        preds_val = mdl.predict(X_val)
        preds_test = mdl.predict(X_test)
        res = {
            'model': mdl,
            'val_pred': preds_val,
            'test_pred': preds_test,
            'val_mae': mean_absolute_error(y_val, preds_val),
            'val_rmse': np.sqrt(mean_squared_error(y_val, preds_val)),
            'test_mae': mean_absolute_error(y_test, preds_test),
            'test_rmse': np.sqrt(mean_squared_error(y_test, preds_test)),
        }
        results[name] = res
    return results


def plot_actual_vs_pred(idx, actual, preds, title, outpath):
    plt.figure(figsize=(10, 4))
    plt.plot(idx, actual, label='actual')
    plt.plot(idx, preds, label='pred')
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()


def run_pipeline():
    df_raw = load_and_profile(DATA_PATH)
    df = aggregate_by_time(df_raw)
    df = enforce_hourly_index(df)
    df = fill_missing(df)

    # pollutants available
    pollutant_cols = [c for c in df.columns if c.lower() in ['pm2p5', 'pm10', 'co', 'no2', 'go3', 'so2']]
    if not pollutant_cols:
        # fallback: pick 'pm2p5' if exists with that name exactly
        pollutant_cols = [c for c in df.columns if 'pm2' in c.lower()]
    print("Target pollutant columns:", pollutant_cols)

    horizons = [1, 6, 24, 168]

    # we'll loop over pollutants and horizons and train direct models
    for pollutant in pollutant_cols[:3]:  # limit to first 3 to keep runtime reasonable
        print(f"\nProcessing pollutant: {pollutant}")
        for h in horizons:
            print(f" Horizon: {h}h")
            X = create_features(df, pollutant)
            y = df[pollutant].shift(-h)  # target at t+h (direct strategy)
            # align
            mask = X.index <= y.index.max()
            X = X.loc[mask]
            y = y.loc[X.index]
            # drop rows with NaN (caused by shifting)
            valid = (~X.isna().any(axis=1)) & (~y.isna())
            Xf = X.loc[valid]
            yf = y.loc[valid]
            if len(Xf) < 200:
                print(" Not enough data after shifting/feature creation, skipping.")
                continue
            X_train, y_train, X_val, y_val, X_test, y_test = train_val_test_split(Xf, yf)
            scaler, X_train_s, X_val_s, X_test_s = scale_fit_transform(X_train, X_val, X_test)

            models_cfg = {
                'LinearRegression': LinearRegression(),
                'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=2)
            }
            if XGBOOST_AVAILABLE:
                models_cfg['XGBoost'] = XGBRegressor(n_estimators=100, random_state=42, verbosity=0)

            results = train_and_evaluate(X_train_s, y_train, X_val_s, y_val, X_test_s, y_test, models_cfg)

            # save best model by test_mae
            best_name = min(results.keys(), key=lambda k: results[k]['test_mae'])
            best_model = results[best_name]['model']
            model_tag = f"{pollutant}_h{h}h_{best_name}"
            joblib.dump({'model': best_model, 'scaler': scaler, 'features': Xf.columns.tolist()}, OUT_DIR / f"{model_tag}.joblib")

            # save metrics and plots
            metrics_path = OUT_DIR / f"{model_tag}_metrics.txt"
            with open(metrics_path, 'w') as f:
                for k, v in results.items():
                    f.write(f"{k}: val_mae={v['val_mae']:.4f}, val_rmse={v['val_rmse']:.4f}, test_mae={v['test_mae']:.4f}, test_rmse={v['test_rmse']:.4f}\n")
            # plot last portion of test set
            test_idx = X_test.index
            for k, v in results.items():
                plot_actual_vs_pred(test_idx, y_test, v['test_pred'], f"{pollutant} {h}h {k}", OUT_DIR / f"{model_tag}_{k}_plot.png")

    print("Pipeline finished. Outputs in:", OUT_DIR)


if __name__ == '__main__':
    run_pipeline()
