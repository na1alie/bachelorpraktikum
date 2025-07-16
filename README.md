# Course Recommender System using Knowledge Graphs
This project implements a recommender system for courses offered by the Computer Science and Computer Engineering Departments of TUM. It leverages a knowledge graph connecting jobs, skills and courses to generate recommendations tailored to students' career aspirations.

## 📁 Main Components
- **Job Data Preprocessing**
  - `job_offer_collection/`: Collects job postings via Bright Data (LinkedIn, Glassdoor, Indeed).
  - `job_skill_extraction/`: Extracts relevant skills per job using the Claude API.
  - `job_skill_deduplication/`: Canonicalizes job skills with SentenceTransformer embeddings.
  - `job_seniority_classification/`: Classifies jobs by experience level (only for job postings that were missing the seniority_level entry in the Bright Data API response).
  - `clean_job_titles/`: Cleans job titles by stripping away details such as gender tags and contract information to enable deduplication.
  - `job_title_deduplication/`: Deduplicates job titles with SentenceTransformer embeddings.
- **Course Data Preprocessing**
  - `course_offer_collection/`: Collects raw course data from the TUM module catalog using Selenium.
  - `courses_cs_bsc/`: (Legacy) Collects course data (only CS BSc electives).
  - `course_skill_extraction/`: Uses the Claude API to extract skills from course descriptions.
  - `course_skill_deduplication/`: Maps extracted course skills to canonical job skill names.
- **Knowledge Graph Construction**
  - `kg_construction_scripts/`: Builds the Neo4j knowledge graph.
  - `skill_clustering/`: Groups similar skills into named SkillGroups using UMAP + HDBSCAN.
- **UI**
  - Streamlit-based web tool.
- **Evaluation**
  - Scripts for evaluating course recommendations.

## 🌐 Web Tool
An interactive Streamlit app provides both a search interface and a conversational chat interface for exploring course recommendations based on job titles. It recommends courses with explanations, filters, and LLM-generated summaries. The chat interface is powered by an agent using GraphRAG to enable natural language queries.  
🔗 Try the app here: https://evaluate.lohhof.city
