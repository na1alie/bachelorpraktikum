from neo4j import GraphDatabase
import json

URI = "neo4j+s://19f2c9b2.databases.neo4j.io"
AUTH = ("neo4j", "2BfCH2hjWO_3Z3cqcUj4wXsyqxKe7bfKeBqIhM9J0o8")

#create NODES
def create_course_tx(tx, name):
    # Create new course node with given name, if not exists already
    result = tx.run("""
        MERGE (c:Course {name: $name})
        RETURN c.name AS name
        """, name=name
    )

def create_skill_tx(tx, name):
    # Create new skill node with given name, if not exists already
    result = tx.run("""
        MERGE (s:Skill {name: $name})
        RETURN s.name AS name
        """, name=name
    )

def create_job_tx(tx, name):
    # Create new job node with given name, if not exists already
    result = tx.run("""
        MERGE (j:Job {name: $name})
        RETURN j.name AS name
        """, name=name
    )

#create RELATIONSHIPS
def create_teaches_relationship_tx(tx, course, skill):
    # Create a teaches relationship between a Course and Skill
    tx.run("""
        MATCH (c:Course {name: $course})
        MATCH (s:Skill {name: $skill})
        MERGE (c)-[:TEACHES]->(s)
        """, course=course, skill=skill)
    
def create_requires_relationship_tx(tx, job, skill):
    # Create a requires relationship between a Job and Skill
    tx.run("""
        MATCH (j:Job {name: $job})
        MATCH (s:Skill {name: $skill})
        MERGE (j)-[:REQUIRES]->(s)
        """, job=job, skill=skill)
    
#delete all nodes and relationshipps
def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")

#connect to database
driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()
print("Connected to:", driver.get_server_info())

#add nodes and relationships saved in courses_skills.json
with open("courses_skills.json", "r", encoding="utf-8") as f:
    courses_skills = json.load(f)
for course in courses_skills:
    with driver.session() as session:
        session.execute_write(create_course_tx, course["title"])
        for skill in course["skills"]:
            session.execute_write(create_skill_tx, skill)
            session.execute_write(create_teaches_relationship_tx, course["title"], skill)
            print(skill)
            #session.execute_write(clear_database)

# Close driver 
driver.close()