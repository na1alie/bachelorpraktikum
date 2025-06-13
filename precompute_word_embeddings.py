from sentence_transformers import SentenceTransformer
import pickle
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

st_model = SentenceTransformer("all-MiniLM-L6-v2")

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

# --- Fetch all job titles ---
def fetch_all_job_titles():
    query = "MATCH (j:Job) RETURN DISTINCT j.name AS name"
    with driver.session() as session:
        result = session.run(query)
        return [record["name"] for record in result if record["name"]]

# --- Fetch all skills ---
def fetch_all_skills():
    query = "MATCH (s:Skill) RETURN DISTINCT s.name AS name"
    with driver.session() as session:
        result = session.run(query)
        return [record["name"] for record in result if record["name"]]

def precompute_and_save_embeddings():
    all_jobs = fetch_all_job_titles()
    all_skills = fetch_all_skills()

    job_embeddings = st_model.encode(all_jobs, convert_to_numpy=True)
    skill_embeddings = st_model.encode(all_skills, convert_to_numpy=True)

    with open("job_embeddings.pkl", "wb") as f:
        pickle.dump((all_jobs, job_embeddings), f)

    with open("skill_embeddings.pkl", "wb") as f:
        pickle.dump((all_skills, skill_embeddings), f)

    print("Precomputed and saved job and skill embeddings.")

precompute_and_save_embeddings()