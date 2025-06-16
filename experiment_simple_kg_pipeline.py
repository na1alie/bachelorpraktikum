from pathlib import Path
#from neo4j_graphrag.llm import OpenAILLM as LLM
#from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings as Embeddings
from neo4j_graphrag.experimental.components.pdf_loader import DataLoader, PdfDocument
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm import AnthropicLLM
import json
import neo4j
import os
from dotenv import load_dotenv
from neo4j_graphrag.embeddings.sentence_transformers import SentenceTransformerEmbeddings
import asyncio

load_dotenv()
ANTHROPIC_KEY=os.getenv("ANTHROPIC_API_KEY")
NEO4J_URI = "neo4j+s://db4db4e4.databases.neo4j.io"
NEO4J_AUTH = ("neo4j", "thK5o68RtU40Ug3fm26ZctCGVMkyzGvXaKICJi9JqGY")

neo4j_driver = neo4j.GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

ex_llm = AnthropicLLM(
    model_name="claude-3-opus-20240229",
    model_params={"max_tokens": 1000},  # max_tokens must be specified
    api_key=ANTHROPIC_KEY,  # can also set `ANTHROPIC_API_KEY` in env vars
)


# Initialize the embedder with the default model
embedder = SentenceTransformerEmbeddings(model="all-MiniLM-L6-v2")

prompt_template = """
You are an education technology researcher tasked with extracting information from text 
to structure it in a property graph for curriculum mapping and course recommendation 
based on job requirements.

Extract the entities (nodes) and specify their type from the following Input text.
Also extract the relationships between these nodes. The relationship direction goes from the start node to the end node.

Return result as JSON using the following format:
{{"nodes": [ {{"id": "0", "label": "the type of entity", "properties": {{"name": "name of entity" }} }}],
  "relationships": [{{"type": "TYPE_OF_RELATIONSHIP", "start_node_id": "0", "end_node_id": "1", "properties": {{"details": "Description of the relationship"}} }}] }}

Guidelines:
- Use only the information from the Input text. Do not add any additional information.  
- If the input text is empty, return an empty JSON.
- Create as many nodes and relationships as needed to provide a rich, interconnected knowledge graph.
- Nodes may represent concepts such as: **Course**, **Skill**, **JobTitle**, **Tool**, **Topic**, **Field**, **Organization**, **Credential**, or others as appropriate.
- Relationship types may include: **teaches**, **requires**, **prepares_for**, **related_to**, **offered_by**, **uses**, or other meaningful connections.
- Assign a unique string ID to each node, and reuse that ID when defining relationships.
- The graph must support reasoning about which courses to recommend for specific job roles, based on required or taught skills.
- Do not return any additional information other than the JSON structure.

Schema:
{schema}

Examples:
{examples}

Input text:

{text}
"""

# 1. Build KG and Store in Neo4j Database
kg_builder_pdf = SimpleKGPipeline(
    llm=ex_llm,
    driver=neo4j_driver,
    text_splitter=FixedSizeSplitter(chunk_size=500, chunk_overlap=100),
    embedder=embedder,
    prompt_template=prompt_template,
    from_pdf=True
)

async def build_kg():
    file_paths = ['job_offer_collection/job_results_bright_data.pdf']

    for path in file_paths:
        print(f"Processing : {path}")
        pdf_result = await kg_builder_pdf.run_async(path)
        print(f"Result: {pdf_result}")

asyncio.run(build_kg())