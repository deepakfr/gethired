import streamlit as st
import pdfplumber
import docx
from docx import Document
from fpdf import FPDF
import requests
import smtplib
from email.message import EmailMessage
from io import BytesIO
import unicodedata

# ✅ Set your Groq API Key
GROQ_API_KEY = "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"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# ✅ Set your Email credentials
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465
SENDER_EMAIL = 'yourcompanyemail@gmail.com'  # 👈 Your sender Gmail
SENDER_PASSWORD = 'yourapppassword'          # 👈 App password (not regular Gmail password!)

# 🧠 Extract Text
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

# 🧠 Unicode Safe Text
def sanitize_text(text):
    return unicodedata.normalize('NFKD', text).encode('latin-1', 'ignore').decode('latin-1')

# 🧠 Call Groq API
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
        "messages": [{"role": "system", "content": "You are a helpful AI assistant."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        raise Exception(f"❌ Error from Groq API: {response.status_code} - {response.text}")

# 📄 Create DOCX
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

# 📄 Create Beautiful PDF
class BeautifulPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(30, 30, 30)
        self.cell(0, 15, 'GetHired - Resume & Cover Letter', ln=True, align='C')
        self.ln(10)

    def add_section_title(self, title):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(0, 102, 204)
        self.cell(0, 10, title, ln=True)
        self.ln(5)

    def add_body_text(self, content):
        self.set_font('Helvetica', '', 12)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 8, content)
        self.ln(8)

def create_beautiful_pdf(resume, cover_letter):
    pdf = BeautifulPDF()
    pdf.add_page()
    pdf.add_section_title("Tailored Resume")
    pdf.add_body_text(sanitize_text(resume))
    pdf.add_page()
    pdf.add_section_title("Cover Letter")
    pdf.add_body_text(sanitize_text(cover_letter))
    return pdf.output(dest='S').encode('latin1')

# 📧 Email with Attachments
def send_email_with_attachments(to_email, docx_data, pdf_data):
    msg = EmailMessage()
    msg['Subject'] = "Your Tailored Resume & Cover Letter from GetHired 🎯"
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    msg.set_content("Hi there!\n\nPlease find attached your Tailored Resume and Cover Letter. Best of luck! 🚀\n\n- GetHired Team")

    # Attach DOCX
    msg.add_attachment(docx_data.getvalue(), maintype='application', subtype='vnd.openxmlformats-officedocument.wordprocessingml.document', filename="Tailored_Resume_and_CoverLetter.docx")
    # Attach PDF
    msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename="Tailored_Resume_and_CoverLetter.pdf")

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

# 🏠 Streamlit App
st.set_page_config(page_title="GetHired - Tailor My Resume", page_icon="📝")
st.title("📝 GetHired - Tailor My Resume")
st.caption("Upload your Resume (PDF, DOC, or TXT) + Paste the Job Description. Get a tailored Resume and Cover Letter!")

st.markdown("---")

# Upload and Input
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

                    if "### Cover Letter" in output:
                        tailored_resume, cover_letter = output.split("### Cover Letter")
                        tailored_resume = tailored_resume.replace("### Tailored Resume", "").strip()
                        cover_letter = cover_letter.strip()

                        # Create DOCX and Beautiful PDF
                        docx_file = create_docx(tailored_resume, cover_letter)
                        pdf_file = create_beautiful_pdf(tailored_resume, cover_letter)

                        st.success("✅ Your Resume & Cover Letter are ready!")

                        st.download_button(
                            "📥 Download DOCX (Word)",
                            data=docx_file,
                            file_name="Tailored_Resume_and_CoverLetter.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                        st.download_button(
                            "📥 Download PDF (Beautiful)",
                            data=pdf_file,
                            file_name="Tailored_Resume_and_CoverLetter.pdf",
                            mime="application/pdf"
                        )

                        # 📧 Ask for Email
                        st.markdown("---")
                        st.subheader("📩 Send to your Email")
                        user_email = st.text_input("Enter your Email address:")

                        if st.button("📤 Email me the Documents"):
                            if user_email:
                                send_email_with_attachments(user_email, docx_file, pdf_file)
                                st.success("🎉 Thank you! Your documents have been emailed to you successfully. Best of luck for your job search!")
                                st.balloons()
                            else:
                                st.warning("⚠️ Please enter a valid email address.")

                    else:
                        st.error("❌ Unexpected output format. Please try again.")
                except Exception as e:
                    st.error(str(e))
    else:
        st.warning("⚠️ Please upload your Resume and paste the Job Description before proceeding!")
