import streamlit as st


from recommender_helper import (
    load_precomputed_embeddings,
    get_jobs_by_seniority,
    find_closest_jobs,
    get_job_description_and_skills,
    summarize_job_claude,
    get_course_description,
    summarize_course_claude,
    get_required_skills,
    get_job_seniority_levels,
    get_required_skill_groups,
    recommend_courses_top_coverage,
    recommend_courses_top_similarity
)


# --- Session State ---
if "selected_job" not in st.session_state:
    st.session_state.selected_job = None
if "show_course_options" not in st.session_state:
    st.session_state.show_course_options = False
if "closest_jobs" not in st.session_state:
    st.session_state.closest_jobs = []
if "selected_levels" not in st.session_state:
    st.session_state.selected_levels = []
if "seniority_levels" not in st.session_state:
    st.session_state.seniority_levels = []

# --- Inputs ---
st.title("Curriculum Mapping Tool")
st.page_link("pages/chat_ui.py", label=" ->  Click here to discover more")
job_input = st.text_input("Input a Job Title", value="", placeholder="e.g. Data Scientist")

seniority_levels = st.multiselect(
    "Select Seniority Level(s)",
    ["Mid-Senior level", "Entry level", "Internship", "Senior", "Associate", "Director", "All Levels"],
    default=["All Levels"]
)
st.session_state.seniority_levels = seniority_levels

if st.button("Find Jobs"):
    all_job_titles, job_title_embeddings, _, _ = load_precomputed_embeddings()
    filtered_jobs = get_jobs_by_seniority(st.session_state.seniority_levels)
    filtered_indices = [i for i, t in enumerate(all_job_titles) if t in filtered_jobs]
    filtered_jobs = [all_job_titles[i] for i in filtered_indices]
    filtered_embeddings = job_title_embeddings[filtered_indices] 

    closest = find_closest_jobs(job_input, filtered_jobs, filtered_embeddings)
    similarity_threshold = 0.6
    closest_jobs = [job for job in closest if job[1] >= similarity_threshold]

    if closest_jobs:
        st.session_state.closest_jobs = closest_jobs
    else:
        st.warning(
            f"No good matches found. "
            "Please try a different job title."
        )
        st.session_state.closest_jobs = []
if st.session_state.closest_jobs:
    st.markdown(
    "<h3 style='color:#3498db; font-weight: bold;'> Top Job Recommendations</h3>",
    unsafe_allow_html=True
    )
    for job_title, similarity in st.session_state.closest_jobs:
        job_info = get_job_description_and_skills(job_title)
        if "summaries" not in st.session_state:
            st.session_state.summaries = {}
        if job_title not in st.session_state.summaries:
            if job_info and job_info["description"]:
                #summary = summarize_job_claude(job_title, job_info)
                summary = "placeholder: to not to use api key to much"
                st.session_state.summaries[job_title] = summary
            else:
                st.session_state.summaries[job_title] = None

        with st.container():
            st.markdown(f"**{job_title}**  — Similarity: `{similarity:.3f}`")
            summary = st.session_state.summaries[job_title]
            if summary:
                st.markdown(f"**Summary:** {summary}")
            else:
                st.warning("No description found for this job.")
            st.markdown("---")

    selected = st.selectbox(
        "Choose fitting job",
        st.session_state.closest_jobs,
        format_func=lambda o: o[0]
    )
    st.session_state.selected_job = selected[0]

    levels_in_graph = get_job_seniority_levels(selected[0])
    if "All Levels" in st.session_state.seniority_levels or st.session_state.seniority_levels == []:
        st.session_state.selected_levels = ["Mid-Senior level", "Entry level", "Internship", "Senior", "Associate", "Director"]
    else:
        st.session_state.selected_levels = list(set(levels_in_graph) & set(st.session_state.seniority_levels))

    if st.button("Select Job"):
        st.session_state.show_course_options = True

#  --- Show course filters ---
if st.session_state.show_course_options and st.session_state.selected_job:
    st.success(f"Selected: {st.session_state.selected_job}")
    st.markdown("**Select Language and Module Level for Course Recommendations:**")

    language = st.multiselect(
        "Select Language",
        ["English", "German", "All Languages"],
        default=["All Languages"]
    )

    modullevel = st.multiselect(
        "Select Modullevel",
        ["Bachelor", "Master", "All Levels"],
        default=["All Levels"]
    )
    if "All Languages" in language:
        language = ["Englisch", "Deutsch/Englisch", "Deutsch"]
    else:
        language = [l.replace("English", "Englisch")
                    .replace("German", "Deutsch")
                    for l in language]
        
    if "All Levels" in modullevel:
        modullevel = ["Bachelor", "Bachelor/Master", "Master"]
    elif "Bachelor" in modullevel and "Master" in modullevel:
        modullevel = ["Bachelor", "Bachelor/Master", "Master"]
    if "Bachelor" in modullevel:
        modullevel = ["Bachelor", "Bachelor/Master"]   
    if "Master" in modullevel:
        modullevel = ["Master", "Bachelor/Master"]   
    
    algorithm_choice = st.radio(
        "Select recommendation strategy:",
        ["Top Similarity", "Top Coverage"],
        index=0  # default selection
    )

    if st.button(f"Recommend Courses to become {st.session_state.selected_job}"):
        st.markdown(
        "<h3 style='color:#3498db; font-weight: bold;'> Top Course Recommendations</h3>",
        unsafe_allow_html=True
        )
        with st.spinner("Finding best matching courses..."):
            all_required_skills = set(get_required_skills(st.session_state.selected_job, st.session_state.selected_levels))
            all_required_skill_groups = get_required_skill_groups(st.session_state.selected_job, st.session_state.selected_levels)
            all_taught_skills = set()
            
            if algorithm_choice == "Top Similarity":
                top_courses = recommend_courses_top_similarity(
                    st.session_state.selected_job,
                    st.session_state.selected_levels,
                    language,
                    modullevel
                )
            elif algorithm_choice == "Top Coverage":
                top_courses = recommend_courses_top_coverage(
                    st.session_state.selected_job,
                    st.session_state.selected_levels,
                    language,
                    modullevel
                )
            num_courses = sum(len(course_list) for _, course_list in top_courses)
            st.markdown(f" ({num_courses} courses found)")
            for job_title, course_list in top_courses:
                for course, similarity, skills in course_list:
                    all_taught_skills.update(skills)
                    course_info = get_course_description(course)
                    #summary_course = summarize_course_claude(course, course_info)
                    summary_course = "placeholder: to not to use api key to much"
                    st.markdown(f"""
                    **{course}**
                    - **Match Score:** `{similarity:.3f}`
                    - **Skills Taught needed as {st.session_state.selected_job}:** {', '.join(skills)}
                    - **Module Level:** `{course_info['modulniveau']}`
                    - **Language:** `{course_info['sprache']}`
                    - **Summary:** {summary_course}
                    - [**View Course**]({course_info['url']})
                    """)
                    st.write("---")
            filtered_skill_groups = {
                group: skills
                for group, skills in all_required_skill_groups.items()
                if not any(skill in all_taught_skills for skill in skills)
            }
            skill_gap = sorted(filtered_skill_groups.keys())
            st.info(f"**Taught skills:** These skills are covered by a recommended course: {', '.join(all_taught_skills)}")
            if skill_gap:
                st.info(f"**Skill Gaps:** These required skill areas are not covered by any recommended course: {', '.join(skill_gap)}")
            else:
                st.success("No skill gaps! The recommended courses cover all required skills.")

