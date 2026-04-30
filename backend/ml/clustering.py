import pandas as pd
import joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from models import db, User

MODEL_PATH = "ml/kmeans.pkl"
SCALER_PATH = "ml/kmeans_scaler.pkl"


# ============================
# BUILD DATASET (FROM DB)
# ============================
def build_student_dataset():

    data = []

    users = User.query.all()

    for user in users:

        gpas, hours, diffs, methods = [], [], [], []

        for sem in user.semesters:
            for c in sem.courses:

                if c.performance and c.performance.gpa is not None:
                    gpas.append(c.performance.gpa)

                if c.difficulty is not None:
                    diffs.append(c.difficulty)

                if c.study_habits:
                    h = c.study_habits[0]

                    if h.study_hours is not None:
                        hours.append(h.study_hours)

                    if h.study_method:
                        methods.append(
                            1 if str(h.study_method).lower() == "active" else 0
                        )

        if not gpas:
            continue

        data.append({
            "email": user.email,
            "avg_gpa": sum(gpas)/len(gpas),
            "avg_hours": sum(hours)/len(hours) if hours else 0,
            "avg_difficulty": sum(diffs)/len(diffs) if diffs else 0,
            "active_ratio": sum(methods)/len(methods) if methods else 0
        })

    return pd.DataFrame(data)


# ============================
# TRAIN CLUSTER MODEL
# ============================
def train_clustering(k=3):

    df = build_student_dataset()

    if df.empty:
        print("No data for clustering")
        return

    X = df[["avg_gpa", "avg_hours", "avg_difficulty", "active_ratio"]]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = KMeans(n_clusters=k, random_state=42)
    df["cluster"] = model.fit_predict(X_scaled)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    df.to_csv("ml/student_clusters.csv", index=False)

    print("Clustering trained successfully")