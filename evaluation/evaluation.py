import json
from fuzzywuzzy import fuzz

# === CONFIG ===
COURSE_JSON = '/home/natalie/Bachelorprojekt/evaluation/course_subset.json'
OUTPUT_FILE = '/home/natalie/Bachelorprojekt/evaluation/matching_courses.json'

# List of skill required by job:
skills = [
    "Python",
    "Data Analysis"
]

FUZZY_THRESHOLD = 80 

# look in course subset if skill can be found in title, lernergebnisse or inhalt
with open(COURSE_JSON, 'r', encoding='utf-8') as f:
    courses = json.load(f)

matches = []

for course in courses:
    course_id = course.get('kennung', '')
    name = course.get('name', '')
    url = course.get('url', '')
    lernergebnisse = course.get('lernergebnisse', '').lower()
    inhalt = course.get('inhalt', '').lower()
    title = name.lower()

    matched_skills = []
    match_contexts = []

    for skill in skills:
        skill_lower = skill.lower()

        for field_name, text in [("Title", title), ("Lernergebnisse", lernergebnisse), ("Inhalt", inhalt)]:
            score = fuzz.partial_ratio(skill_lower, text)
            if score >= FUZZY_THRESHOLD:
                snippet_start = text.find(skill_lower)
                snippet = ""
                if snippet_start >= 0:
                    snippet = text[max(0, snippet_start - 20):snippet_start + len(skill_lower) + 20]

                matched_skills.append(skill)
                match_contexts.append({
                    "Skill": skill,
                    "Field": field_name,
                    "FuzzyScore": score,
                    "ContextSnippet": snippet.strip()
                })
                break  

    if matched_skills:
        matches.append({
            'CourseID': course_id,
            'Name': name,
            'URL': url,
            'MatchedSkills': matched_skills,
            'MatchesDetail': match_contexts
        })

with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
    json.dump(matches, outfile, indent=4, ensure_ascii=False)

print(f" Saved {len(matches)} matched courses with fuzzy context")
