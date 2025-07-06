import json
import os
import time
import re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Load API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise EnvironmentError("Please set the ANTHROPIC_API_KEY environment variable.")

client = Anthropic(api_key=api_key)

# Load clusters from file
with open("clusters_skills_simple_2.json", "r") as f:
    clusters = json.load(f)

final_output = {}

def build_prompt(cluster_id, skills):
    skill_list = "\n".join(f"- {skill}" for skill in skills)
    return f"""
You are an expert in computer science education and workforce development. I will give you a list of skills that have been clustered together based on vector similarity. Each skill may be part of a university course or a job requirement. All clusters are from the domain of computer science, but that alone is not sufficient reason to group skills together. Do not group skills together simply because they share technical jargon — group them by meaningful semantic themes.

Your task is to:
1. Assign a concise umbrella name that accurately describes the core theme of this skill cluster.
2. Respond strictly in this JSON format, DO NOT include your thinking in the output:

{{
  "split": false,
  "clusters": [
    {{
      "name": "Umbrella Term",
      "skills": ["skill1", "skill2", "skill3"]
    }}
  ]
}}

- Do NOT split the cluster.
- Do NOT merge it with others.
- Do NOT remove, reword, or replace any skills.
- Do NOT add new skills.
- All skills listed must remain **exactly** as they are — same wording, same list.

Here is the skill cluster:

{skill_list}
"""

for cluster_id, skills in clusters.items():

    print(f"Processing cluster {cluster_id} with {len(skills)} skills...")

    prompt = build_prompt(cluster_id, skills)

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            temperature=0.4,
            messages=[{
                "role": "user",
                "content": prompt.strip()
            }]
        )
        text_response = response.content[0].text.strip()

        # Try to parse JSON from Claude’s response
        try:
            json_start = text_response.find('{')
            json_data = json.loads(text_response[json_start:])
            for cluster in json_data["clusters"]:
                final_output[cluster["name"]] = cluster["skills"]
        except Exception as parse_error:
            print(f"⚠️ Could not parse response for cluster {cluster_id}. Raw text:")
            print(text_response)
            print()
            continue

        time.sleep(1)

    except Exception as e:
        print(f"❌ Error processing cluster {cluster_id}: {e}")
        continue

# Save final output
with open("named_clusters_2.json", "w") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

print("✅ All done! Named clusters saved to named_clusters.json")
