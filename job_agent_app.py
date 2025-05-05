
import streamlit as st
import pandas as pd
import requests
from PyPDF2 import PdfReader
import docx
import os

st.set_page_config(layout="wide")

# Function to extract text from uploaded resume
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

# Fetch jobs from JSearch API
def fetch_jobs(query, country, city, employment_type):
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": "2bc0998f49mshb8e8cd2a7c87e7dp18960fjsnf228ecfe1ab9",
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    full_query = f"{query} in {city}, {country}"
    params = {
        "query": full_query,
        "employment_types": employment_type if employment_type != "Any" else "",
        "page": "1",
        "num_pages": "1"
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
            "Cover Letter Path": "",
            "Status": "Applied"
        })
    return jobs

# Streamlit UI
st.title("Smart Job Search Assistant")

query = st.text_input("Job Title / Keywords", "project manager")
country = st.text_input("Country", "Canada")
city = st.text_input("City", "Toronto")
employment_type = st.selectbox("Employment Type", ["Any", "Full-time", "Part-time", "Contract", "Temporary", "Internship"])

uploaded_resume = st.file_uploader("Upload your Resume (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])
if uploaded_resume:
    file_type = uploaded_resume.name.split(".")[-1]
    resume_text = extract_text(uploaded_resume, file_type)
else:
    resume_text = ""

if st.button("Find Jobs"):
    st.info("Searching...")
    jobs = fetch_jobs(query, country, city, employment_type)

    if not jobs:
        st.warning("No jobs found.")
    else:
        for i, job in enumerate(jobs):
            with st.expander(f"[{i+1}] {job['Job Title']} at {job['Company']}"):
                st.markdown(f"**Location:** {job['Location']}")
                st.markdown(f"[Apply Here]({job['Link']})")
                st.write("### Prompt for ChatGPT:")
                st.code(f"Write a cover letter for a {query} role at {job['Company']} in {city}, {country}.

Resume:
{resume_text[:1500]}...", language="markdown")
