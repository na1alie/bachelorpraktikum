import openai
import os
import json
from dotenv import load_dotenv
from knowledge_graph_utils import *
from neo4j import GraphDatabase


with open("courses_skills.json", "r", encoding="utf-8") as f:
    courses_skills = json.load(f)

#connect to database

load_dotenv()
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
driver.verify_connectivity()
print("Connected to:", driver.get_server_info())

for course in courses_skills:
    with driver.session() as session:
        session.execute_write(add_course, course["title"])
        for skill in course["skills"]:
            session.execute_write(add_skill, skill)
            session.execute_write(add_teaches_relationship, course["title"], skill)
            print(skill)

# Close driver 
driver.close()



#pre-process courses
with open("content.json", "r", encoding="utf-8") as f:
    courses = json.load(f)

filtered_content = []
for course in courses:
    inhalt = course.get("inhalt", "").strip()
    lernergebnisse = course.get("lernergebnisse", "").strip()
    anmerkung = course.get("anmerkung", "").strip()

    exclude_due_to_anmerkung = (
        anmerkung == "Die Lehrveranstaltungen werden nicht mehr angeboten." or
        anmerkung == "Dieses Modul wird nicht mehr angeboten!" or
        anmerkung == "Wird nicht mehr angeboten." or
        anmerkung.startswith("Das Modul wird nicht mehr angeboten.")
    )

    if (inhalt or lernergebnisse) and not exclude_due_to_anmerkung:
        filtered_content.append(course)

# Write the filtered result to a new file
with open("filtered_content.json", "w", encoding="utf-8") as f:
    json.dump(filtered_content, f, ensure_ascii=False, indent=2)

print(f"{len(filtered_content)} courses written to 'filtered_content.json'")
print(f"{len(courses)} courses in content.json'")

#OPENAI
load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))

courses_skills = []

with open("courses.json", "r", encoding="utf-8") as f:
    gefiltert = json.load(f)

for course in gefiltert:
    print(course["name"])
    prompt = f"""
    You are an expert in curriculum design and skills mapping.

    Extract only the relevant **skills** mentioned in the course description below. 
    Extract only high-level, commonly used skills from this course. 
    Use short, normalized names (e.g., 'Java' instead of 'Java programming'). 
    Avoid niche or overly specific terms.
    Don´t extract more than 10 skills.
    Translate every skill to english.
    Skills DO NOT require indicators such as "experience in/with ...", "understanding of ..." or "interest in..."

    Return the skills as a **Python list of strings**, and do not include any explanation or formatting beyond that.

    Course description:
    \"\"\"{course}\"\"\"
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
        )

    skills_raw = response.choices[0].message.content.strip()
    print(skills_raw)

    try:
        skills_list = eval(skills_raw)
        courses_skills.append({
        "title": course["name"],
        "kennung": course["kennung"],
        "skills": skills_list 
        })
    except Exception as e:
        print(f"Could not parse skills for: {course['title']}")
        
    with open("courses_skills.json", "w", encoding="utf-8") as f:
        json.dump(courses_skills, f, ensure_ascii=False, indent=2)