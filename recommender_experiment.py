from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory
from neo4j import GraphDatabase
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import torch
from pykeen.models import TransE
import os
from dotenv import load_dotenv

# Load triples factory
tf = TriplesFactory.from_path_binary('trained_triples_factory')

# Reconstruct the model architecture
model = TransE(triples_factory=tf)

# Load trained weights
model.load_state_dict(torch.load('transe_model.pt'))
model.eval()

# --- Configuration ---
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# --- Connect to Neo4j ---
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- Candidate Filtering ---
def filter_courses_by_job(job_title):
    query = """
    MATCH (j:Job {name: $job_title})-[:REQUIRES]->(s:Skill)<-[:TEACHES]-(c:Course)
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
def recommend_courses(job_title, top_n=10):
    candidates = filter_courses_by_job(job_title)
    job_emb = get_entity_embedding(job_title)
    print(candidates)


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

# --- Example ---
print(recommend_courses("Junior Developer"))
