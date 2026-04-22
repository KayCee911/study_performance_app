from flask import Blueprint, request, jsonify
from ml.predict import predict_gpa
from sklearn.preprocessing import LabelEncoder

ml = Blueprint("ml", __name__)

# Temporary encoder (later we improve this properly)
le = LabelEncoder()
le.fit(["reading", "group", "video", "practice"])

@ml.route("/predict-gpa", methods=["POST"])
def predict():
    data = request.json

    study_hours = data["study_hours"]
    focus_score = data["focus_score"]
    study_method = le.transform([data["study_method"]])[0]
    unit = data["unit"]
    difficulty = data["difficulty"]

    result = predict_gpa(
        study_hours,
        focus_score,
        study_method,
        unit,
        difficulty
    )

    return jsonify({
        "predicted_gpa": round(result, 2)
    })