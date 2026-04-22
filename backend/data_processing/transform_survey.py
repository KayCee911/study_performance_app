import pandas as pd

def transform_survey_data(file_path):
    df = pd.read_csv(file_path)

    # STEP 1: CLEAN COLUMN NAMES
    df.columns = df.columns.str.strip()

    id_cols = ["Timestamp", "Username"]

    course_rows = []

    # STEP 2: LOOP THROUGH COURSES (1–10)
    for i in range(1, 11):

        code_col = f"1. Course {i} code"
        unit_col = f"2. Course {i} Unit (in figures)"
        diff_col = f"3. Course {i} difficulty"
        time_col = f"4. Study time for this course (hours per week)"
        method_col = f"5. Study method for course {i}"
        grade_col = f"6. Course {i} Grade"

        # skip if missing
        if grade_col not in df.columns:
            continue

        temp = df[id_cols + [
            code_col, unit_col, diff_col,
            time_col, method_col, grade_col
        ]].copy()

        temp = temp.rename(columns={
            code_col: "course_code",
            unit_col: "unit",
            diff_col: "difficulty",
            time_col: "study_time",
            method_col: "study_method",
            grade_col: "grade"
        })

        temp["course_no"] = i

        course_rows.append(temp)

    # STEP 3: COMBINE ALL COURSES
    df_long = pd.concat(course_rows, ignore_index=True)

    # STEP 4: CLEAN
    df_long = df_long.dropna(subset=["grade"])

    df_long["grade"] = df_long["grade"].astype(str).str.upper().str.strip()

    grade_map = {"A":5,"B":4,"C":3,"D":2,"E":1,"F":0}
    df_long["points"] = df_long["grade"].map(grade_map)

    return df_long