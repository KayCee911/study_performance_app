import joblib

model = joblib.load("ml/recommender.pkl")
scaler = joblib.load("ml/scaler.pkl")


def build_features(study_hours, difficulty, study_method, unit):

    method_map = {"Active": 1, "Passive": 0, "Unknown": 0}
    m = method_map.get(study_method, 0)

    # ✅ MATCH TRAINING
    effort_score = study_hours / (difficulty + 1)
    difficulty_pressure = difficulty * (1 - m)

    return [
        study_hours,
        difficulty,
        m,
        unit,
        effort_score,
        difficulty_pressure
    ]


def recommend(study_hours, difficulty, study_method, unit):

    base = build_features(study_hours, difficulty, study_method, unit)
    base_scaled = scaler.transform([base])

    current_gpa = model.predict(base_scaled)[0]

    best_gpa = current_gpa
    best_plan = (study_hours, study_method)

    for hours in range(int(study_hours), int(study_hours) + 5):
        for method in ["Active", "Passive"]:

            feat = build_features(hours, difficulty, method, unit)
            feat_scaled = scaler.transform([feat])

            pred = model.predict(feat_scaled)[0]

            if pred > best_gpa:
                best_gpa = pred
                best_plan = (hours, method)

    if best_gpa <= current_gpa:
        suggestion = "Current strategy is already optimal"
    else:
        suggestion = f"Study {best_plan[0]} hrs using {best_plan[1]} method"

    return {
        "current_gpa": round(float(current_gpa), 2),
        "improved_gpa": round(float(best_gpa), 2),
        "suggestion": suggestion
    }