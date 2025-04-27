import streamlit as st
import openai
from datetime import datetime
from fpdf import FPDF

# ✅ Set your Groq/OpenAI Key
openai.api_key = "gsk_WhI4OpClTGCT2LxxvSpMWGdyb3FYBVUkG8jUO0HKpwK6OCylD8U"
openai.api_base = "https://api.groq.com/openai/v1"

# 🧠 AI function to generate ATS-Friendly Resume
def generate_resume(name, title, summary, experiences, skills, education):
    prompt = f"""
    Act as a professional career coach and resume expert.

    Create a highly ATS-optimized and recruiter-friendly RESUME for the following candidate:

    - Full Name: {name}
    - Professional Title: {title}
    - Summary: {summary}
    - Work Experiences: {experiences}
    - Skills (keywords): {skills}
    - Education: {education}

    Strict Instructions:
    - Structure the resume clearly with sections: Summary, Skills, Experience, Education.
    - Use bullet points under each experience (start bullets with strong action verbs like "Managed", "Developed", "Designed", etc.)
    - Match and emphasize skills using the exact keywords provided.
    - Keep formatting simple (no graphics, no fancy tables) for easy ATS parsing.
    - Professional and formal tone.
    - No personal pronouns (no "I", "my", etc.).
    - Keep it under 2 pages if possible.

    Output only the resume text, no extra commentary.
    """
    response = openai.ChatCompletion.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content

# 🧠 AI function to generate ATS-Optimized Cover Letter
def generate_cover_letter(name, title, job_title, company_name, motivation):
    prompt = f"""
    Act as a professional HR expert and write a personalized, ATS-optimized COVER LETTER for a job application.

    Candidate Details:
    - Name: {name}
    - Professional Title: {title}
    - Applying For: {job_title} at {company_name}
    - Motivation: {motivation}

    Strict Instructions:
    - Start with a professional greeting.
    - In the first paragraph, mention enthusiasm for {job_title} at {company_name}.
    - In the second paragraph, highlight relevant skills and achievements matching the role (use the skills as keywords).
    - In the third paragraph, explain motivation and cultural fit for the company.
    - Close with a polite call to action (e.g., looking forward to discussing the opportunity).
    - Formal and professional tone, no unnecessary storytelling.
    - Do not use personal pronouns like "I am excited"; keep it professional but warm.

    Output only the cover letter text, no extra commentary.
    """
    response = openai.ChatCompletion.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return response.choices[0].message.content

# 🧾 PDF Export Function
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'GetHired', ln=True, align='C')
        self.ln(10)

    def add_content(self, title, content):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, ln=True)
        self.ln(4)
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, content)
        self.ln(8)

def create_pdf_file(name, resume, cover_letter):
    pdf = PDF()
    pdf.add_page()
    pdf.add_content("Resume", resume)
    pdf.add_page()
    pdf.add_content("Cover Letter", cover_letter)

    return pdf.output(dest='S').encode('latin1')

# 🏠 Streamlit App
st.set_page_config(page_title="GetHired - Resume & Cover Letter Generator", page_icon="📝")
st.title("📝 GetHired - Resume & Cover Letter Generator")
st.caption("Create ATS-optimized resumes and cover letters in seconds.")

st.markdown("---")

st.subheader("📄 Enter Your Details")

# Form to capture user input
with st.form("user_info_form"):
    name = st.text_input("Full Name")
    title = st.text_input("Professional Title (e.g., Software Engineer)")
    summary = st.text_area("Professional Summary")
    experiences = st.text_area("Work Experiences (list briefly)")
    skills = st.text_area("Skills (comma separated)")
    education = st.text_area("Education (degrees, certifications)")

    st.markdown("---")
    st.subheader("✉️ Cover Letter Details")
    job_title = st.text_input("Job Title Applying For")
    company_name = st.text_input("Company Name")
    motivation = st.text_area("Why do you want this job?")

    submitted = st.form_submit_button("🚀 Generate Resume & Cover Letter")

# After submitting
if submitted:
    if not name.strip() or not job_title.strip():
        st.warning("⚠️ Please complete all fields before submitting!")
    else:
        with st.spinner("✍️ Writing your Resume and Cover Letter..."):
            resume = generate_resume(name, title, summary, experiences, skills, education)
            cover_letter = generate_cover_letter(name, title, job_title, company_name, motivation)

        st.success("✅ Done! Here are your documents:")

        st.markdown("---")

        st.subheader("📄 Your Resume:")
        st.code(resume)

        st.subheader("✉️ Your Cover Letter:")
        st.code(cover_letter)

        # Download buttons (TXT)
        st.download_button("📥 Download Resume (TXT)", resume, file_name=f"{name.replace(' ', '_')}_Resume.txt")
        st.download_button("📥 Download Cover Letter (TXT)", cover_letter, file_name=f"{name.replace(' ', '_')}_CoverLetter.txt")

        # Generate combined PDF
        pdf_bytes = create_pdf_file(name, resume, cover_letter)
        st.download_button(
            "📥 Download Full PDF (Resume + Cover Letter)",
            pdf_bytes,
            file_name=f"{name.replace(' ', '_')}_Application.pdf",
            mime="application/pdf"
        )

        st.markdown("---")

        st.info("💬 Want premium features like PDF styling, AI job matching, and expert resume reviews? Coming soon!")
