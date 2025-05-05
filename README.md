
# Job Agent App (OpenAI Only)

This is a smart job application assistant built with Streamlit. It helps users search, rank, and rewrite resumes for job listings using OpenAI's GPT API.

## ✅ Features

- 🔍 **Job Search** by title, country, city, and province
- 📄 **Resume Upload** in `.txt`, `.pdf`, or `.docx`
- 🧠 **Resume Rewriting** with GPT (OpenAI)
- 📈 **Match Score Calculation** between resume and job description
- ⭐ **Ranking** jobs by match score
- 🔽 **Sorting** by score, job title, or company
- 📑 **Pagination** of job results
- 📊 **Advanced Filters**:
  - Employment type
  - Salary range
  - Remote-only toggle
  - Province/state input
- 📥 **Download Rewritten Resume** as `.docx`

## 🚀 How to Deploy on Streamlit Cloud

1. Upload this code to a public GitHub repository.
2. Visit [https://streamlit.io/cloud](https://streamlit.io/cloud).
3. Click **"New App"**, select your repo and branch.
4. Set the main file to `job_agent_app.py`.
5. Click **Deploy**.

## 🔐 API Requirements

- **OpenAI API Key** – required for resume rewriting.
  Get yours at: https://platform.openai.com/account/api-keys

## 📦 Installation (local)

```bash
pip install -r requirements.txt
streamlit run job_agent_app.py
```

## 📝 Credits

Built with ❤️ using:
- Streamlit
- OpenAI GPT
- PyPDF2 & python-docx
- RapidAPI (JSearch endpoint)

---

MIT License © 2025
