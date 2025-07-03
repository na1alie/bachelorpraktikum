import streamlit as st
import anthropic
from pyvis.network import Network
import tempfile
#from langchain.tools import Tool
#from langchain.agents import initialize_agent, AgentType
from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
import pickle
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import ast
import numpy as np
import re
import tempfile
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from recommender_helper import (
    load_precomputed_embeddings,
    get_jobs_by_seniority,
    find_closest_jobs,
    get_job_description_and_skills,
    summarize_job_claude,
    recommend_courses_semantic,
    get_course_description,
    summarize_course_claude,
)


if "state" not in st.session_state:
    st.session_state.state = {
        "messages": [],
        "job_title": None,
        "level": None,
        "courses": [],
        "results": [],
    }

dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'kg_construction_scripts', '.env')
load_dotenv(dotenv_path=dotenv_path)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

KNOWN_JOB_LEVELS = [
    "Internship",
    "Entry Level",
    "Associate",
    "Mid-Senior level",
    "Senior",
    "Director",
    "Executive"
]

# Color mapping for node types
NODE_STYLES = {
    "Job": {"color": "#e74c3c", "font_color": "white"},     # Bright Red
    "Skill": {"color": "#3498db", "font_color": "white"},   # Vivid Blue
    "Course": {"color": "#2ecc71", "font_color": "white"},  # Bright Green
}

# llm = ChatAnthropic(
#     model="claude-3-opus-20240229",  # You can also use "claude-3-sonnet-20240229"
#     temperature=0,
#     max_tokens=1024,
#     api_key=os.getenv("ANTHROPIC_API_KEY") 
# )

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="meta-llama/llama-4-scout-17b-16e-instruct"
)

# --- Load SentenceTransformer model ---
embedder = SentenceTransformer('all-MiniLM-L6-v2')

class EmbeddingStore:
    _instance = None

    def __init__(self):
        # Prevent double initialization
        if not hasattr(self, "initialized"):
            self.all_jobs, self.job_embeddings = self.load_job_embeddings()
            self.all_skills, self.skill_embeddings = self.load_skill_embeddings()
            self.initialized = True

    @staticmethod
    def load_job_embeddings():
        with open("job_embeddings.pkl", "rb") as f:
            all_jobs, job_embeddings = pickle.load(f)
        return all_jobs, job_embeddings

    @staticmethod
    def load_skill_embeddings():
        with open("skill_embeddings.pkl", "rb") as f:
            all_skills, skill_embeddings = pickle.load(f)
        return all_skills, skill_embeddings

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_required_skills(job_title: str):
    query = """
    MATCH (j:Job {name: $job_title})-[:requires]->(s:Skill)
    RETURN s.name AS skill
    """
    with driver.session() as session:
        result = session.run(query, job_title=job_title)
        return [record["skill"] for record in result]


def get_relevant_courses_with_skills(job_title):
    query = """
        MATCH (j:Job {name: $job_title})-[:requires]->(s:Skill)<-[:TEACHES]-(c:Course)
        WITH c, collect(DISTINCT s.name) AS required_skills
        MATCH (c)-[:TEACHES]->(sk:Skill)
        RETURN c.name AS course, collect(DISTINCT sk.name) AS all_skills, required_skills
    """
    with driver.session() as session:
        result = session.run(query, job_title=job_title)
        return [(record["course"], record["all_skills"], record["required_skills"]) for record in result]


def get_explanation_subgraph(job_titles, level, course_name):
    query = """
        MATCH (c:Course)
        WHERE toLower(c.name) CONTAINS toLower($course_name)
        WITH c
        MATCH (c)-[:TEACHES]->(s:Skill)<-[:requires]-(j:Job)
        WHERE j.name IN $job_titles
        {level_clause}
        WITH c, j, collect(DISTINCT s) AS shared_skills

        OPTIONAL MATCH (c)-[:TEACHES]->(s2:Skill)
        WITH c, j, shared_skills, collect(DISTINCT s2) AS all_taught_skills

        OPTIONAL MATCH (j)-[:requires]->(s3:Skill)
        WITH c, j, shared_skills, all_taught_skills, collect(DISTINCT s3) AS all_required_skills

        UNWIND all_taught_skills AS taught
        UNWIND all_required_skills AS required

        RETURN DISTINCT j, taught, required, c
    """

    # Insert seniority level condition if needed
    level_clause = "\nAND j.seniority_level = $level" if level else ""
    query = query.format(level_clause=level_clause)

    with driver.session() as session:
        params = {"job_titles": job_titles, "course_name": course_name}
        if level:
            params["level"] = level

        result = session.run(query, **params)

        nodes = {}
        edges = set()

        for record in result:
            job_node = record["j"]
            taught_skill = record["taught"]
            required_skill = record["required"]
            course_node = record["c"]

            nodes[job_node.id] = {
                "id": job_node.id, "label": job_node["name"], "type": "Job"
            }
            nodes[course_node.id] = {
                "id": course_node.id, "label": course_node["name"], "type": "Course"
            }

            nodes[taught_skill.id] = {
                "id": taught_skill.id, "label": taught_skill["name"], "type": "Skill"
            }
            nodes[required_skill.id] = {
                "id": required_skill.id, "label": required_skill["name"], "type": "Skill"
            }

            edges.add((job_node.id, required_skill.id, "requires"))
            edges.add((course_node.id, taught_skill.id, "teaches"))

        return {
            "nodes": list(nodes.values()),
            "edges": [
                {"from": src, "to": tgt, "type": rel} for (src, tgt, rel) in edges
            ]
        }


