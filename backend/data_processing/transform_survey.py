import pandas as pd
import re


def clean_numeric(value):
    if pd.isna(value):
        return None

    nums = re.findall(r"\d+\.?\d*", str(value))
    return float(nums[0]) if nums else None


def clean_study_time(value):
    if pd.isna(value):
        return None

    value = str(value).lower()
    value = value.replace("hours", "").replace("hrs", "").replace("hr", "").strip()

    # handle ranges like "4-5"
    if "-" in value:
        parts = re.findall(r"\d+\.?\d*", value)
        if len(parts) >= 2:
            return sum(map(float, parts)) / len(parts)

    nums = re.findall(r"\d+\.?\d*", value)
    return float(nums[0]) if nums else None


def transform_survey_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    records = []

    for _, row in df.iterrows():
        username = row.get("Username")

        if pd.isna(username):
            continue

        for i in range(1, 11):
            try:
                course = row.get(f"1. Course {i} code")
                unit = row.get(f"2. Course {i} Unit (in figures)")
                difficulty = row.get(f"3. Course {i} difficulty")
                study_time = row.get(f"4. Study time for this course (hours per week)")
                study_method = row.get(f"5. Study method for course {i}")
                grade = row.get(f"6. Course {i} Grade")

                # skip invalid grade
                if pd.isna(grade):
                    continue

                grade = str(grade).strip().upper()

                grade_map = {"A":5, "B":4, "C":3, "D":2, "E":1, "F":0}
                points = grade_map.get(grade)

                if points is None:
                    continue

                # ---------- CLEAN VALUES ----------
                unit = clean_numeric(unit)
                if unit is None:
                    unit = 3

                difficulty = clean_numeric(difficulty)
                if difficulty is None:
                    difficulty = 3

                study_time = clean_study_time(study_time)
                if study_time is None:
                    study_time = 0

                if pd.notna(study_method):
                    study_method = str(study_method).strip().capitalize()
                    if study_method not in ["Active", "Passive"]:
                        study_method = "Passive"
                else:
                    study_method = "Passive"

                # ---------- RECORD ----------
                records.append({
                    "username": str(username).strip().lower(),
                    "course": str(course).strip() if pd.notna(course) else "UNKNOWN",
                    "unit": float(unit),
                    "difficulty": float(difficulty),
                    "study_time": float(study_time),
                    "study_method": study_method,
                    "grade": grade,
                    "points": float(points)
                })

            except Exception as e:
                print(f"Error processing course {i}:", e)

    df_clean = pd.DataFrame(records)

    print("\n=== TRANSFORMED DATA SAMPLE ===")
    print(df_clean.head())

    return df_clean