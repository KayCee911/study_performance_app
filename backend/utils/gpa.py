def calculate_gpa(courses):
    total_points = 0
    total_units = 0

    for course in courses:
        if course.points is None or course.unit is None:
            continue

        total_points += course.points * course.unit
        total_units += course.unit

    if total_units == 0:
        return 0

    return round(total_points / total_units, 2)