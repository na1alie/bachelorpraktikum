import json
import os
from dotenv import load_dotenv
from knowledge_graph_utils import *
from neo4j import GraphDatabase

load_dotenv()
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

input_file = "../jobs_titles_deduplicated.jsonl"

#connect to database
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
driver.verify_connectivity()
print("Connected to:", driver.get_server_info())

with open(input_file, "r", encoding="utf-8") as f_in:
    for line_number, line in enumerate(f_in, start=1):
        if line_number < 479:
            continue
        line = line.strip()
        if not line:
            continue
        try:
            job = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Skipping invalid JSON on line {line_number}: {e}")
            continue

        with driver.session() as session:
            session.write_transaction(add_job, job["deduplicated_title"])
            for skill in job["deduplicated_skills"]:
                session.write_transaction(add_skill, skill)
                session.write_transaction(add_requires_relation, job["deduplicated_title"], skill)
        
        print("Added", job["deduplicated_title"])