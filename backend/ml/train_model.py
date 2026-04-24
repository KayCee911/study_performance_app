import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer
import joblib

from data_processing.transform_survey import transform_survey_data

# LOAD DATA
df = transform_survey_data("Project survey.csv")

# ENCODE study_method
df["study_method"] = df["study_method"].map({
    "Active": 1,
    "Passive": 0
})

# DROP rows where target is missing
df = df.dropna(subset=["points"])

# FEATURES
X = df[["study_time", "difficulty", "study_method"]]
y = df["points"]

# HANDLE MISSING VALUES (IMPORTANT)
imputer = SimpleImputer(strategy="mean")
X = imputer.fit_transform(X)

# TRAIN TEST SPLIT
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# MODEL
model = LinearRegression()
model.fit(X_train, y_train)

# SAVE MODEL + IMPUTER
joblib.dump(model, "ml/model.pkl")
joblib.dump(imputer, "ml/imputer.pkl")

print("✅ Model trained and saved!")