def find_closest_jobs(input_title, top_k=3):
    store = EmbeddingStore.get_instance()
    
    all_job_titles = store.all_jobs
    job_title_embeddings = store.job_embeddings

    input_emb = embedder.encode([input_title], convert_to_numpy=True)
    similarities = cosine_similarity(input_emb, job_title_embeddings)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]
    return [(all_job_titles[i], float(similarities[i])) for i in top_indices]


def recommend_courses_semantic(closest_jobs, top_n=10):
    #closest_jobs = ast.literal_eval(closest_jobs_str)
    store = EmbeddingStore.get_instance()
    
    all_job_titles = store.all_jobs
    job_title_embeddings = store.job_embeddings
    all_skills = store.all_skills
    skill_embeddings = store.skill_embeddings
    skill_to_embedding = dict(zip(all_skills, skill_embeddings))

    #closest_jobs = find_closest_jobs(job_title, all_job_titles, job_title_embeddings)

    course_suggestions = []

    alpha = 0.6

    for job, job_score in closest_jobs:
        job_skills = get_required_skills(job)
        job_skill_embeddings = [
            skill_to_embedding[skill]
            for skill in job_skills
            if skill in skill_to_embedding  # in case some skill is missing from precomputed
        ]

        all_courses = get_relevant_courses_with_skills(job)
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

    print(course_suggestions)
    st.session_state.state["results"] = course_suggestions
    top_courses_flat = flatten_and_deduplicate_courses(course_suggestions)
    st.session_state.state["courses"] = top_courses_flat
    return top_courses_flat


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
    top_courses_flat = [(course, float(score)) for course, score in sorted_courses[:max_courses]]
    return top_courses_flat


def filter_jobs(job_list, level):
    """
    Filters a list of (job_name, similarity_score) tuples by checking if the job exists
    in the Neo4j database at the given level. Returns a filtered list in the same format.
    """
    query = """
    MATCH (j:Job)
    WHERE toLower(j.name) = toLower($name) AND toLower(j.seniority_level) = toLower($level)
    RETURN j.name AS job
    """

    filtered = []
    with driver.session() as session:
        for job_name, score in job_list:
            result = session.run(query, name=job_name, level=level)
            if result.single():
                filtered.append((job_name, score))
    
    return filtered

def extract_job_title_and_level(user_input):
    parts = [p.strip().lower() for p in user_input.split(",")]
    if len(parts) == 2 and parts[1] in KNOWN_JOB_LEVELS:
        return parts[0], parts[1]
    else:
        # no level found, treat whole input as job title
        return user_input.strip(), None


def extract_course_index(query: str) -> int | None:
    query = query.lower()

    # Match patterns like "1st course", "2nd recommendation", "first course", "second recommendation"
    match = re.search(r"\b(?:(\d+)(st|nd|rd|th)|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+(course|recommendation)\b", query)
    
    if not match:
        return None

    # If numeric match (e.g., "2nd course")
    if match.group(1):
        return int(match.group(1)) - 1

    # If word-based ordinal match (e.g., "second course")
    word_to_index = {
        "first": 0,
        "second": 1,
        "third": 2,
        "fourth": 3,
        "fifth": 4,
        "sixth": 5,
        "seventh": 6,
        "eighth": 7,
        "ninth": 8,
        "tenth": 9
    }

    return word_to_index.get(match.group(0).split()[0])  # get ordinal index


def extract_course_name(query: str, courses: list[str]) -> str | None:
    for course in courses:
        if course.lower() in query.lower():
            return course
    return None


