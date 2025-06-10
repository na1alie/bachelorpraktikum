import json
import re

input_file = "jobs_skills_deduplicated.jsonl"
output_file = "jobs_titles_cleaned.jsonl"

# Regex patterns to remove
patterns = [
    # Gender tags (common forms)
    r"\(\s*m\s*/\s*[wfdx](\s*/\s*[wfdx])?\s*\)",         # (m/w/d), (m/f/x), etc.
    r"\(\s*f\s*/\s*m\s*/?\s*div\s*\)",                   # (f/m/div)
    r"\(.*?m.*?w.*?d.*?\)",                              # (Allrounder, m/w/d)
    r"\(\s*f\s*/\s*m\s*/?\s*d\s*\)",                     # (f/m/d)
    r"\(\s*w\s*/\s*m\s*/?\s*d\s*\)",                     # (w/m/d)
    r"\(\s*f\s*/\s*d\s*/?\s*m\s*\)",                     # (f/d/m)
    r"\(\s*d\s*/\s*m\s*/?\s*f\s*\)",                     # (d/m/f)
    r"\(.*?german.*?\)",                                 # (German-speaking)
    r"\(.*?contract.*?\)",                               # (contract)
    r"\(\s*(term[-\w\s]*|contract|.*?benefits.*?)\)"     # (Term-limited w/ benefits)
    r"\(.*?\$.*?\)",                                     # ($150k- $230k, 1% - 2.5%)
    r"\(.*?all\s*genders.*?\)",                          # (all genders)
    r"\-?\s*limited term.*?(open)?",                     # - Limited Term (Open)
    r"\-?\s*remote\s*usa",                               # - Remote USA
    r"\-?\s*work\s*from\s*home",                         # - Work From Home
    r"100%\s*remote",                                    # 100% Remote
    r"\d+\+\s*yrs.*?experience.*?required",              # 3+ Yrs Paid Tax Experience Required
    r"für\s+die\s+region\s+dach",                        # für die Region DACH
    r"mobiles\s+arbeiten",                               # mobiles Arbeiten
    r"\b2025\b",                                         # 2025
    r"\busa\b",                                          # USA
    r"\bus\b",                                           # US
    r"\bgermany\b",                                      # Germany
    r"\(\s*[A-Za-z\s\-]+fluency\s*\)",                   # (Spanish Fluency), (German Fluency), etc.
    r"\(\s*[A-Za-z\s\-]+speaking\s*\)",                  # (German-speaking), etc.
    r"\brelocate to saudi arabia\b",                     # Relocate to Saudi Arabia
    r"\b(munich|san francisco)\b"                        # Munich or San Francisco

]

# Compile all into one regex pattern
combined_pattern = re.compile("|".join(patterns), re.IGNORECASE)

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

        title = job.get("job_title", "")
        if title:
            print(title)
            # Remove noise terms
            cleaned = combined_pattern.sub("", title)
            # Collapse extra whitespace
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            job["cleaned_job_title"] = cleaned
            print(cleaned)

        json.dump(job, f_out, ensure_ascii=False)
        f_out.write("\n")

