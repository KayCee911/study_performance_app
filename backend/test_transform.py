from data_processing.transform_survey import transform_survey_data

# Run transformation
df_long = transform_survey_data("Project survey.csv")

# BASIC CHECKS
print("\n=== SORTED DATA ===")
print(df_long.sort_values(["username", "course"]))

print("\n=== GPA PER STUDENT ===")
print(df_long.groupby("username")["points"].mean())

print("\n=== AVG PER COURSE ===")
print(df_long.groupby("course")["points"].mean())