from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import pickle
from pykeen.triples import TriplesFactory
import torch
from pykeen.models import TransE
import streamlit as st

#TEST
#SentenceTransformer for finding similair jobs, pykeen for finding courses for each job

# Load SentenceTransformer model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Load triples factory
tf = TriplesFactory.from_path_binary('trained_triples_factory')

# Reconstruct the model architecture
model = TransE(triples_factory=tf)

# Load trained weights
model.load_state_dict(torch.load('transe_model.pt'))
model.eval()

# --- Configuration ---
dotenv_path = os.path.join(os.path.dirname(__file__), 'kg_construction_scripts', '.env')
load_dotenv(dotenv_path=dotenv_path)
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- Candidate Filtering ---
def filter_courses_by_job(job_title):
    query = """
    MATCH (j:Job {name: $job_title})-[:requires]->(s:Skill)<-[:TEACHES]-(c:Course)
    RETURN DISTINCT c.name AS course
    """
    with driver.session() as session:
        result = session.run(query, job_title=job_title)
        return [record["course"] for record in result]

def get_entity_embedding(label):
    entity_id = tf.entity_to_id.get(label)
    if entity_id is None:
        raise ValueError(f"Entity '{label}' not found in the triples.")
    embedding = model.entity_representations[0](torch.tensor([entity_id])).detach().numpy()
    return embedding

# --- Embedding-Based Ranking ---
def recommend_courses(job_title, top_n=2):
    candidates = filter_courses_by_job(job_title)
    job_emb = get_entity_embedding(job_title)


    course_scores = []
    for course in candidates:
        try:
            course_emb = get_entity_embedding(course)
            sim = cosine_similarity(course_emb, job_emb)[0][0]
            course_scores.append((course, sim))
        except KeyError:
            continue  # In case a node is missing in the embeddings

    ranked = sorted(course_scores, key=lambda x: x[1], reverse=True)
    return [(course, score) for course, score in ranked[:top_n]]



def load_precomputed_embeddings():
    with open("job_embeddings.pkl", "rb") as f:
        all_jobs, job_embeddings = pickle.load(f)
    return all_jobs, job_embeddings

def find_closest_jobs(input_title, all_job_titles, job_title_embeddings, top_k=3):
    input_emb = embedder.encode([input_title], convert_to_numpy=True)
    similarities = cosine_similarity(input_emb, job_title_embeddings)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]
    return [(all_job_titles[i], similarities[i]) for i in top_indices]


def recommend_top_jobs(user_input):
    all_job_titles, job_title_embeddings = load_precomputed_embeddings()
    closest_jobs = find_closest_jobs(user_input, all_job_titles, job_title_embeddings, top_k=3)
    return closest_jobs




st.title("Curriculum Mapping Tool")
st.write("Enter a job title to discover relevant courses:")
job_input = st.text_input("Job Title", placeholder="e.g. Data Scientist")

if st.button("Recommend Courses"):
    if not job_input.strip():
        st.warning("Please enter a valid job title.")
    else:
        with st.spinner("Looking up recommendations..."):
            try:
                top_jobs = recommend_top_jobs(job_input)
                if not top_jobs:
                    st.error("No similar jobs found.")
                else:
                    st.success(f"Top 3 jobs similar to: **{job_input}**")
                    for job, score in top_jobs:
                        st.subheader(f"Similar Job: {job} (Similarity: {score:.4f})")
                        courses = recommend_courses(job, top_n=3)
                        if not courses:
                            st.warning("No course recommendations found for this job.")
                        else:
                            st.write("Top Recommended Courses:")
                            for course_name, course_score in courses:
                                st.write(f"- {course_name} (Similarity: {course_score:.4f})")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")




