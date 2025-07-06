import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.recommender_helper import recommend_courses_semantic


COURSE_JSON = '/home/natalie/Bachelorprojekt/evaluation/course_subset.json'

# Load course subset
with open(COURSE_JSON, 'r', encoding='utf-8') as f:
    subset_courses = json.load(f)


subset_names = set(
    f"{course['kennung']}: {course['name']}".strip() for course in subset_courses
)

print(f"Subset courses loaded: {len(subset_names)}")

# Get recommendations
top_courses = recommend_courses_semantic(
    "Programmer - Game Development + Web Front End.",
    ["Englisch", "Deutsch/Englisch", "Deutsch"],
    ["Bachelor", "Bachelor/Master", "Master"]
)

print("\nCourses recommended AND in subset:\n")

matches = []

for job_title, course_list in top_courses:
    for course_name, course_score, required_skills in course_list:
        if course_name in subset_names:
            print(f"{course_name}: score {course_score:.4f} — teaches: {required_skills}")
            matches.append(course_name)

if not matches:
    print("No overlap found.")