def add_skill(tx, skill_name):
    tx.run("MERGE (s:Skill {name: $skill_name})", skill_name=skill_name)

def add_job(tx, job_name):
    tx.run("MERGE (j:Job {name: $job_name})", job_name=job_name)

def add_course(tx, course_name):
    tx.run("MERGE (c:Course {name: $course_name})", course_name=course_name)

def add_requires_relation(tx, job_name, skill_name):
    tx.run("""
        MATCH (j:Job {name: $job_name})
        MATCH (s:Skill {name: $skill_name})
        MERGE (j)-[:requires]->(s)
    """, job_name=job_name, skill_name=skill_name)