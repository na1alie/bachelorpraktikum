import anthropic
import os
import json
from dotenv import load_dotenv

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_path, "kg_construction_scripts", ".env")
load_dotenv(env_path)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


with open("/home/natalie/Bachelorprojekt/course_skill_extraction/courses_department_cs.json", "r", encoding="utf-8") as f:
    filtered_content = json.load(f)


courses_skills = []

for course in filtered_content:
    print(course["name"])
    prompt = f"""
    You are an expert in curriculum design and skills mapping.


    Your task is to extract **only the relevant skills** from the following course description. Focus strictly on **general, high-level, transferable skills** commonly recognized in academia or industry.

    **Instructions:**
    - Return **at most fifteen** distinct skills
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

    except Exception as e:
        print(f"Could not parse skills for: {course['title']}")
        
    with open("/home/natalie/Bachelorprojekt/course_skill_extraction/course_anthropic_skills.json", "w") as outfile:
        json.dump(courses_skills, outfile, indent=4, ensure_ascii=False)
