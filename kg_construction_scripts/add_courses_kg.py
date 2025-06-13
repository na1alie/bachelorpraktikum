import openai
import os
import json
from dotenv import load_dotenv
from knowledge_graph_utils import *
from neo4j import GraphDatabase


load_dotenv()

#connect to database
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
driver.verify_connectivity()
print("Connected to:", driver.get_server_info())

#pre-process courses
with open("courses_skills.json", "r", encoding="utf-8") as f:
    courses_skills = json.load(f)

for course in courses_skills:
        with driver.session() as session:
            session.execute_write(add_course, f'{course["kennung"]}: {course["name"]}')
            for skill in course["skills"]:
                session.execute_write(add_skill, skill)
                session.execute_write(add_teaches_relationship,f'{course["kennung"]}: {course["name"]}', skill)

# Close driver 
driver.close()
