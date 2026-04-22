import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# -----------------------------
# 1. LOAD DATA FROM DATABASE EXPORT OR CSV
# -----------------------------
df = pd.read_csv("Project survey.csv")  
# later we can connect directly to PostgreSQL

# -----------------------------
# 2. FEATURE ENGINEERING
# -----------------------------

# Encode study method (e.g., reading, group study, video)
le = LabelEncoder()
df["study_method"] = le.fit_transform(df["study_method"])

features = [
    "study_hours",
    "focus_score",
    "study_method",
    "unit",
    "difficulty"
]

X = df[features]
y = df["gpa"]

# -----------------------------
# 3. TRAIN / TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# 4. MODEL TRAINING
# -----------------------------
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# -----------------------------
# 5. SAVE MODEL
# -----------------------------
os.makedirs("ml", exist_ok=True)
joblib.dump(model, "ml/model.pkl")

print("Model trained and saved successfully!")