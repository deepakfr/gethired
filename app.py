import streamlit as st
import openai
import pdfplumber
import docx
from io import BytesIO

# ✅ Set your Groq/OpenAI Key
openai.api_key = "gsk_WhI4OpClTGCT2LxxvSpMWGdyb3FYBVUkG8jUO0HKpwK6OCylD8U"
openai.api_base = "https://api.groq.com/openai/v1"

# 🧠 Read file content
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

# 🧠 AI function to tailor Resume and Cover Letter
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
    response = openai.ChatCompletion.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content

# 🏠 Streamlit App
st.set_page_config(page_title="GetHired - Tailor My Resume", page_icon="📝")
st.title("📝 GetHired - Tailor My Resume")
st.caption("Upload your Resume (PDF or DOC) + Job Description (PDF or DOC). Get a tailored resume and cover letter!")

st.markdown("---")

# Upload section
st.subheader("📄 Upload Files")
existing_resume_file = st.file_uploader("Upload Your Current Resume (PDF, DOC, or TXT)", type=["pdf", "docx", "txt"])
job_description_file = st.file_uploader("Upload the Job Description (PDF, DOC, or TXT)", type=["pdf", "docx", "txt"])

if st.button("🚀 Tailor Resume & Create Cover Letter"):
    if existing_resume_file and job_description_file:
        existing_resume = extract_text(existing_resume_file)
        job_description = extract_text(job_description_file)

        if not existing_resume.strip() or not job_description.strip():
            st.error("❌ Could not extract text properly. Please check the files.")
        else:
            with st.spinner("✍️ Tailoring your Resume and writing your Cover Letter..."):
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
    else:
        st.warning("⚠️ Please upload both files before proceeding!")
