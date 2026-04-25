import joblib

model = joblib.load("ml/model.pkl")
imputer = joblib.load("ml/imputer.pkl")


def predict_gpa(study_hours, difficulty, study_method):
    study_method_map = {
        "Active": 1,
        "Passive": 0
    }

    study_method = study_method_map.get(study_method)

    if study_method is None:
        raise ValueError("Invalid study method")

    X = [[study_hours, difficulty, study_method]]
    X = imputer.transform(X)

    prediction = model.predict(X)[0]

    return float(prediction)