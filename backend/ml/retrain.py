import pandas as pd
import numpy as np
import joblib

from models import Course
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ml.recommender_engine import build_features, FEATURE_COLUMNS


# =========================
# FETCH DATA
# =========================
def fetch_training_data():

    records = []

    courses = Course.query.all()

    for c in courses:

        perf = c.performance
        habit = c.study_habits[0] if c.study_habits else None

        if not perf or not habit:
            continue

        if perf.gpa is None or habit.study_hours is None:
            continue

        records.append({
            "study_time": habit.study_hours,
            "difficulty": c.difficulty or 0,
            "study_method": habit.study_method or "Passive",
            "unit": c.unit or 3,
            "points": perf.gpa
        })

    return pd.DataFrame(records)


# =========================
# RETRAIN MODEL
# =========================
def retrain_model():

    df = fetch_training_data()

    # ✅ SAFETY: NO DATA
    if df.empty:
        return {"error": "No data available for training"}

    df = df.dropna()
    df = df[df["study_time"] > 0]

    X = []
    y = []

    for _, row in df.iterrows():
        features = build_features(
            row["study_time"],
            row["difficulty"],
            row["study_method"],
            row["unit"]
        )
        X.append(features)
        y.append(row["points"])

    if len(X) == 0:
        return {"error": "Not enough valid training samples"}

    # ✅ Use DataFrame for feature names
    X_df = pd.DataFrame(X, columns=FEATURE_COLUMNS)
    y = np.array(y)

    # =========================
    # SCALE
    # =========================
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_df)

    # =========================
    # TRAIN
    # =========================
    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=10,
        random_state=42
    )

    model.fit(X_scaled, y)

    # =========================
    # EVALUATE
    # =========================
    preds = model.predict(X_scaled)

    mae = mean_absolute_error(y, preds)
    rmse = np.sqrt(mean_squared_error(y, preds))
    r2 = r2_score(y, preds)

    # =========================
    # SAVE
    # =========================
    joblib.dump(model, "ml/recommender.pkl")
    joblib.dump(scaler, "ml/scaler.pkl")
    joblib.dump(FEATURE_COLUMNS, "ml/feature_columns.pkl")

    return {
        "message": "Model retrained successfully",
        "samples": int(len(X)),
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "r2": round(r2, 3),
        "feature_importance": model.feature_importances_.tolist()
    }