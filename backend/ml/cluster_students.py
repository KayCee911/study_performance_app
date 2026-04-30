import pandas as pd
from sklearn.cluster import KMeans
from data_processing.transform_survey import transform_survey_data

df = transform_survey_data("Project survey.csv")

df["study_time"] = df["study_time"].fillna(0)
df["difficulty"] = df["difficulty"].fillna(0)

df["study_method"] = df["study_method"].map({
    "Active": 1,
    "Passive": 0,
    "Unknown": 0
})

# Aggregate per student
student_df = df.groupby("username").agg({
    "study_time": "mean",
    "difficulty": "mean",
    "study_method": "mean",
    "points": "mean"
}).reset_index()

X = student_df[["study_time", "difficulty", "study_method", "points"]]

kmeans = KMeans(n_clusters=3, random_state=42)
student_df["cluster"] = kmeans.fit_predict(X)

student_df.to_csv("ml/student_clusters.csv", index=False)

print("Clusters saved")