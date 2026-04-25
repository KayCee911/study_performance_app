import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

from data_processing.transform_survey import transform_survey_data

# LOAD DATA
df = transform_survey_data("Project survey.csv")

# CLEAN
df = df.dropna(subset=["points"])

# ENCODE study_method
df["study_method"] = df["study_method"].map({
    "Active": 1,
    "Passive": 0,
    "Unknown": 0
})

# FEATURES
X = df[["study_time", "difficulty", "study_method", "unit"]].fillna(0)

# TARGET
y = df["points"]

# TRAIN
model = RandomForestRegressor()
model.fit(X, y)

# SAVE
joblib.dump(model, "ml/recommender.pkl")

print(" Model trained and saved")