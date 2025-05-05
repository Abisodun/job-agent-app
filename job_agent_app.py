
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Job Agent with Tracker", layout="wide")

# Sidebar navigation
st.sidebar.title("📂 Navigation")
page = st.sidebar.radio("Go to", ["🔍 Job Search", "📋 Application Tracker"])

if "applications" not in st.session_state:
    st.session_state.applications = []

if page == "🔍 Job Search":
    st.title("🔍 Smart Job Search")
    st.write("This is where job search, filtering, resume rewrite, and ranking logic will go.")
    st.write("→ Add your job search UI and logic here.")

    # Example job to simulate tracking
    if st.button("Simulate & Track Sample Job"):
        st.session_state.applications.append({
            "Job Title": "Project Manager",
            "Company": "Sample Corp",
            "Deadline": "2025-06-30",
            "Status": "Pending"
        })
        st.success("Sample job tracked!")

elif page == "📋 Application Tracker":
    st.title("📋 Application Tracker with Deadlines & Google Sheets Export")

    if not st.session_state.applications:
        st.warning("No applications tracked yet.")
    else:
        df = pd.DataFrame(st.session_state.applications)
        st.dataframe(df)

        if st.button("Export to CSV"):
            df.to_csv("tracked_applications.csv", index=False)
            with open("tracked_applications.csv", "rb") as f:
                st.download_button("Download CSV", f, file_name="applications.csv")
