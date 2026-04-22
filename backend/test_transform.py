from data_processing.transform_survey import transform_survey_data

df_long = transform_survey_data("Project survey.csv")

print("\n=== FULL DATA ===")
print(df_long.head())

print("\n=== WITH COURSE DIFFICULTY ===")
print(df_long[["Username", "course_code", "difficulty", "study_time", "grade", "points"]].head())

print("\n=== AVG BY DIFFICULTY ===")
print(df_long.groupby("difficulty")["points"].mean())