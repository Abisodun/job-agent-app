
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from PyPDF2 import PdfReader
import docx

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

page = st.sidebar.radio("Select Page:", ["Job Search", "Application Tracker"])

if page == "Job Search":
    st.title("AI Job Application Agent")
    st.write("Search for jobs and prepare cover letters using ChatGPT.")

    job_query = st.text_input("Job Title / Keywords", "project manager")
    location = st.text_input("Location", "Winnipeg")

    uploaded_resume = st.file_uploader("Upload your Resume (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])
    if uploaded_resume:
        file_type = uploaded_resume.name.split(".")[-1]
        resume_text = extract_text(uploaded_resume, file_type)
    elif os.path.exists(RESUME_FILE):
        resume_text = open(RESUME_FILE, "r", encoding="utf-8").read()
    else:
        st.warning("Please upload a resume or create a 'resume.txt' file.")
        st.stop()

    def fetch_jobs(query, location):
        url = f"https://ca.indeed.com/jobs?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        job_cards = soup.find_all("div", class_="job_seen_beacon")
        jobs = []
        for div in job_cards:
            title_elem = div.find("h2")
            company_elem = div.find("span", class_="companyName")
            link_elem = div.find("a", href=True)
            if title_elem and company_elem and link_elem:
                jobs.append({
                    "Job Title": title_elem.text.strip(),
                    "Company": company_elem.text.strip(),
                    "Link": f"https://ca.indeed.com{link_elem['href']}",
                    "Cover Letter Path": "",
                    "Status": "Applied"
                })
        return jobs

    def keyword_match(title, resume):
        return sum(1 for word in title.lower().split() if word in resume.lower())

    if st.button("Find Jobs"):
        st.info("Searching...")
        jobs = fetch_jobs(job_query, location)
        jobs = sorted(jobs, key=lambda j: keyword_match(j["Job Title"], resume_text), reverse=True)

        if not jobs:
            st.error("No jobs found.")
        else:
            for i, job in enumerate(jobs[:5]):
                with st.expander(f"[{i+1}] {job['Job Title']} at {job['Company']}"):
                    st.markdown(f"[View Job Posting]({job['Link']})")
                    st.write("### Prompt to Use in ChatGPT:")
                    prompt = f"""Write a professional cover letter for:

Job Title: {job['Job Title']}
Company: {job['Company']}

Use this resume:
{resume_text[:1500]}...(truncated)
"""
                    st.code(prompt, language="markdown")

                    letter = st.text_area("Paste your generated cover letter here (or type SKIP):", key=f"cl_{i}")
                    if letter.strip().lower() != "skip" and letter.strip() != "":
                        filename = f"cover_letter_{i+1}.txt"
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(letter)
                        job["Cover Letter Path"] = filename

                        file_exists = os.path.isfile(LOG_FILE)
                        with open(LOG_FILE, "a", newline="", encoding="utf-8") as csvfile:
                            df = pd.DataFrame([job])
                            df.to_csv(csvfile, mode='a', index=False, header=not file_exists)

                        st.success(f"Cover letter saved as `{filename}` and job logged.")
                    elif letter.strip().lower() == "skip":
                        st.info("Skipped.")

else:
    st.title("Job Application Tracker")

    if "job_data" not in st.session_state:
        if os.path.exists(LOG_FILE):
            st.session_state.job_data = pd.read_csv(LOG_FILE, index_col=False)
        else:
            st.session_state.job_data = pd.DataFrame(columns=[
                "Job Title", "Company", "Link", "Cover Letter Path", "Status"
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
        disabled=["Job Title", "Company", "Cover Letter Path"],
        hide_index=True,
        use_container_width=True,
        key="editor"
    )

    st.session_state.job_data = edited_df

    if st.button("Save Updates"):
        edited_df.to_csv(LOG_FILE, index=False)
        st.success("Application statuses saved!")
