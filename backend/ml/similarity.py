import pandas as pd
from ml.clustering import get_similar_students as cluster_similar
from data_processing.transform_survey import transform_survey_data


def get_similar_students(email):

    try:
        # 🔥 ALWAYS USE PROCESSED DATA
        df = transform_survey_data("temp.csv")

        if df.empty:
            print("Dataset is empty after transformation")
            return pd.DataFrame()

        return cluster_similar(email, df)

    except Exception as e:
        print("Clustering error:", e)
        return pd.DataFrame()