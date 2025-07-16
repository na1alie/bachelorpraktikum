from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import hdbscan
import pickle
from collections import defaultdict
import umap.umap_ as umap
import np
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from collections import Counter
import json

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Fetch all skills required by any job
def fetch_all_job_skills():
    query = """
    MATCH (:Job)-[:REQUIRES]->(s:Skill)
    RETURN DISTINCT s.name AS name
    """
    with driver.session() as session:
        result = session.run(query)
        return [record["name"] for record in result if record["name"]]

# Fetch all skills taught by any course
def fetch_all_course_skills():
    query = """
    MATCH (:Course)-[:TEACHES]->(s:Skill)
    RETURN DISTINCT s.name AS name
    """
    with driver.session() as session:
        result = session.run(query)
        return [record["name"] for record in result if record["name"]]


# --- Load SentenceTransformer model ---
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def load_precomputed_embeddings():
    with open("../skill_embeddings.pkl", "rb") as f:
        all_skills, skill_embeddings = pickle.load(f)
    return all_skills, skill_embeddings

all_skills, skill_embeddings = load_precomputed_embeddings()

job_skills = fetch_all_job_skills()
course_skills = fetch_all_course_skills()

reduced_embeddings = umap.UMAP(n_components=100, n_neighbors=15, min_dist=0.0, metric='cosine').fit_transform(skill_embeddings)
clusterer = hdbscan.HDBSCAN(min_cluster_size=2)
cluster_labels = clusterer.fit_predict(reduced_embeddings)

# cluster_labels from HDBSCAN or KMeans
cluster_to_skills = defaultdict(list)
for skill, label in zip(all_skills, cluster_labels):
    if label != -1:  # ignore noise points
        cluster_to_skills[label].append(skill)
print("Number of clusters:", len(cluster_to_skills))
# Print top 5 clusters and their skills
# for cluster_id in sorted(cluster_to_skills):
#     print(f"\nCluster {cluster_id}:")
#     for s in cluster_to_skills[cluster_id]:  # show first 10 skills
#         print(f"  - {s}")

# Convert cluster_labels to a NumPy array if it isn't already
cluster_labels = np.array(cluster_labels)

# Count of all skills
total_skills = len(cluster_labels)

# Count of clustered (non-noise) skills
clustered_skills = np.sum(cluster_labels != -1)

# Percentage clustered
percentage_clustered = (clustered_skills / total_skills) * 100

print(f"Total skills: {total_skills}")
print(f"Clustered skills: {clustered_skills}")
print(f"Percentage clustered: {percentage_clustered:.2f}%")

job_skills_set = set(job_skills)
course_skills_set = set(course_skills)

cluster_to_skills_2 = defaultdict(list)
for skill, label in zip(all_skills, cluster_labels):
    if label == -1:
        continue  # ignore noise points
    in_job = skill in job_skills_set
    in_course = skill in course_skills_set

    if in_job and in_course:
        source = 'both'
    elif in_job:
        source = 'job'
    elif in_course:
        source = 'course'
    else:
        source = 'unknown'

    cluster_to_skills_2[label].append((skill, source))

non_mixed_clusters = []

for cluster_id, skills in cluster_to_skills_2.items():
    types = [source for _, source in skills]
    counts = Counter(types)
    has_job = counts['job'] > 0 or counts['both'] > 0
    has_course = counts['course'] > 0 or counts['both'] > 0

    if has_job and has_course:
        print(f"Cluster {cluster_id} connects job and course skills! ✅")
    else:
        print(f"Cluster {cluster_id} is one-sided: {counts}")
        non_mixed_clusters.append(cluster_id)

mixed = sum(1 for s in cluster_to_skills_2.values() if 
            any(src in ['job','both'] for _, src in s) and
            any(src in ['course','both'] for _, src in s))
total = len(cluster_to_skills_2)
print(f"\n{mixed} out of {total} clusters mix job and course skills.")

# Prepare cluster_to_skills dictionary with only skill names (like your print format)
clusters_simple = {}
for cluster_id in sorted(cluster_to_skills):
    clusters_simple[str(cluster_id)] = cluster_to_skills[cluster_id]  # list of skill strings

# Write that dictionary to JSON nicely formatted
with open("clusters_skills_simple_2.json", "w", encoding="utf-8") as f:
    json.dump(clusters_simple, f, indent=4, ensure_ascii=False)

print("\nNon-mixed cluster IDs:")
print(non_mixed_clusters)