from sentence_transformers import SentenceTransformer, util
import torch
import json
from collections import Counter

input_file = "../job_seniority_classification/jobs_complete.jsonl"
output_file = "jobs_titles_deduplicated_2.jsonl"
canonical_titles_file = "all_unique_job_titles_with_groups.json"
graph_load_file = "jobs_to_load_into_graph.jsonl"  # NEW file to store one representative job per group

model = SentenceTransformer('all-MiniLM-L6-v2')
threshold = 0.80
max_group_size = 3
top_k = 30  # number of top skills to retain

canonical_groups = {}  # key: (canonical_title, level), value: list of dicts with 'title' and 'level'

all_jobs = []
with open(input_file, "r", encoding="utf-8") as f_in:
    for line in f_in:
        if line.strip():
            try:
                job = json.loads(line)
                all_jobs.append(job)
            except json.JSONDecodeError:
                continue

# Precompute embeddings for all job titles + seniority levels
job_embeddings = []
for job in all_jobs:
    title = job.get("cleaned_job_title", "").strip()
    level = job.get("job_seniority_level", "").strip()
    emb = model.encode(title, convert_to_tensor=True)
    job_embeddings.append((job, title, level, emb))

assigned = [False] * len(all_jobs)
written = [False] * len(all_jobs)

with open(output_file, "w", encoding="utf-8") as f_out, open(graph_load_file, "w", encoding="utf-8") as f_graph:
    for i, (job_i, title_i, level_i, emb_i) in enumerate(job_embeddings):
        if assigned[i]:
            continue

        group_id = f"group_{len(canonical_groups)}"
        canonical_groups[group_id] = {
            "canonical_title": title_i,
            "level": level_i,
            "members": [{"title": title_i, "level": level_i}]
        }
        
        assigned[i] = True

        candidates = []
        for j, (job_j, title_j, level_j, emb_j) in enumerate(job_embeddings):
            if i == j or assigned[j]:
                continue
            if level_j != level_i:
                continue
            sim = util.cos_sim(emb_i, emb_j).item()
            if sim >= threshold:
                candidates.append((j, sim, title_j, level_j))

        candidates = sorted(candidates, key=lambda x: x[1], reverse=True)[:max_group_size-1]

        group_indices = [i]
        for j, sim, title_j, level_j in candidates:
            assigned[j] = True
            canonical_groups[canonical_key].append({"title": title_j, "level": level_j})
            group_indices.append(j)

        print()
        print("NEXT GROUP ###############################################")
        # Collect skills from all jobs in the group
        all_skills = []
        for idx in group_indices:
            all_skills.extend(job_embeddings[idx][0].get("deduplicated_skills", []))
            print(job_embeddings[idx][1])
            print(job_embeddings[idx][2])
            print(job_embeddings[idx][0].get("deduplicated_skills", []))
        print(all_skills)
        common_skills = [skill for skill, _ in Counter(all_skills).most_common(top_k)]
        print(common_skills)

        # Write jobs in group to output file, adding deduplicated fields
        for idx in group_indices:
            job = job_embeddings[idx][0]
            job["deduplicated_title"] = canonical_key[0]
            job["deduplicated_skills"] = common_skills
            json.dump(job, f_out, ensure_ascii=False)
            f_out.write("\n")
            written[idx] = True

        # Save ONE representative job (the canonical one) to graph file
        canonical_job = job_embeddings[i][0].copy()
        canonical_job["deduplicated_title"] = canonical_key[0]
        canonical_job["deduplicated_skills"] = common_skills
        json.dump(canonical_job, f_graph, ensure_ascii=False)
        f_graph.write("\n")

# Prepare canonical group overview
nested_canonical_groups = {}
for (title, level), matches in canonical_groups.items():
    if title not in nested_canonical_groups:
        nested_canonical_groups[title] = {}
    nested_canonical_groups[title][level] = matches

with open(canonical_titles_file, "w", encoding="utf-8") as f:
    json.dump(nested_canonical_groups, f, ensure_ascii=False, indent=2)

