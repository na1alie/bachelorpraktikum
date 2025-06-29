from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import numpy as np
import pickle
import anthropic

dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'kg_construction_scripts', '.env')
load_dotenv(dotenv_path=dotenv_path)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- Load SentenceTransformer model ---
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def load_precomputed_embeddings():
    with open("job_embeddings.pkl", "rb") as f:
        all_jobs, job_embeddings = pickle.load(f)
    with open("skill_embeddings.pkl", "rb") as f:
        all_skills, skill_embeddings = pickle.load(f)
    return all_jobs, job_embeddings, all_skills, skill_embeddings

################################# jobs #######################################################

def find_closest_jobs(input_title, all_job_titles, job_title_embeddings, top_k=3):
    input_emb = embedder.encode([input_title], convert_to_numpy=True)
    similarities = cosine_similarity(input_emb, job_title_embeddings)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]
    return [(all_job_titles[i], similarities[i]) for i in top_indices]


def get_job_description_and_skills(job_title):
    query = """
    MATCH (j:Job {name: $job_title})
    OPTIONAL MATCH (j)-[:requires]->(s:Skill)
    RETURN j.description AS description, collect(DISTINCT s.name) AS skills
    """
    with driver.session() as session:
        result = session.run(query, job_title=job_title)
        record = result.single()
        if record:
            return {
                "description": record["description"] or "No description provided.",
                "skills": record["skills"] or []
            }
        else:
            return None
        

def summarize_job_claude(job_title, job_info):
    prompt = f"""
    Job Title: {job_title}

    Description:
    {job_info['description']}

    Required Skills:
    {', '.join(job_info['skills'])}

    Please summarize this job in 2-3 clear sentences as if explaining to a student.
    """

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=300,
        temperature=0.5,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.content[0].text.strip()

# if can selects "All Levels" or one or more of the seniority levels in KG 
def get_jobs_by_seniority(seniority_levels):
    if "All Levels" in seniority_levels:
        query = "MATCH (j:Job) RETURN j.name AS name"
        params = {}
    else:
        query = """
        MATCH (j:Job)
        WHERE j.seniority_level IN $levels
        RETURN j.name AS name
        """
        params = {"levels": seniority_levels}

    with driver.session() as session:
        result = session.run(query, **params)
        return [record["name"] for record in result if record["name"]]
    

# 7 different seniority levels in KG: "Mid-Senior level", "Entry Level", "Internship", "Not Applicable", "Senior",, "Associate", "Director"
# Step 1: user input: job title, selection of Seniority Levels, Output: Top K Jobs with Claude Summary
def suggest_jobs(job = "Data Scientist", seniority_levels =  ["Director", "Founding ML Engineer", "All Levels"]):
    filtered_jobs = get_jobs_by_seniority(seniority_levels)
    #print(len(filtered_jobs))
    if not filtered_jobs:
        print(f"No jobs found for level: {seniority_levels}")
        return
    all_job_titles, job_title_embeddings, all_skills, skill_embeddings = load_precomputed_embeddings()

    filtered_indices = [i for i, title in enumerate(all_job_titles) if title in filtered_jobs]
    if not filtered_indices:
        print(f"No embeddings found for filtered jobs!")
        return


    filtered_titles = [all_job_titles[i] for i in filtered_indices]
    filtered_embeddings = job_title_embeddings[filtered_indices]

    # Find closest jobs in filtered set
    closest_jobs = find_closest_jobs(job, filtered_titles, filtered_embeddings)
    for job_title, similarity in closest_jobs:
        job_info = get_job_description_and_skills(job_title)
        print(f"\n{job_title} (Similarity: {similarity:.4f})")
        if job_info:
            print("Description:", job_info["description"])
            print("Skills:", ", ".join(job_info["skills"]))
            #summary = summarize_job_claude(job_title, job_info)   ## give claude summary of top k courses back to user
            #print("Summary:", summary) 
        else:
            print("No job info found.")

suggest_jobs()


##################################### courses ##############################################################

