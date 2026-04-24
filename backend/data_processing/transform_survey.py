import pandas as pd
import re

def clean_study_time(value):
    if pd.isna(value):
        return None

    value = str(value).lower()

    # remove text noise
    value = value.replace("hours", "").replace("hrs", "").replace("hr", "").strip()

    # handle ranges like "4-5"
    if "-" in value:
        parts = value.split("-")
        try:
            nums = [float(p) for p in parts if p.strip().isdigit()]
            if len(nums) == 2:
                return sum(nums) / 2
        except:
            return None

    # extract number
    nums = re.findall(r"\d+", value)
    return float(nums[0]) if nums else None


def transform_survey_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    records = []

    for _, row in df.iterrows():
        username = row["Username"]

        for i in range(1, 11):
            try:
                course = row.get(f"1. Course {i} code")
                grade = row.get(f"6. Course {i} Grade")
                difficulty = row.get(f"3. Course {i} difficulty")
                study_time = row.get(f"4. Study time for this course (hours per week)")
                study_method = row.get(f"5. Study method for course {i}")

                # skip empty grades
                if pd.isna(grade):
                    continue

                grade = str(grade).strip().upper()

                grade_map = {"A":5,"B":4,"C":3,"D":2,"E":1,"F":0}
                points = grade_map.get(grade)

                if points is None:
                    continue

                # CLEAN difficulty
                difficulty = pd.to_numeric(difficulty, errors="coerce")

                # CLEAN study_time
                study_time = clean_study_time(study_time)

                # CLEAN study_method
                if pd.notna(study_method):
                    study_method = str(study_method).strip().capitalize()
                else:
                    study_method = None

                records.append({
                    "username": username,
                    "course": str(course).strip() if pd.notna(course) else None,
                    "grade": grade,
                    "points": points,
                    "difficulty": difficulty,
                    "study_time": study_time,
                    "study_method": study_method
                })

            except Exception as e:
                print(f"Error processing course {i}:", e)

    df_clean = pd.DataFrame(records)

    print("\n=== TRANSFORMED DATA ===")
    print(df_clean.head())
    print("\nMissing values:\n", df_clean.isna().sum())

    return df_clean