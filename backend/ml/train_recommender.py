import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor

from data_processing.transform_survey import transform_survey_data


# ==============================
# LOAD + CLEAN DATA
# ==============================
df = transform_survey_data("Project survey.csv")

df = df.dropna(subset=["points"])

# Encode study method
df["study_method"] = df["study_method"].map({
    "Active": 1,
    "Passive": 0,
    "Unknown": 0
}).fillna(0)

# ==============================
# CLEAN NUMERICAL FEATURES
# ==============================
df["study_time"] = df["study_time"].fillna(0).clip(0, 5)
df["difficulty"] = df["difficulty"].fillna(0).clip(0, 5)
df["unit"] = df["unit"].fillna(3)

# Remove extreme noise
df = df[df["study_time"] <= 5]
df = df[df["difficulty"] <= 5]

# ==============================
# FEATURE ENGINEERING (IMPROVED)
# ==============================

# smarter effort
df["effort_score"] = df["study_time"] / (df["difficulty"] + 1)

# pressure from difficulty + bad method
df["difficulty_pressure"] = df["difficulty"] * (1 - df["study_method"])

features = [
    "study_time",
    "difficulty",
    "study_method",
    "unit",
    "effort_score",
    "difficulty_pressure"
]

X = df[features]
y = df["points"]

# ==============================
# SCALE FEATURES
# ==============================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ==============================
# TRAIN / TEST SPLIT
# ==============================
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# ==============================
# MODEL (REGULARIZED)
# ==============================
model = RandomForestRegressor(
    n_estimators=300,
    max_depth=8,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42
)

model.fit(X_train, y_train)

# ==============================
# EVALUATE
# ==============================
preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)

print(f"🔥 MAE: {round(mae, 3)}")

# ==============================
# SAVE
# ==============================
joblib.dump(model, "ml/recommender.pkl")
joblib.dump(scaler, "ml/scaler.pkl")

print("Model + Scaler saved")