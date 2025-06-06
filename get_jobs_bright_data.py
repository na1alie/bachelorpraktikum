import requests
import json
import time
from dotenv import load_dotenv
import os

load_dotenv()
BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
file_results = "job_results_bright_data.json"
file_searches = "job_searches.json"

all_jobs = []

# Request jobs and save snapshot ids
url_reqs = "https://api.brightdata.com/datasets/v3/trigger"
headers_reqs = {
	"Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
	"Content-Type": "application/json",
}

params_linkedin = {
	"dataset_id": "gd_lpfll7v5hcqtkxl6l",
	"include_errors": "true",
	"type": "discover_new",
	"discover_by": "keyword",
	"limit_per_input": "5",
}
data_format_linkedin = [{"location":"Munich","keyword":"","country":"","time_range":"","job_type":"","experience_level":"","remote":"","company":""}, {"location":"San Francisco","keyword":"","country":"","time_range":"","job_type":"","experience_level":"","remote":"","company":""}]

params_glassdoor = {
	"dataset_id": "gd_lpfbbndm1xnopbrcr0",
	"include_errors": "true",
	"type": "discover_new",
	"discover_by": "keyword",
	"limit_per_input": "5",
}
data_format_glassdoor = [{"location":"Munich","keyword":"","country":""}, {"location":"San Francisco","keyword":"","country":""}]

params_indeed = {
	"dataset_id": "gd_l4dx9j9sscpvs7no2",
	"include_errors": "true",
	"type": "discover_new",
	"discover_by": "keyword",
	"limit_per_input": "5",
}
data_format_indeed = [{"country":"Germany","domain":"indeed.com","keyword_search":"","location":"Munich","date_posted":"","posted_by":""}, {"country":"US","domain":"indeed.com","keyword_search":"","location":"San Francisco","date_posted":"","posted_by":""}]

params_data_formats = [[params_linkedin, data_format_linkedin], [params_glassdoor, data_format_glassdoor], [params_indeed, data_format_indeed]]


def insert_keyword(data_list, keyword_value):
    for item in data_list:
        if "keyword" in item:
            item["keyword"] = keyword_value
        elif "keyword_search" in item:
            item["keyword_search"] = keyword_value
    return data_list


def wait_for_data_collection(snapshot_id):
	url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
	headers = {"Authorization": f"Bearer {BRIGHT_DATA_API_KEY}"}

	start_time = time.time()
	timeout = 180

	while True:
		response = requests.get(url, headers=headers)
		data = response.json()
		
		status = data.get("status")
		print(f"Status: {status}")

		if status == "ready":
			print("Snapshot is ready!")
			return True

		elif status in ("error", "failed"):
			print("Snapshot failed.")
			return False

		if time.time() - start_time > timeout:
			print("Timeout reached while waiting for completion.")
			return False

		time.sleep(15)


with open(file_searches, 'r', encoding='utf-8') as f:
	searches = json.load(f)

for job_title in searches["job_titles"]:
	for params_data in params_data_formats:
		data = insert_keyword(params_data[1], job_title)

		print(data)

		response = requests.post(url_reqs, headers=headers_reqs, params=params_data[0], json=data)
		print(response.text)
		print(response)
		snapshot_id = response.json()["snapshot_id"]

		# Wait until data collection is completed
		print("wait for data collection")
		success = wait_for_data_collection(snapshot_id)

		# Download snapshots and retrieve job results
		url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
		headers = {
			"Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
		}
		params = {
			"format": "json",
		}

		response = requests.get(url, headers=headers, params=params)
		if response:
			#all_jobs.extend(response.json())
			print("downloaded data")
			with open(file_results, 'r', encoding='utf-8') as f:
				existing_data = json.load(f)
			
			existing_data.extend(response.json())

			with open(file_results, "w", encoding="utf-8") as f:
				json.dump(existing_data, f, ensure_ascii=False, indent=2)
