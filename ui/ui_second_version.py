import streamlit as st

from reommender_helper import (
    load_precomputed_embeddings,
    get_jobs_by_seniority,
    find_closest_jobs,
    get_job_description_and_skills,
    summarize_job_claude,
    recommend_courses_semantic,
    get_course_description,
    summarize_course_claude,
)


# --- Session State ---
if "selected_job" not in st.session_state:
    st.session_state.selected_job = None
if "show_course_options" not in st.session_state:
    st.session_state.show_course_options = False
if "closest_jobs" not in st.session_state:
    st.session_state.closest_jobs = []

# --- Inputs ---
st.title("Curriculum Mapping Tool")
job_input = st.text_input("Job Title", value="", placeholder="e.g. Data Scientist")

seniority_levels = st.multiselect(
    "Seniority Level(s)",
    ["Mid-Senior level", "Entry level", "Internship", "Senior", "Associate", "Director", "All Levels"],
    default=["All Levels"]
)


if st.button("Find Jobs"):
    all_job_titles, job_title_embeddings, _, _ = load_precomputed_embeddings()
    filtered_jobs = get_jobs_by_seniority(seniority_levels)
    filtered_indices = [i for i, t in enumerate(all_job_titles) if t in filtered_jobs]
    filtered_jobs = [all_job_titles[i] for i in filtered_indices]
    filtered_embeddings = job_title_embeddings[filtered_indices]  # dummy for now

    closest = find_closest_jobs(job_input, filtered_jobs, filtered_embeddings)
    st.session_state.closest_jobs = closest

if st.session_state.closest_jobs:
    st.subheader("Top 3 Job recommendations")
    for job_title, similarity in st.session_state.closest_jobs:
        job_info = get_job_description_and_skills(job_title)
        if "summaries" not in st.session_state:
            st.session_state.summaries = {}
        if job_title not in st.session_state.summaries:
            if job_info and job_info["description"]:
                summary = summarize_job_claude(job_title, job_info)
                #summary = "placeholder: to not to use api key to much"
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

    if st.button("Select Job"):
        st.session_state.show_course_options = True

#  --- Show course filters ---
if st.session_state.show_course_options and st.session_state.selected_job:
    st.success(f"Selected: {st.session_state.selected_job}")

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
                    .replace("German/English", "Deutsch/Englisch")
                    .replace("German", "Deutsch")
                    for l in language]
        
    if "All Levels" in modullevel:
        modullevel = ["Bachelor", "Bachelor/Master", "Master"]

    if st.button(f"Recommend Courses to become {st.session_state.selected_job}"):
        st.subheader("Top Course recommendations")
        with st.spinner("Finding best matching courses..."):
            top_courses = recommend_courses_semantic(
                st.session_state.selected_job,
                language,
                modullevel
            )
            for job_title, course_list in top_courses:
                for course, similarity, skills in course_list:
                    course_info = get_course_description(course)
                    summary_course = summarize_course_claude(course, course_info)
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

