import json
import requests
from langdetect import detect, LangDetectException
from dotenv import load_dotenv
import os

load_dotenv()
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"
TARGET_LANG = "EN"

DESCRIPTION_FIELDS = ["job_summary", "job_overview", "description_text"]

def detect_description_field(job_dict):
    for key in DESCRIPTION_FIELDS:
        if key in job_dict and job_dict[key]:
            return key
    return None

def is_german(text):
    try:
        return detect(text) == "de"
    except LangDetectException:
        return False

def translate_text(text):
    params = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": TARGET_LANG,
    }
    response = requests.post(DEEPL_API_URL, data=params)
    response.raise_for_status()
    return response.json()["translations"][0]["text"]

def process_jobs(jobs):
    processed = []
    for job in jobs:
        field = detect_description_field(job)
        if not field:
            print("No description field found, skipping.")
            continue
        else:
            print("Found:", field)

        text = job[field]
        try:
            if is_german(text):
                translated = translate_text(text)
                job["translated_description"] = translated
        except Exception as e:
            print(f"Error processing job ID {job.get('job_posting_id', 'unknown')}: {e}")
        processed.append(job)
    return processed


# Load your data (replace with your input file or structure)
with open("job_results_bright_data.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

processed_jobs = process_jobs(jobs)

# Save the updated jobs to a new JSON file
with open("translated_jobs_bright_data.json", "w", encoding="utf-8") as f:
    json.dump(processed_jobs, f, ensure_ascii=False, indent=2)