import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


# =========================
# BUILD FEATURES
# =========================
def build_cluster_features(df):

    required_cols = ["username", "study_time", "difficulty", "points", "unit"]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    # Aggregate per student
    features = df.groupby("username").agg({
        "study_time": "mean",
        "difficulty": "mean",
        "points": "mean",
        "unit": "mean"
    }).reset_index()

    features.rename(columns={
        "study_time": "avg_hours",
        "difficulty": "avg_difficulty",
        "points": "avg_gpa",
        "unit": "avg_unit"
    }, inplace=True)

    return features


# =========================
# TRAIN CLUSTER MODEL
# =========================
def train_clustering(df, k=3):

    features = build_cluster_features(df)

    X = features.drop(columns=["username"])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    features["cluster"] = model.fit_predict(X_scaled)

    return features, model, scaler


# =========================
# GET SIMILAR STUDENTS
# =========================
def get_similar_students(email, df): 

    try:
        features, model, scaler = train_clustering(df)

        # Normalize email (important)
        email = str(email).strip().lower()

        user_row = features[features["username"] == email]

        if user_row.empty:
            return pd.DataFrame()

        user_cluster = user_row.iloc[0]["cluster"]

        similar = features[features["cluster"] == user_cluster].copy()

        # =========================
        # 🔥 ADD RANKING HERE
        # =========================
        if "avg_gpa" in similar.columns:
            similar["rank"] = similar["avg_gpa"].rank(
                ascending=False,
                method="dense"
            )

        return similar

    except Exception as e:
        print("Clustering error:", e)
        return pd.DataFrame()