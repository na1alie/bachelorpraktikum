import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import quote_plus

file_searches = 'job_searches.json'
file_results = 'job_results.json'


def search_jobs_glassdoor_for(title):
    base_url = "https://www.glassdoor.com/Job/jobs.htm"
    list_url = f"{base_url}?q={quote_plus(title)}&l=Germany&p=1"
    
    jobs = []
    return jobs


def search_jobs_linkedin_for(title):
    list_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords="+quote_plus(title)+"&location=Germany&geoId=&trk=public_jobs_jobs-search-bar_search-submit&start=50"

    response = requests.get(list_url)

    list_data = response.text
    list_soup = BeautifulSoup(list_data, 'html.parser')
    page_jobs = list_soup.find_all('li')

    jobs = []

    for job in page_jobs:
        info = {}
        base_card_div = job.find("div", {"class": "base-card"})
        if base_card_div:
            job_title = base_card_div.find("h3", {"class": "base-search-card__title"}).text.strip()
            info["title"] = job_title
            company = base_card_div.find("h4", {"class": "base-search-card__subtitle"}).text.strip()
            info["company"] = company
            location = base_card_div.find("span", {"class": "job-search-card__location"}).text.strip()
            info["location"] = location
            job_id = base_card_div.get("data-entity-urn").split(":")[-1]
            info["job_id"] = job_id
            jobs.append(info)

    print(jobs)

    for job_info in jobs:
        job_id = job_info["job_id"]
        job_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        job_response = requests.get(job_url)
        job_data = job_response.text
        job_soup = BeautifulSoup(job_data, 'html.parser')
        job_description = job_soup.find("div", {"class": "show-more-less-html__markup"})
        job_description = job_description.text.strip() if job_description else ""
        job_info["description"] = job_description
    
    return jobs


with open(file_searches, 'r', encoding='utf-8') as f:
    data = json.load(f)

for job_title in data["job_titles"]:
    if job_title not in data or not data[job_title]:
        results = search_jobs_linkedin_for(job_title)
        data[job_title] = results
        # if os.path.exists(file_results):
        #     with open(file_results, "r", encoding="utf-8") as f:
        #         existing_data = json.load(f)
        # else:
        #     existing_data = {"jobs": []}

        # existing_data["jobs"].extend()

        with open(file_searches, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)