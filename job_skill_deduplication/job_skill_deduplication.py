from sentence_transformers import SentenceTransformer, util
import torch
from pprint import pprint
import json

jobs = []
with open("jobs_skills.jsonl", "r", encoding="utf-8") as f:
    for line_number, line in enumerate(f, start=1):
        line = line.strip()
        if not line:
            continue  # skip empty lines
        try:
            job = json.loads(line)
            jobs.append(job)
        except json.JSONDecodeError as e:
            print(f"Skipping invalid JSON on line {line_number}: {e}")

#jobs_sample = jobs[200:210]

model = SentenceTransformer('all-MiniLM-L6-v2')
threshold = 0.825

# These will grow as we discover new canonical skills
canonical_skills = []
canonical_embeddings = []

def find_canonical(skill_embedding):
    if not canonical_embeddings:
        return None
    # Stack existing embeddings into shape (N, D)
    stacked = torch.stack(canonical_embeddings)
    sims = util.cos_sim(skill_embedding, stacked)  # shape (1, N)
    max_sim, idx = sims.max(1)
    if max_sim.item() >= threshold:
        return canonical_skills[idx.item()]
    return None

# Process every job
for job in jobs:
    deduped_skills = []
    # Priority order: LLM skills first, then SkillNer full
    for skill in job.get("skills_LLM", []) + job.get("skills_skillNer_full", []):
        # Encode **exactly** as-is (preserving case)
        skill_emb = model.encode(skill, convert_to_tensor=True)

        # Try to map to an existing canonical skill
        canonical = find_canonical(skill_emb)
        if canonical is None:
            # New canonical: remember both string and its embedding
            canonical_skills.append(skill)
            canonical_embeddings.append(skill_emb)
            deduped_skills.append(skill)
        else:
            # Use the previously chosen canonical name
            if canonical not in set(deduped_skills):
                deduped_skills.append(canonical)

    # Keep at most 15, in insertion order
    job["deduplicated_skills"] = deduped_skills[:15]

with open("jobs_skills_deduplicated.json", "w", encoding="utf-8") as f:
    json.dump(jobs, f, ensure_ascii=False, indent=2)

with open("all_unique_skills.json", "w", encoding="utf-8") as f:
    json.dump(list(canonical_skills), f, indent=2, ensure_ascii=False)
