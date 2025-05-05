
import streamlit as st
import pandas as pd
import requests
import openai
from PyPDF2 import PdfReader
import docx
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(layout="wide")

RESUME_FILE = "resume.txt"
LOG_FILE = "job_log.csv"
GOOGLE_SHEET_NAME = "Job_Application_Tracker"

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

def score_resume_against_job(resume, job_description):
    resume_words = set(resume.lower().split())
    job_words = set(job_description.lower().split())
    match = resume_words.intersection(job_words)
    score = int((len(match) / len(job_words)) * 100) if job_words else 0
    return score

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

def export_to_google_sheets(df):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.create(GOOGLE_SHEET_NAME)
        worksheet = sheet.get_worksheet(0)
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return sheet.url
    except Exception as e:
        return f"Error: {e}"

st.title("Application Tracker with Deadlines & Google Sheets Export")

if os.path.exists(LOG_FILE):
    df = pd.read_csv(LOG_FILE)
    if "Deadline" not in df.columns:
        df["Deadline"] = ""

    st.metric("Total Applications", len(df))

    df["Match Label"] = df["Status"].apply(lambda x: "✅" if x == "Hired" else "🔍")

    df = df.sort_values(by="Deadline", na_position='last')

    status_options = ["Applied", "Interviewing", "Rejected", "Hired"]

    edited_df = st.data_editor(
        df,
        column_config={
            "Status": st.column_config.SelectboxColumn("Status", options=status_options),
            "Link": st.column_config.LinkColumn("Job Link"),
            "Deadline": st.column_config.DateColumn("Deadline")
        },
        disabled=["Job Title", "Company", "Location", "Cover Letter Path"],
        use_container_width=True,
        hide_index=True,
        key="editor"
    )

    if st.button("Save Updates"):
        edited_df.to_csv(LOG_FILE, index=False)
        st.success("Tracker updated.")

    if st.button("Export to Google Sheets"):
        with st.spinner("Exporting to Google Sheets..."):
            url = export_to_google_sheets(edited_df)
            if url.startswith("http"):
                st.success(f"Exported successfully: [Open Sheet]({url})")
            else:
                st.error(url)
else:
    st.warning("No applications tracked yet.")