def get_explanation_subgraph_tool(course_name: str) -> dict:
    # Parse the input if you want, e.g. "Data Scientist, Machine Learning"
    # try:
    #     job_title, course_name = map(str.strip, job_title_and_course_name.split(","))
    # except Exception:
        
    #     return {"error": "Please provide input as 'Job Title, Course Name'"}
    course_index = extract_course_index(course_name)
    #course_name_extracted = extract_course_name(course_name)

    print(course_index)
    if course_index:
        course_name = st.session_state.state["courses"][course_index][0]
    
    job_titles = [job for job, _ in st.session_state.state["results"]]
    
    #graph_data = get_explanation_subgraph(job_title, course_name)
    return f"[SHOW_GRAPH] {job_titles} | {course_name}"


def recommend_courses_for_job_title(input):
    job_title, level = extract_job_title_and_level(input)
    st.session_state.state["job_title"] = job_title
    st.session_state.state["level"] = level
    closest_jobs = find_closest_jobs(job_title)
    if level in KNOWN_JOB_LEVELS:
        closest_jobs = filter_jobs(closest_jobs, level)
    return recommend_courses_semantic(closest_jobs)


tools = [
    # Tool(name="get_required_skills", func=get_required_skills,
    #      description="Use this to get required skills for a given job title"),
    Tool(name="recommend_courses_for_job_title", func=recommend_courses_for_job_title,
             description=(
                "Use this to get course recommendations for a user-specified job. "
                f"If the user EXPLICITLY includes a job level like {KNOWN_JOB_LEVELS}, "
                "you must extract and pass it along as a second argument. "
                "Otherwise, do not assume a level — just pass the job title only."
    )),
    Tool(
        name="get_explanation_subgraph",
        func=get_explanation_subgraph_tool,
        description=(
                    "Use this **ONLY** when the user **EXPLICITLY** asks for an EXPLANATION. "
                    "Return a string in the form '[SHOW_GRAPH] job title | course name'. "
                    "Does **NOT** require a job title input"
                    "Does **NOT** require a course name input, tool can infer from e.g. 'first course/recommendation', just pass this"
                    "**IMPORTANT**: You MUST include the output verbatim in your final answer to the user. "
                    "Do NOT just use the information internally — explicitly write the '[SHOW_GRAPH] ...' string into your answer."
        )
    ),
    Tool(
        name="get_course_description",
        func=get_course_description,
        description=(
                    "Use this tool to get more information about a course's content and learning goal."
                    "ONLY use this to give some more information. DO NOT use it to recommend coureses."
                    "Please summarize the retrieved info in English in 2-3 clear sentences as if explaining to a student."
                    "Include the url in the format [**View Course**](url) so that it is clickable"
                    "Use the other info if the user asks for teaching language or level of the course"
        )
    ),
]

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    memory=memory,
)

def display_graph(data):
    net = Network(
        height='600px',
        width='100%',
        notebook=False,
        cdn_resources='in_line',
        directed=True
    )
    net.barnes_hut(gravity=-8000, spring_length=150, central_gravity=0.2)

    # Add styled nodes
    for node in data['nodes']:
        style = NODE_STYLES.get(node['type'], {"color": "#bdc3c7", "font_color": "black"})  # fallback: gray
        net.add_node(
            node['id'],
            label=node['label'],
            color=style['color'],
            font={"size": 26, "color": style['font_color']},  # Larger labels and better contrast
            size=35,  # Bigger nodes
            shape="ellipse",
            title=f"{node['type']}: {node['label']}"
        )

    # Add labeled edges with better spacing
    for edge in data['edges']:
        net.add_edge(
            edge['from'],
            edge['to'],
            label=edge['type'],
            arrows='to',
            font={"size": 20, "color": "black", "align": "middle"},
            color="#7f8c8d"  # Medium contrast gray
        )

    # Export and display in Streamlit
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".html") as tmp_file:
        path = tmp_file.name
        net.save_graph(path)
        html_content = open(path, 'r').read()

    st.components.v1.html(html_content, height=650, scrolling=True)

st.title("📚 TUM Courses Recommender")
st.caption("🚀 A Streamlit chatbot powered by Claude")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = agent.run(prompt + " Use this context: " + str(st.session_state.state))

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)

    if "[SHOW_GRAPH]" in response:
        try:
            # Extract job and course using simple pattern: [SHOW_GRAPH] Job Title | Course Name
            match = re.search(r"\[SHOW_GRAPH\]\s*(.*?)\s*\|\s*(.*)", response)
            if match:
                job_titles, course_name = match.group(1), match.group(2)
                job_titles = [job for job, _ in st.session_state.state["results"]]
                subgraph_data = get_explanation_subgraph(job_titles, st.session_state.state["level"], course_name)
                display_graph(subgraph_data)
            else:
                st.warning("Could not extract job title and course name from graph instruction.")
        except Exception as e:
            st.error(f"Error while showing graph: {e}")
