import json


with open("evaluation.json", "r", encoding="utf-8") as f:
    evaluation_results = json.load(f)

with open("job_subset.json", "r", encoding="utf-8") as f:
    fitting_jobs = json.load(f)


job_lookup = {job["job_title"]: job for job in fitting_jobs}

for result in evaluation_results:
    job_title = result['job']
    matches = result['matches']

    # find the fitting ground truth for this job:
    fitting_courses = [
        j['fitting_courses_subset']
        for j in fitting_jobs
        if j['job_title'] == job_title
    ][0]

    true_matches = [r for r in matches if r in fitting_courses]

    precision = len(true_matches) / len(matches) if matches else 0
    recall = len(true_matches) / len(fitting_courses) if fitting_courses else 0

    result['precision'] = precision
    result['recall'] = recall
    result['true_matches'] = true_matches

with open("precision_recall.json", "w", encoding="utf-8") as f:
    json.dump(evaluation_results, f, indent=2, ensure_ascii=False)

print ("done")
