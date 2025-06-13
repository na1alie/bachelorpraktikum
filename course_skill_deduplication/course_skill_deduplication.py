from sentence_transformers import SentenceTransformer, util
import torch
import json
import numpy as np


# find for skills in courses_anthropic_skills a match in all_unique_skills, if no such match: add skill to KG anyway

model = SentenceTransformer("all-MiniLM-L6-v2")

# load unique skills
with open("/home/natalie/Bachelorprojekt/job_skill_deduplication/all_unique_skills.json") as f:
    skills = json.load(f)

print(f"loaded {len(skills)} skills")

# load courses with skills
with open("/home/natalie/Bachelorprojekt/course_skill_extraction/courses_anthropic_skills.json", "r") as f:
    courses = json.load(f)

print(f"loaded {len(courses)} courses")


all_course_skills = [course['skills'] for course in courses if 'skills' in course]
flattened_course_skills = [skill for sublist in all_course_skills for skill in sublist]

unique_course_skills = list(set(flattened_course_skills))
print(len(unique_course_skills))

# encode all skills
course_skills_encodings = torch.tensor(model.encode(unique_course_skills))
skills_encodings =torch.tensor(model.encode(skills))

# torch cosine similarity only works for single vector*matrix
# similarity_scores = torch.cosine_similarity(skills_encodings[0], course_skills_encodings, dim=1)
def pairwise_cosine_sim(a, b):
   a_norm = a / a.norm(dim=1)[:, None]
   b_norm = b / b.norm(dim=1)[:, None]
   res = torch.mm(a_norm, b_norm.T)
   return res

cosine_sim = pairwise_cosine_sim(skills_encodings, course_skills_encodings)
print(f"maximum deviation of first row to torch implementation of cosine sim: {torch.max(cosine_sim[0] - torch.cosine_similarity(skills_encodings[0], course_skills_encodings, dim=1))}") 
print(cosine_sim.shape)


# for eacjh course skill (dim 1) find the closest skill (dim 0)
skill_matching_max = torch.max(cosine_sim, dim=0)
skill_matching_score = skill_matching_max.values # max
skill_matching = skill_matching_max.indices # argmax

# calculate percentile cutoff 
p = 50
percentile_cutoff = np.percentile(skill_matching_score.numpy(), p)
print(f"keeping {100-p}% of course skills when cutting at sim {percentile_cutoff}")
cutoff_mask = skill_matching_score >= percentile_cutoff
# get matched skills
matched_skills = np.array(skills)[skill_matching.numpy()]
original_skills = np.array(unique_course_skills)
stacked_matching = np.array([original_skills, matched_skills, skill_matching_score.numpy()])
matched_stacked = stacked_matching[:,cutoff_mask]
unmatched_stacked = stacked_matching[:,~cutoff_mask]


lookup_dict = {x[0]: {"skill": x[1], "score": x[2]} for x in matched_stacked.T.tolist()}
# iterate through courses: and add matched skills
for course in courses:
    if 'skills' in course:
        matched_skills = []
        matching = []
        for skill in course['skills']:
            if skill in lookup_dict:
                matched_skill = lookup_dict[skill]
                matched_skill_name = matched_skill['skill']
                if matched_skill not in matched_skills:
                    matched_skills.append(matched_skill_name)
                matching.append((skill, matched_skill_name, matched_skill['score']))
            else:
                matching.append((skill, "unmatched", None))
        course['matching'] = matching
        course['matched_skills'] = matched_skills

with open("/home/natalie/Bachelorprojekt/course_skill_deduplication/courses_with_matching.json", "w") as outfile:
    json.dump(courses, outfile, indent=4, ensure_ascii=False)

print("wrote skills to courses_with_matching")