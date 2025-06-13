#import openai
import anthropic
import os
import json
from dotenv import load_dotenv
from knowledge_graph_utils import *
from neo4j import GraphDatabase

#OPENAI
load_dotenv()
#client = openai.OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

#connect to database
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
driver.verify_connectivity()
print("Connected to:", driver.get_server_info())

#pre-process courses
with open("../courses_cs_bsc/cs_bsc_courses_info.json", "r", encoding="utf-8") as f:
    courses = json.load(f)

filtered_content = []
for course in courses:
    inhalt = course.get("inhalt", "").strip()
    lernergebnisse = course.get("lernergebnisse", "").strip()
    name = course.get("name", "").strip()
    kennung = course.get("kennung", "").strip()
    anmerkung = course.get("anmerkung", "").strip()

    exclude_due_to_anmerkung = (
        name == "" or
        kennung == "" or
        anmerkung == "Die Lehrveranstaltungen werden nicht mehr angeboten." or
        anmerkung == "Dieses Modul wird nicht mehr angeboten!" or
        anmerkung == "Wird nicht mehr angeboten." or
        anmerkung.startswith("Das Modul wird nicht mehr angeboten.")
    )

    if (inhalt or lernergebnisse) and not exclude_due_to_anmerkung:
        filtered_content.append(course)



with open("filtered_cs_content.json", "w", encoding="utf-8") as f:
    json.dump(filtered_content, f, ensure_ascii=False, indent=2)
        

# print(f"{len(filtered_content)} courses written to 'filtered_content.json'")
# print(f"{len(courses)} courses in content.json'")

courses_skills = []

filtered_content_2 = filtered_content[2:]

for course in filtered_content_2:
    print(course["name"])
    prompt = f"""
    You are an expert in curriculum design and skills mapping.


    Your task is to extract **only the relevant skills** from the following course description. Focus strictly on **general, high-level, transferable skills** commonly recognized in academia or industry.

    **Instructions:**
    - Return **at most ten** distinct skills
    - Use **normalized, concise terms** (e.g., 'Java' not 'Java programming').
    - Each skill should consist of **one to three words maximum**.
    - Avoid niche, overly specific terms.
    - Translate all skills to **English**, even if the input is in another language.
    - Do **not** include qualifiers like "experience with", "understanding of", or "interest in".
    - Do **not** ouput generic skills such as "Mathematics", "Informatics", "Physics"

    **Output format:**
    Return a valid **Python list of strings**, and **nothing else**—no explanation, no notes, no headings.

    Course description:
    \"\"\"{course}\"\"\"
    """

    # response = client.chat.completions.create(
    #     model="gpt-4",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0
    #     )
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    skills_raw = response.content[0].text.strip()
    print(skills_raw)

    try:
        skills_list = eval(skills_raw)
        courses_skills.append({
        "title": course["name"],
        "kennung": course["kennung"],
        "skills": skills_list 
        })
        with driver.session() as session:
            session.execute_write(add_course, f'{course["kennung"]}: {course["name"]}')
            for skill in skills_list:
                session.execute_write(add_skill, skill)
                session.execute_write(add_teaches_relationship,f'{course["kennung"]}: {course["name"]}', skill)
        print("Added course:", course["kennung"], course["name"])

    except Exception as e:
        print(f"Could not parse skills for: {course['title']}")
        
    with open("courses_skills.json", "w", encoding="utf-8") as f:
        json.dump(courses_skills, f, ensure_ascii=False, indent=2)


# Close driver 
driver.close()
