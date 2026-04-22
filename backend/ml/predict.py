import joblib
import numpy as np

# Load trained model
model = joblib.load("ml/model.pkl")


def predict_gpa(study_hours, focus_score, study_method, unit, difficulty):
    features = np.array([[study_hours, focus_score, study_method, unit, difficulty]])
    prediction = model.predict(features)
    return float(prediction[0])