def get_required_skills(job_title):
    query = """
    MATCH (j:Job {name: $job_title})-[:requires]->(s:Skill)
    RETURN s.name AS skill
    """
    with driver.session() as session:
        result = session.run(query, job_title=job_title)
        return [record["skill"] for record in result]

def get_relevant_courses_with_skills(job_title, languages, module_levels):
    query = """
        MATCH (j:Job {name: $job_title})-[:requires]->(s:Skill)<-[:TEACHES]-(c:Course)
        WHERE c.sprache IN $languages
          AND c.modulniveau IN $module_levels
        WITH c, collect(DISTINCT s.name) AS required_skills
        MATCH (c)-[:TEACHES]->(sk:Skill)
        RETURN c.name AS course, collect(DISTINCT sk.name) AS all_skills, required_skills
    """
    with driver.session() as session:
        result = session.run(
            query,
            job_title=job_title,
            languages=languages,
            module_levels=module_levels
        )
        return [
            (record["course"], record["all_skills"], record["required_skills"])
            for record in result
        ]


def recommend_courses_semantic(job_title, language, module_level, top_n=10):
    _, _, all_skills, skill_embeddings = load_precomputed_embeddings()
    skill_to_embedding = dict(zip(all_skills, skill_embeddings))

    job_skills = get_required_skills(job_title)
    job_skill_embeddings = [
        skill_to_embedding[skill]
        for skill in job_skills
        if skill in skill_to_embedding
    ]

    all_courses = get_relevant_courses_with_skills(job_title, language, module_level)
    ranked_courses = []

    for course_name, course_skills, required_skills in all_courses:
        if not course_skills:
            continue
        course_skill_embeddings = [
            skill_to_embedding[skill]
            for skill in course_skills
            if skill in skill_to_embedding
        ]

        sim_matrix = cosine_similarity(job_skill_embeddings, course_skill_embeddings)
        avg_score = np.mean(sim_matrix)

        ranked_courses.append((course_name, avg_score, required_skills))

    ranked_courses.sort(key=lambda x: x[1], reverse=True)
    return [(job_title, ranked_courses[:top_n])]


def get_course_description(course_title):
    query = """
    MATCH (c:Course {name: $course_title})
    RETURN 
      c.inhalt AS inhalt,
      c.lernergebnisse AS lernergebnisse,
      c.modulniveau AS modulniveau,
      c.sprache AS sprache,
      c.url AS url
    """
    with driver.session() as session:
        result = session.run(query, course_title=course_title)
        record = result.single()
        if record:
            return {
                "inhalt": record["inhalt"],
                "lernergebnisse": record["lernergebnisse"],
                "modulniveau": record["modulniveau"],
                "sprache": record["sprache"],
                "url": record["url"]
            }
        else:
            return None
        
def summarize_course_claude(course_title, course_info):
    prompt = f"""
    Course Title: {course_title}

    Content:
    {course_info['inhalt']}
    {course_info["lernergebnisse"]}

   

    Please summarize this course in 2-3 clear sentences as if explaining to a student.
    """

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=300,
        temperature=0.5,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.content[0].text.strip()


# 3 different language properties in KG: "Englisch", "Deutsch/Englisch", "Deutsch"
# 3 different modulelevel prperites in KG: "Bachelor", "Bachelor/Master", "Master"
# After Step 1, Step 2: user selects one of suggestet jobs, select language, modullevel 
# Output: Top K Courses with Claude Summary, todo: predict potential skill gaps, give back url? skills in common with job?
top_courses = recommend_courses_semantic("Data Scientist",["Englisch", "Deutsch/Englisch", "Deutsch"], ["Bachelor", "Bachelor/Master", "Master"] )
for job_title, course_list in top_courses:
    print("Courses recommended for:", job_title)
    for course, course_score,  required_skills in course_list:
        print(f"{course}: course score {course_score:.4f}, - teaches:", required_skills)
        course_info = get_course_description(course)
        #print(course_info)
        #summary = summarize_course_claude(course, course_info)   ## give summary of top k courses back to user
        #print("Summary:", summary)
    print()






