from models import Performance


# =========================
# CALCULATE ERROR
# =========================
def calculate_error():

    records = Performance.query.filter(
        Performance.predicted_gpa.isnot(None)
    ).all()

    errors = []

    for r in records:
        if r.gpa is None or r.predicted_gpa is None:
            continue

        error = abs(r.gpa - r.predicted_gpa)
        errors.append(error)

    if not errors:
        return None

    return sum(errors) / len(errors)


# =========================
# SHOULD RETRAIN
# =========================
def should_retrain(threshold=0.5, min_samples=50):

    error = calculate_error()
    total_samples = Performance.query.count()

    if error is None:
        return False

    return error > threshold and total_samples > min_samples