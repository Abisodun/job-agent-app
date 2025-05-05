
import streamlit as st
import pandas as pd
import requests
import openai
from PyPDF2 import PdfReader
import docx
import os

st.set_page_config(layout="wide")

RESUME_FILE = "resume.txt"
LOG_FILE = "job_log.csv"

def extract_text(file, file_type):
    if file_type == "txt":
        return file.read().decode("utf-8")
    elif file_type == "pdf":
        reader = PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif file_type == "docx":
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

def fetch_jobs(query, country, city, employment_type, is_remote, min_salary, experience):
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": "2bc0998f49mshb8e8cd2a7c87e7dp18960fjsnf228ecfe1ab9",
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    full_query = f"{query or 'project manager'} in {city}, {country}"
    valid_types = ["Full-time", "Part-time", "Contract", "Temporary", "Internship"]

    params = {
        "query": full_query,
        "employment_types": employment_type if employment_type in valid_types else None,
        "remote_jobs_only": "true" if is_remote else "false",
        "min_salary": min_salary,
        "experience_level": experience.lower() if experience != "Any" else None,
        "page": "1",
        "num_pages": "2"
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        st.error(f"API request failed with status code {response.status_code}")
        return []

    data = response.json()
    jobs = []
    for job in data.get("data", []):
        jobs.append({
            "Job Title": job.get("job_title", "N/A"),
            "Company": job.get("employer_name", "N/A"),
            "Location": job.get("job_city", "N/A") + ", " + job.get("job_country", "N/A"),
            "Link": job.get("job_apply_link", "N/A"),
            "Description": job.get("job_description", ""),
            "Cover Letter Path": "",
            "Status": "Applied"
        })
    return jobs

def generate_cover_letter(api_key, job_title, company, resume):
    openai.api_key = api_key
    prompt = f"Write a concise and professional cover letter for a '{job_title}' role at '{company}'. Base it on this resume:\n\n{resume[:1500]}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def score_resume_against_job(resume, job_description):
    resume_words = set(resume.lower().split())
    job_words = set(job_description.lower().split())
    match = resume_words.intersection(job_words)
    score = int((len(match) / len(job_words)) * 100) if job_words else 0
    return score

page = st.sidebar.radio("Select Page:", ["Job Search", "Application Tracker"])

if page == "Job Search":
    st.title("AI Job Application Agent with Resume Scoring")

    api_key = st.text_input("Enter your OpenAI API Key", type="password")
    query = st.text_input("Job Title / Keywords", "project manager")
    country = st.text_input("Country", "Canada")
    city = st.text_input("City", "Toronto")
    employment_type = st.selectbox("Employment Type", ["Any", "Full-time", "Part-time", "Contract", "Temporary", "Internship"])
    experience = st.selectbox("Experience Level", ["Any", "Entry", "Mid", "Senior"])
    is_remote = st.checkbox("Remote Only?")
    min_salary = st.slider("Minimum Salary ($)", 0, 200000, 0, 5000)

    uploaded_resume = st.file_uploader("Upload your Resume (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])
    if uploaded_resume:
        file_type = uploaded_resume.name.split(".")[-1]
        resume_text = extract_text(uploaded_resume, file_type)
    elif os.path.exists(RESUME_FILE):
        resume_text = open(RESUME_FILE, "r", encoding="utf-8").read()
    else:
        st.warning("Please upload a resume or create a 'resume.txt' file.")
        st.stop()

    if st.button("Find Jobs"):
        with st.spinner("Searching jobs..."):
            jobs = fetch_jobs(query, country, city, employment_type, is_remote, min_salary, experience)

        if not jobs:
            st.warning("No jobs found.")
        else:
            for i, job in enumerate(jobs[:10]):
                with st.expander(f"[{i+1}] {job['Job Title']} at {job['Company']}"):
                    st.markdown(f"**Location:** {job['Location']}")
                    st.markdown(f"[Apply Here]({job['Link']})")

                    score = score_resume_against_job(resume_text, job["Description"])
                    st.info(f"Resume Match Score: {score}%")

                    if st.button(f"Generate Cover Letter", key=f"gen_{i}"):
                        if api_key:
                            letter = generate_cover_letter(api_key, job["Job Title"], job["Company"], resume_text)
                            filename = f"cover_letter_{i+1}.txt"
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(letter)
                            job["Cover Letter Path"] = filename

                            file_exists = os.path.isfile(LOG_FILE)
                            with open(LOG_FILE, "a", newline="", encoding="utf-8") as csvfile:
                                df = pd.DataFrame([job])
                                df.to_csv(csvfile, mode='a', index=False, header=not file_exists)

                            st.text_area("Generated Cover Letter", value=letter, height=300)
                            st.success(f"Cover letter saved and job logged.")
                        else:
                            st.error("Please provide a valid OpenAI API key.")

else:
    st.title("Job Application Tracker")

    if "job_data" not in st.session_state:
        if os.path.exists(LOG_FILE):
            st.session_state.job_data = pd.read_csv(LOG_FILE, index_col=False)
        else:
            st.session_state.job_data = pd.DataFrame(columns=[
                "Job Title", "Company", "Location", "Link", "Cover Letter Path", "Status"
            ])

    df = st.session_state.job_data

    st.header("Summary")
    st.metric("Total Applications", len(df))

    st.header("Application Table")
    status_options = ["Applied", "Interviewing", "Rejected", "Hired"]

    column_config = {
        "Status": st.column_config.SelectboxColumn("Status", options=status_options),
        "Link": st.column_config.LinkColumn("Job Link")
    }

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        disabled=["Job Title", "Company", "Location", "Cover Letter Path"],
        hide_index=True,
        use_container_width=True,
        key="editor"
    )

    st.session_state.job_data = edited_df

    if st.button("Save Updates"):
        edited_df.to_csv(LOG_FILE, index=False)
        st.success("Application statuses saved!")
