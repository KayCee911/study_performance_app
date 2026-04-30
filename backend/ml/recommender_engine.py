import joblib
import pandas as pd
import numpy as np

# ==============================
# LOAD MODEL
# ==============================
model = joblib.load("ml/recommender.pkl")
scaler = joblib.load("ml/scaler.pkl")

FEATURE_COLUMNS = [
    "study_time",
    "difficulty",
    "study_method",
    "unit",
    "effort_score",
    "difficulty_pressure"
]


# ==============================
# ENCODING
# ==============================
def encode_method(method):
    return 1 if str(method).lower() == "active" else 0


# ==============================
# FEATURE ENGINEERING
# ==============================
def build_features(study_time, difficulty, method, unit):

    study_time = float(study_time or 0)
    difficulty = float(difficulty or 0)
    unit = float(unit or 3)

    method_val = encode_method(method)

    effort_score = study_time / (difficulty + 1)
    difficulty_pressure = difficulty * (1 - method_val)

    return [
        study_time,
        difficulty,
        method_val,
        unit,
        effort_score,
        difficulty_pressure
    ]


# ==============================
# PREDICT
# ==============================
def predict(features):

    X_df = pd.DataFrame([features], columns=FEATURE_COLUMNS)
    X_scaled = scaler.transform(X_df)

    pred = float(model.predict(X_scaled)[0])

    return pred


# ==============================
# STATISTICAL CONFIDENCE
# ==============================
def compute_confidence(features, n_samples=20):

    preds = []

    for _ in range(n_samples):
        noise = np.random.normal(0, 0.05, len(features))
        noisy = [f + n for f, n in zip(features, noise)]

        preds.append(predict(noisy))

    std = np.std(preds)

    # lower std = higher confidence
    confidence = max(0, min(1, 1 - std))

    return round(confidence, 2)


# ==============================
# EXPLANATIONS
# ==============================
def generate_explanations(current, recommended):

    explanations = []

    if recommended["hours"] > current["hours"]:
        explanations.append("Increasing study time improves understanding")

    if recommended["method"] != current["method"]:
        if recommended["method"] == "Active":
            explanations.append("Active study improves retention")
        else:
            explanations.append("Passive study suits this course pattern")

    if current["difficulty"] >= 4:
        explanations.append("High course difficulty requires more effort")

    if current["hours"] < 2:
        explanations.append("Study time is below optimal threshold")

    if not explanations:
        explanations.append("Current strategy already optimal")

    return explanations


# ==============================
# OPTIMIZATION
# ==============================
def optimize_recommendation(current_hours, difficulty, method, unit):

    best_gpa = -1
    best_plan = (current_hours, method)

    # SEARCH
    for hours in range(1, 5):
        for m in ["Active", "Passive"]:

            features = build_features(hours, difficulty, m, unit)
            pred = predict(features)

            if pred > best_gpa:
                best_gpa = pred
                best_plan = (hours, m)

    # CURRENT
    current_features = build_features(current_hours, difficulty, method, unit)
    current_gpa = predict(current_features)

    # NO FAKE IMPROVEMENT
    if best_gpa <= current_gpa:
        best_gpa = current_gpa
        best_plan = (current_hours, method)

    # CONFIDENCE (STATISTICAL)
    confidence = compute_confidence(current_features)

    explanations = generate_explanations(
        {"hours": current_hours, "method": method, "difficulty": difficulty},
        {"hours": best_plan[0], "method": best_plan[1]}
    )

    return {
        "current_gpa": round(current_gpa, 2),
        "improved_gpa": round(best_gpa, 2),
        "recommended_hours": int(best_plan[0]),
        "recommended_method": best_plan[1],
        "confidence": confidence,
        "explanations": explanations
    }


# ==============================
# AI SUMMARY
# ==============================
def generate_ai_summary(results):

    if not results:
        return "No data available."

    weak = [r["course"] for r in results if r["current_gpa"] < 3]
    strong = [r["course"] for r in results if r["current_gpa"] >= 4]

    improvements = [
        r["improved_gpa"] - r["current_gpa"]
        for r in results
    ]

    avg_gain = round(sum(improvements) / len(improvements), 2)

    return (
        f"You are strong in {len(strong)} courses, "
        f"while {len(weak)} need improvement. "
        f"Following recommendations can increase GPA by ~{avg_gain}. "
        f"Main pattern: more study time + active learning improves results."
    )