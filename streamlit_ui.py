import streamlit as st


st.title("Personalized Curriculum Mapping Tool")
st.write("Enter a job title to discover relevant courses:")
job_input = st.text_input("Job Title", placeholder="e.g. Data Scientist")

if st.button("Recommend Courses"):
    if not job_input.strip():
        st.warning("Please enter a valid job title.")
    else:
        with st.spinner("Looking up recommendations..."):
                    if job_input != "Data Scientist":
                        st.error(f" No job titled '{job_input}' found in the graph.")
                        st.warning("No course recommendations found for this job.")
                    else:
                        st.success(f"Top course matches for **{job_input}**:")
        