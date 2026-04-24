from flask import Blueprint, request, jsonify
from backend.ml.model_loader import predict_performance

ml = Blueprint("ml", __name__)

@ml.route("/predict", methods=["POST"])
def predict():

    data = request.json

    result = predict_performance(
        study_time=data["study_time"],
        unit=data["unit"],
        difficulty=data["difficulty"],
        study_method=data["study_method"]
    )

    return jsonify({
        "predicted_grade_point": round(result, 2)
    })