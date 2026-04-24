import joblib

model = joblib.load("ml/model.pkl")

def predict_gpa(study_hours, difficulty, study_method):

    method_map = {
        "Active": 1,
        "Passive": 0
    }

    method_encoded = method_map.get(study_method, 0)

    prediction = model.predict([[
        study_hours,
        difficulty,
        method_encoded
    ]])

    return float(prediction[0])