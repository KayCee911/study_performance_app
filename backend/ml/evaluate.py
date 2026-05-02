import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from ml.recommender_engine import build_features, predict


def evaluate_model(df):

    y_true = []
    y_pred = []

    for _, row in df.iterrows():

        if row["points"] is None:
            continue

        features = build_features(
            row["study_time"],
            row["difficulty"],
            row["study_method"],
            row["unit"]
        )

        pred = predict(features)

        y_pred.append(pred)
        y_true.append(row["points"])

    # ✅ SAFETY CHECK
    if not y_true:
        return {"error": "No valid data for evaluation"}

    # =========================
    # METRICS
    # =========================
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)  # ✅ Correct
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    return {
        "RMSE": round(rmse, 3),
        "MAE": round(mae, 3),
        "R2": round(r2, 3)
    }