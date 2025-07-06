from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import numpy as np
import pickle
import time

load_dotenv()
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


# --- Neo4j queries ---
def get_required_skills(job_title):
    query = """
    MATCH (j:Job {name: $job_title})-[:REQUIRES]->(s:Skill)
    RETURN s.name AS skill
    """
    with driver.session() as session:
        result = session.run(query, job_title=job_title)
        return [record["skill"] for record in result]

def get_relevant_courses_with_skills(job_title):
    query = """
        MATCH (j:Job {name: $job_title})-[:REQUIRES]->(s:Skill)<-[:TEACHES]-(c:Course)
        WITH c, collect(DISTINCT s.name) AS required_skills
        MATCH (c)-[:TEACHES]->(sk:Skill)
        RETURN c.name AS course, collect(DISTINCT sk.name) AS all_skills, required_skills
    """
    with driver.session() as session:
        result = session.run(query, job_title=job_title)
        return [(record["course"], record["all_skills"], record["required_skills"]) for record in result]

def fetch_all_job_titles():
    query = "MATCH (j:Job) RETURN DISTINCT j.name AS name"
    with driver.session() as session:
        result = session.run(query)
        return [record["name"] for record in result if record["name"]]

def find_closest_jobs(input_title, all_job_titles, job_title_embeddings, top_k=3):
    # all_job_titles = fetch_all_job_titles()
    # job_title_embeddings = embedder.encode(all_job_titles, convert_to_numpy=True)
    input_emb = embedder.encode([input_title], convert_to_numpy=True)
    similarities = cosine_similarity(input_emb, job_title_embeddings)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]
    return [(all_job_titles[i], similarities[i]) for i in top_indices]

def recommend_courses_semantic(job_title, top_n=10):
    load_start = time.time()
    all_job_titles, job_title_embeddings, all_skills, skill_embeddings = load_precomputed_embeddings()
    load_end = time.time()
    skill_to_embedding = dict(zip(all_skills, skill_embeddings))

    jobs_start = time.time()
    closest_jobs = find_closest_jobs(job_title, all_job_titles, job_title_embeddings)
    jobs_end = time.time()
    print(closest_jobs)

    course_suggestions = []

    courses_start = time.time()
    alpha = 0.6

    for job, job_score in closest_jobs:
        job_skills = get_required_skills(job)
        job_skill_embeddings = [
            skill_to_embedding[skill]
            for skill in job_skills
            if skill in skill_to_embedding  # in case some skill is missing from precomputed
        ]

        relevant_courses_start = time.time()
        all_courses = get_relevant_courses_with_skills(job)
        relevant_courses_end = time.time()
        print("Query time:", relevant_courses_end - relevant_courses_start)
        ranked_courses = []

        for course_name, course_skills, required_skills in all_courses:
            if not course_skills:
                continue
            course_skill_embeddings = [
                skill_to_embedding[skill]
                for skill in course_skills
                if skill in skill_to_embedding  # in case some skill is missing from precomputed
             ]

            sim_matrix = cosine_similarity(job_skill_embeddings, course_skill_embeddings)
            avg_score = np.mean(sim_matrix)

            final_score = alpha * job_score + (1 - alpha) * avg_score
            ranked_courses.append((course_name, avg_score, final_score, required_skills))

        ranked_courses.sort(key=lambda x: x[1], reverse=True)
        course_suggestions.append((job, ranked_courses[:top_n]))

    courses_end = time.time()
    print("Loading time:", load_end - load_start, "Job starting points time:", jobs_end - jobs_start, "Course recs time:", courses_end - courses_start)
    return course_suggestions

def flatten_and_deduplicate_courses(top_courses, max_courses=10):
    course_scores = {}

    for _, course_list in top_courses:
        for course_name, _, final_score, _ in course_list:
            # Keep the max score if duplicate course_name
            if course_name not in course_scores or final_score > course_scores[course_name]:
                course_scores[course_name] = final_score

    # Sort courses by score descending
    sorted_courses = sorted(course_scores.items(), key=lambda x: x[1], reverse=True)

    # Take top max_courses courses
    top_courses_flat = [(course, score) for course, score in sorted_courses[:max_courses]]
    return top_courses_flat

top_courses = recommend_courses_semantic("Computer Vision Engineer")
for job_title, course_list in top_courses:
    print("Courses recommended for:", job_title)
    for course, course_score, final_score, required_skills in course_list:
        print(f"{course}: course score {course_score:.4f}, weighted score {final_score:.4f} - teaches:", required_skills)
    print()

top_courses_flat = flatten_and_deduplicate_courses(top_courses)
for course, score in top_courses_flat:
    print(f"{course}: {score:.4f}")

print()
