import joblib
import pandas as pd

MODEL_PATH = "ml/kmeans.pkl"
SCALER_PATH = "ml/kmeans_scaler.pkl"
DATA_PATH = "ml/student_clusters.csv"


def get_similar_students(email):

    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        df = pd.read_csv(DATA_PATH)
    except:
        print("⚠️ No clustering file found — skipping peer insights")
        return None

    user_row = df[df["email"] == email]

    if user_row.empty:
        return None

    cluster_id = user_row.iloc[0]["cluster"]

    # return only same cluster students
    peers = df[df["cluster"] == cluster_id]

    return peers