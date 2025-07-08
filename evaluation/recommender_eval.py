import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.recommender_helper import recommend_courses_top_coverage, recommend_courses_top_similarity


COURSE_JSON = '/home/natalie/Bachelorprojekt/evaluation/course_subset.json'

# Load course subset
with open(COURSE_JSON, 'r', encoding='utf-8') as f:
    subset_courses = json.load(f)


subset_names = set(
    f"{course['kennung']}: {course['name']}".strip() for course in subset_courses
)

print(f"Subset courses loaded: {len(subset_names)}")

print("######### TOP SIMILARITY ##########")

# Get recommendations
top_courses = recommend_courses_top_similarity(
    "IT Security Engineer",
    ["Entry level"],
    ["Englisch", "Deutsch/Englisch", "Deutsch"],
    ["Bachelor", "Bachelor/Master", "Master"]
)
num_recommended = sum(len(course_list) for _, course_list in top_courses)
print(f"\nTotal courses recommended: {num_recommended}")

print("\nCourses recommended AND in subset:\n")
matches = []

for job_title, course_list in top_courses:
    for course_name, _, _ in course_list:
        if course_name in subset_names:
            print(course_name)
            matches.append(course_name)

if not matches:
    print("No overlap found.")


print("######### TOP COUVERAGE ##########")

top_courses = recommend_courses_top_coverage(
    "IT Security Engineer",
    ["Entry level"],
    ["Englisch", "Deutsch/Englisch", "Deutsch"],
    ["Bachelor", "Bachelor/Master", "Master"]
)
num_recommended = sum(len(course_list) for _, course_list in top_courses)
print(f"\nTotal courses recommended: {num_recommended}")

print("\nCourses recommended AND in subset:\n")
matches = []

for job_title, course_list in top_courses:
    for course_name, _, _ in course_list:
        if course_name in subset_names:
            print(course_name)
            matches.append(course_name)

if not matches:
    print("No overlap found.")