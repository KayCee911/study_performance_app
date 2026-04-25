import joblib
import numpy as np

model = joblib.load("ml/recommender.pkl")

def recommend(study_hours, difficulty, study_method, unit):

    method_map = {
        "Active": 1,
        "Passive": 0,
        "Unknown": 0
    }

    base = np.array([[study_hours, difficulty, method_map.get(study_method, 0), unit]])

    current_gpa = model.predict(base)[0]

    # TRY IMPROVEMENTS
    better_hours = study_hours + 2
    better_method = 1  # Active

    improved = np.array([[better_hours, difficulty, better_method, unit]])
    improved_gpa = model.predict(improved)[0]

    return {
        "current_gpa": round(current_gpa, 2),
        "improved_gpa": round(improved_gpa, 2),
        "suggestion": "Increase study hours and use active study method"
    }