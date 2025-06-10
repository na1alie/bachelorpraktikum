import spacy
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor
import json
import anthropic
import os
from dotenv import load_dotenv
import re

load_dotenv()
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

jobs_file = "translated_jobs_bright_data.json"
output_file = "experiment.jsonl"


def clean_description(text: str) -> str:
    # Add a period before capitalized words following lowercase words, unless already ending in punctuation
    return re.sub(r'(?<=[a-z]) (?=[A-Z])', '. ', text)


with open(jobs_file, "r", encoding="utf-8") as f:
    all_jobs = json.load(f)

jobs_sample = all_jobs[:10]

nlp = spacy.load("en_core_web_lg")
skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

for job in jobs_sample:

    # Skill extraction using skillNer 
    job_description = (
        job.get("translated_description")
        or job.get("job_summary")
        or job.get("description_text")
        or job.get("job_overview", "")
    )

    skillNer = False

    if isinstance(job_description, str) and job_description.strip():
        try:
            annotations = skill_extractor.annotate(job_description)
            skill_phrases = [ann["doc_node_value"] for ann in annotations["results"]["full_matches"]]
            filtered_skills = [m["doc_node_value"] for m in annotations["results"].get("ngram_scored", []) if m.get("score", 0) == 1.0]

            job["skills_skillNer_full"] = skill_phrases
            job["skills_skillNer_scored"] = filtered_skills

            skillNer = True

        except Exception as e:
            print(f"Skipping due to Error: {e}")

    # Skill extraction using LLM
    # prompt = """<instructions> 
    # Your task is to extract ONLY THE RELEVANT SKILLS from the following job offers. Focus strictly on **general, high-level, transferable skills** commonly recognized in academia or industry.
    # Extract a list of at most 10 required hard technical skills from the following job description.
    # Do not include any explanations, reasoning, or extra text. 
    # </instructions>
    # <output_format>
    # ```json
    # {
    # "Skills": ["string, a comma-separated list of required skills as individual items in a list""]
    # }
    # ```
    # </output_format>
    # <constraints>
    # * Skills DO NOT require indicators such as "experience in/with ...", "understanding of ..." or "interest in..."
    # * Use short and normalized names for skills (e.g. "Java" instead of "Java programming")
    # * DO NOT ouput generic skills such as "Maths", "Informatics", "Programming", "Physics"
    # * DO NOT only output frameworks or programming languages, also include concepts to understand
    # </constraints>
    # <job_description>
    # """ + job_description + """
    # </job_description>
    # <skillNer_result>
    # </skillNer_result>
    # """

    prompt = """<instructions> 
    Your task is to extract ONLY THE RELEVANT SKILLS from the following job offers. Focus strictly on **general, high-level, transferable technical skills** commonly recognized in academia or industry.

    You may be provided two sources of skills:
    1. The raw job description text.
    2. A preliminary list of skills automatically extracted by SkillNer (an NLP skill extraction module).

    Note: The SkillNer extracted skills may sometimes be empty or missing. If no SkillNer skills are provided, extract the skills solely from the job description.

    Using both when available, generate a list of AT MOST 10 required hard technical skills that are truly relevant and required by the job. You must critically assess the SkillNer extracted skills and remove any irrelevant or non-technical skills (e.g., "yoga", "team outings", "company culture"). Only keep those skills that make sense as core technical skills necessary for the role.

    Importantly, do NOT restrict yourself to only the skills extracted by SkillNer. If there are other relevant and clearly required skills in the job description, include them as well.

    Do not include any explanations, reasoning, or extra text.

    </instructions>
    <output_format>
    ```json
    {
    "Skills": ["string, a comma-separated list of required skills as individual items in a list"]
    }
    ```
    </output_format>
    <constraints>
    * Skills DO NOT require indicators such as "experience in/with ...", "understanding of ..." or "interest in..."
    * Use short and normalized names for skills (e.g. "Java" instead of "Java programming")
    * DO NOT ouput generic skills such as "Maths", "Informatics", "Programming", "Physics"
    * DO NOT only output frameworks or programming languages, also include concepts to understand
    </constraints>
    <job_description>
    """ + job_description + """
    </job_description>
    <skillNer_result>
    """ + (str(job["skills_skillNer_full"]) + str(job["skills_skillNer_scored"]) if skillNer else "") + """
    </skillNer_result>
    """

    print(prompt)

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
    skill_data = json.loads(cleanResponse)

    job["skills_LLM"] = skill_data.get("Skills", [])

    # Save the updated job list with extracted skills
    with open(output_file, "a", encoding="utf-8") as f:
        json.dump(job, f, indent=2, ensure_ascii=False)