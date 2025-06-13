from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory
from neo4j import GraphDatabase
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
from dotenv import load_dotenv
import torch

# --- Configuration ---
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# --- Connect to Neo4j ---
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def fetch_all_triples():
    query = """
    MATCH (h)-[r]->(t)
    RETURN h.name AS head, type(r) AS relation, t.name AS tail
    """
    with driver.session() as session:
        result = session.run(query)
        triples = [(record["head"], record["relation"], record["tail"]) for record in result]
    return triples

# --- Build TriplesFactory from Neo4j triples ---
triples = fetch_all_triples()
tf = TriplesFactory.from_labeled_triples(np.array(triples))
train_tf, test_tf, val_tf = tf.split([0.8, 0.1, 0.1])

# --- Train embedding model ---
result = pipeline(
    model='TransE',
    training=train_tf,
    testing=test_tf,
    validation=val_tf,
    training_kwargs=dict(num_epochs=100),
)
model = result.model

# Save
torch.save(model.state_dict(), 'transe_model.pt')
tf.to_path_binary('trained_triples_factory')
