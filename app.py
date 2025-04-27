import streamlit as st
import pdfplumber
import docx
from docx import Document
from fpdf import FPDF
import requests
from io import BytesIO
import unicodedata

# ✅ Set your Groq API Key
GROQ_API_KEY = "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"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# 🧠 Function to extract text from uploaded file
def extract_text(file):
    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
        return text
    elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        return file.read().decode("utf-8")

# 🧠 Sanitize text for PDF
def sanitize_text(text):
    return unicodedata.normalize('NFKD', text).encode('latin-1', 'ignore').decode('latin-1')

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

# 📄 Create DOCX file
def create_docx(resume, cover_letter):
    doc = Document()
    doc.add_heading('Tailored Resume', 0)
    doc.add_paragraph(resume)
    doc.add_page_break()
    doc.add_heading('Cover Letter', 0)
    doc.add_paragraph(cover_letter)

    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

# 📄 Create PDF file
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'GetHired Resume & Cover Letter', ln=True, align='C')
        self.ln(10)

    def add_content(self, title, content):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, ln=True)
        self.ln(4)
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, content)
        self.ln(8)

def create_pdf(resume, cover_letter):
    pdf = PDF()
    pdf.add_page()
    pdf.add_content("Tailored Resume", sanitize_text(resume))
    pdf.add_page()
    pdf.add_content("Cover Letter", sanitize_text(cover_letter))

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return pdf_bytes

# 🏠 Streamlit App
st.set_page_config(page_title="GetHired - Tailor My Resume", page_icon="📝")
st.title("📝 GetHired - Tailor My Resume")
st.caption("Upload your Resume (PDF, DOC, or TXT) + Paste the Job Description. Get a tailored Resume and Cover Letter!")

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

                        # Create DOCX and PDF
                        docx_file = create_docx(tailored_resume, cover_letter)
                        pdf_file = create_pdf(tailored_resume, cover_letter)

                        # Download buttons
                        st.download_button(
                            "📥 Download DOCX (Word)",
                            data=docx_file,
                            file_name="Tailored_Resume_and_CoverLetter.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                        st.download_button(
                            "📥 Download PDF (Professional)",
                            data=pdf_file,
                            file_name="Tailored_Resume_and_CoverLetter.pdf",
                            mime="application/pdf"
                        )

                    else:
                        st.error("❌ Unexpected output format. Please try again.")
                except Exception as e:
                    st.error(str(e))
    else:
        st.warning("⚠️ Please upload your Resume and paste the Job Description before proceeding!")
