import anthropic
import json
import os
from dotenv import load_dotenv
from knowledge_graph_utils import *
from neo4j import GraphDatabase

load_dotenv()
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
directory = "../job_offers"

# Loop through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".txt"):
        file_path = os.path.join(directory, filename)

        with open(file_path, 'r', encoding='utf-8') as f:
            offer = f.read()

        prompt = """<instructions> Extract only the job title and the list of required skills from the following job description.
        Do not include any explanations, reasoning, or extra text. 
        Steps:
        1. Identify the job title
        2. Find skills in the skills section AS WELL AS the description text
        3. TRANSLATE EVERYTHING TO ENGLISH
        </instructions>
        <output_format>
        ```json
        {
        "Job Title": "string, the name of the job title, keep general",
        "Skills": ["string, a comma-separated list of required skills as individual items in a list, NO GERMAN TERMS""]
        }
        ```
        </output_format>
        <constraints>
        * Skills DO NOT require indicators such as "experience in/with ...", "understanding of ..." or "interest in..."
        * Use short and normalized names for skills (e.g. "Java" instead of "Java programming")
        * DO NOT ouput generic skills such as "Maths", "Informatics", "Programming", "Physics"
        * Extract only the core job title without any year, experience level, seniority of time-based indicators
        * DO NOT include words or numbers like "2025", "Senior", "Junior", "Entry-level", "Mid-level", "Level 2", or similar qualifiers in job titles
        * IMPORTANT!!! NO GERMAN WORDS
        </constraints>
        <job_description>
        """ + offer + """
        </job_description>"""

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        jsonResponse = response.content[0].text
        cleanResponse = jsonResponse.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(cleanResponse)
        print(data)

        #connect to database
        driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
        driver.verify_connectivity()
        print("Connected to:", driver.get_server_info())
        
        with driver.session() as session:
            session.write_transaction(add_job, data["Job Title"])
            for skill in data["Skills"]:
                session.write_transaction(add_skill, skill)
                session.write_transaction(add_requires_relation, data["Job Title"], skill)