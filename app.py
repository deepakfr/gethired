import streamlit as st
import pdfplumber
import docx
import requests

# ✅ Set your Groq API Key
GROQ_API_KEY = "gsk_WhI4OpClTGCT2LxxvSpMWGdyb3FYBVUkG8jUO0HKpwK6OCylD8U"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# 🧠 Function to extract text from uploaded file
def extract_text(file):
    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        return file.read().decode("utf-8")

# 🧠 Function to send prompt to Groq API
def tailor_resume_and_coverletter(existing_resume, job_description):
    prompt = f"""
    Act as a professional career coach and resume writer.

    Based on the following existing resume:
    {existing_resume}

    And the following job description:
    {job_description}

    Strict Instructions:
    - Rewrite the resume to match the job description, emphasizing relevant skills and experiences.
    - Use keywords from the job description.
    - Keep it clean, ATS-optimized (no graphics, no fancy tables).
    - Sections: Summary, Skills, Experience, Education.
    - Bullet points start with action verbs.
    - Keep tone formal, no personal pronouns (no "I", "we").
    - Limit to 2 pages if possible.

    Then, create a Cover Letter:
    - Personalized to the company/job.
    - Professional tone.
    - 3 paragraphs max: intro (enthusiasm), body (skills match), conclusion (call to action).

    Output format:
    ### Tailored Resume
    [resume here]

    ### Cover Letter
    [cover letter here]
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        raise Exception(f"❌ Error from Groq API: {response.status_code} - {response.text}")

# 🏠 Streamlit App
st.set_page_config(page_title="GetHired - Tailor My Resume", page_icon="📝")
st.title("📝 GetHired - Tailor My Resume")
st.caption("Upload your Resume (PDF or DOC) + Paste the Job Description. Get a tailored Resume and Cover Letter!")

st.markdown("---")

# Upload section
st.subheader("📄 Upload Your Current Resume")
existing_resume_file = st.file_uploader("Upload Your Resume (PDF, DOC, or TXT)", type=["pdf", "docx", "txt"])

st.markdown("---")
st.subheader("🖊️ Paste Job Description")
job_description_text = st.text_area("Paste the Job Description here...")

if st.button("🚀 Tailor Resume & Create Cover Letter"):
    if existing_resume_file and job_description_text.strip():
        existing_resume = extract_text(existing_resume_file)
        job_description = job_description_text

        if not existing_resume.strip():
            st.error("❌ Could not extract text from the uploaded resume. Please check the file.")
        else:
            with st.spinner("✍️ Tailoring your Resume and writing your Cover Letter..."):
                try:
                    output = tailor_resume_and_coverletter(existing_resume, job_description)
                    st.success("✅ Done! Here are your tailored documents:")

                    # Split resume and cover letter
                    if "### Cover Letter" in output:
                        tailored_resume, cover_letter = output.split("### Cover Letter")
                        tailored_resume = tailored_resume.replace("### Tailored Resume", "").strip()
                        cover_letter = cover_letter.strip()

                        st.markdown("---")
                        st.subheader("📄 Tailored Resume:")
                        st.code(tailored_resume)

                        st.subheader("✉️ Cover Letter:")
                        st.code(cover_letter)

                        st.download_button("📥 Download Tailored Resume", tailored_resume, file_name="Tailored_Resume.txt")
                        st.download_button("📥 Download Cover Letter", cover_letter, file_name="Cover_Letter.txt")
                    else:
                        st.error("❌ Unexpected output format. Please try again.")
                except Exception as e:
                    st.error(str(e))
    else:
        st.warning("⚠️ Please upload your Resume and paste the Job Description before proceeding!")
