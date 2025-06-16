import os
import json
import anthropic
import time
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = "../job_title_deduplication/jobs_titles_deduplicated.jsonl"
OUTPUT_FILE = "jobs_complete.jsonl"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_seniority_level(title, description):
    prompt = """
    You are given a job posting consisting of a title and a description.

    Your task is to classify the job's seniority level using one of the following categories:

    - **Internship**: Student or temporary intern roles.
    - **Entry Level**: First full-time job or junior roles, graduate roles.
    - **Associate**: A level above entry, often part of "Associate" titles.
    - **Mid-Senior level**: Includes “Mid-Level”, “Mid-Senior”, or jobs between Associate and Senior.
    - **Senior**: Includes “Senior”, “Lead”, “Staff”, “Principal”.
    - **Director**: Manager of managers; leadership roles.
    - **Executive**: VP, C-level, Founder, etc.
    - **Not Applicable**: Use this if the seniority level is unclear, ambiguous, or cannot be determined from the text.

    If in doubt, or if no seniority level is clearly indicated, return **Not Applicable**.

    Return **only** the most appropriate label from the list above. Do not explain or add any additional text.

    Job Title:""" + title + """Job Description: """ + description

    #print(prompt)

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    content = response.content[0].text.strip()
    print(content)
    return content


def process_jobs(input_path, output_path):
    # count = 0
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        for line in infile:
            # count += 1
            # if count < 50 or count > 70:
            #     continue
            if not line.strip():
                continue  # skip empty lines

            job = json.loads(line)

            if "job_seniority_level" not in job:
                try:
                    title = job["job_title"]
                    job_description = (
                        job.get("translated_description")
                        or job.get("job_summary")
                        or job.get("description_text")
                        or job.get("job_overview", "")
                    )
                    print(f"Classifying: {title}")
                    job["job_seniority_level"] = get_seniority_level(title, job_description)
                    time.sleep(1)
                except Exception as e:
                    print(f"Failed to classify job '{title}': {e}")
            else:
                print("Already has seniority level")
                print(job["url"])

            outfile.write(json.dumps(job, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    process_jobs(INPUT_FILE, OUTPUT_FILE)

