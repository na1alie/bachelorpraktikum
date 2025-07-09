import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.recommender_helper import recommend_courses_top_coverage, recommend_courses_top_similarity


COURSE_JSON = '/home/natalie/Bachelorprojekt/evaluation/course_subset.json'
JOBS_JSON = '/home/natalie/Bachelorprojekt/evaluation/job_subset.json'


# Load course subset
with open(COURSE_JSON, 'r', encoding='utf-8') as f:
    subset_courses = json.load(f)

subset_names = set(
    f"{course['kennung']}: {course['name']}".strip() for course in subset_courses
)

print(f"Subset courses loaded: {len(subset_names)}")

# Load jobs
with open(JOBS_JSON, 'r', encoding='utf-8') as f:
    jobs = json.load(f)

# Prepare results
all_results = []

# For each job in the JSON
for job in jobs:
    job_title = job['job_title']
    job_levels = [job['seniority_level']]
    language = ["Englisch", "Deutsch/Englisch", "Deutsch"]
    module_level = ["Bachelor", "Bachelor/Master", "Master"]

    for top_n in [10, 20, 30, 50]:
        print(f"\n##### {job_title} | Similarity | Top {top_n} #####")

        similarity_results = recommend_courses_top_similarity(
            job_title,
            job_levels,
            language,
            module_level,
            top_n
        )
        similarity_recommended = []
        similarity_matches = []

        for _, course_list in similarity_results:
            for course_name, _, _ in course_list:
                similarity_recommended.append(course_name)
                if course_name in subset_names:
                    similarity_matches.append(course_name)

        print(f"Total similarity recommended: {len(similarity_recommended)}")
        print(f"Matches: {len(similarity_matches)}")

        all_results.append({
            "job": job_title,
            "method": "top_similarity",
            "top_n": top_n,
            "recommended": similarity_recommended,
            "matches": similarity_matches
        })

        print(f"\n##### {job_title} | Coverage | Top {top_n} #####")

        coverage_results = recommend_courses_top_coverage(
            job_title,
            job_levels,
            language,
            module_level,
            top_n
        )
        coverage_recommended = []
        coverage_matches = []

        for _, course_list in coverage_results:
            for course_name, _, _ in course_list:
                coverage_recommended.append(course_name)
                if course_name in subset_names:
                    coverage_matches.append(course_name)

        print(f"Total coverage recommended: {len(coverage_recommended)}")
        print(f"Matches: {len(coverage_matches)}")

        all_results.append({
            "job": job_title,
            "method": "top_coverage",
            "top_n": top_n,
            "recommended": coverage_recommended,
            "matches": coverage_matches
        })

# Write all results to a JSON file
output_path = '/home/natalie/Bachelorprojekt/evaluation/evaluation.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print(f"\n Results written to: {output_path}")