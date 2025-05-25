import openai
import json

#openai api key, kostet je prompt
client = openai.OpenAI(api_key="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")

courses_skills = []

with open("courses.json", "r", encoding="utf-8") as f:
    courses = json.load(f)
    for course in courses:
        prompt = f"""
        You are an expert in curriculum design and skills mapping.

        Extract only the relevant computer science or programming **skills** mentioned in the course description below. 
        Extract only high-level, commonly used computer science skills from this course. 
        Use short, normalized names (e.g., 'Java' instead of 'Java programming'). 
        Avoid niche or overly specific terms.

        Return the skills as a **Python list of strings**, and do not include any explanation or formatting beyond that.

        Course description:
        \"\"\"{course}\"\"\"
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        skills_raw = response.choices[0].message.content.strip()

        try:
           
            skills_list = eval(skills_raw)
        except Exception as e:
            print(f"Could not parse skills for: {course['title']}")
            skills_list = []

        courses_skills.append({
            "title": course["title"],
            "skills": skills_list 
        })
        
    with open("courses_skills.json", "w", encoding="utf-8") as f:
        json.dump(courses_skills, f, ensure_ascii=False, indent=2)