from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv

load_dotenv()
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

#connect to database
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
driver.verify_connectivity()
print("Connected to:", driver.get_server_info())

# Load the JSON clusters
with open("../skill_clustering/named_clusters_2.json", "r") as f:
    clusters = json.load(f)

def load_skill_groups(tx, group_name, skills):
    tx.run("""
        MERGE (group:SkillGroup {name: $group_name})
        WITH group
        UNWIND $skills AS skill_name
            MERGE (skill:Skill {name: skill_name})
            MERGE (group)-[:INCLUDES]->(skill)
    """, group_name=group_name, skills=skills)

with driver.session() as session:
    for cluster_name, skills in clusters.items():
        print(f"📥 Loading cluster: {cluster_name} ({len(skills)} skills)")
        session.write_transaction(load_skill_groups, cluster_name, skills)

driver.close()
print("✅ Done loading all skill clusters into the knowledge graph.")
