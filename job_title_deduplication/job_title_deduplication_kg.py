from sentence_transformers import SentenceTransformer, util
import torch
import json

input_file = "jobs_titles_cleaned.jsonl"
output_file = "jobs_titles_deduplicated.jsonl"
canonical_titles_file = "all_unique_job_titles.json"

model = SentenceTransformer('all-MiniLM-L6-v2')
threshold = 0.80

canonical_titles = []
canonical_title_embeddings = []

def find_canonical(embedding):
    if not canonical_title_embeddings:
        return None
    stacked = torch.stack(canonical_title_embeddings)
    sims = util.cos_sim(embedding, stacked)
    max_sim, idx = sims.max(1)
    if max_sim.item() >= threshold:
        return canonical_titles[idx.item()]
    return None

with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    for line_number, line in enumerate(f_in, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            job = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Skipping invalid JSON on line {line_number}: {e}")
            continue

        job_title = job.get("cleaned_job_title", "").strip()
        if job_title:
            title_emb = model.encode(job_title, convert_to_tensor=True)
            canonical = find_canonical(title_emb)
            if canonical is None:
                canonical_titles.append(job_title)
                canonical_title_embeddings.append(title_emb)
                job["deduplicated_title"] = job_title
            else:
                job["deduplicated_title"] = canonical

        json.dump(job, f_out, ensure_ascii=False)
        f_out.write("\n")

# Save all canonical titles
with open(canonical_titles_file, "w", encoding="utf-8") as f:
    json.dump(canonical_titles, f, ensure_ascii=False, indent=2)
