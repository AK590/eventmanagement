# ml_pricing.py
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
import os

MODEL_PATH = os.getenv("MODEL_PATH", "pricing_model.joblib")

def generate_synthetic_data(n=2000):
    rng = np.random.RandomState(42)
    tickets_booked = rng.randint(0, 300, size=n)
    hours_to_event = rng.exponential(scale=48, size=n)
    base_price = rng.uniform(20, 300, size=n)

    demand_factor = (tickets_booked / 300) * (base_price * 0.4)
    time_urgency = np.exp(-hours_to_event / 48) * (base_price * 0.1)
    
    price = base_price + demand_factor + time_urgency
    
    noise = rng.normal(0, 10, size=n)
    price += noise
    price = np.maximum(price, base_price * 0.9)
    
    return pd.DataFrame({
        "tickets_booked": tickets_booked,
        "hours_to_event": hours_to_event,
        "base_price": base_price,
        "price": price
    })

def train_and_save_model(path=MODEL_PATH):
    df = generate_synthetic_data()
    X = df[["tickets_booked", "hours_to_event", "base_price"]]
    y = df["price"]
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42))
    ])
    pipeline.fit(X, y)
    joblib.dump(pipeline, path)
    return pipeline

def load_model(path=MODEL_PATH):
    if not os.path.exists(path):
        print("Pricing model not found. Training a new one...")
        return train_and_save_model(path)
    print("Loading existing pricing model.")
    return joblib.load(path)

def predict_price(model, tickets_booked: int, hours_to_event: float, base_price: float):
    X = pd.DataFrame([{
        "tickets_booked": tickets_booked,
        "hours_to_event": hours_to_event,
        "base_price": base_price
    }])
    return float(model.predict(X)[0])

