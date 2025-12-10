import streamlit as st
import google.generativeai as genai
from docx import Document
import requests
from bs4 import BeautifulSoup
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Resume Optimizer", page_icon="📄")

# Access API Key from Secrets
# (Make sure your Streamlit Secrets are set up correctly!)
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # Using the standard Flash model. If this gives an error, switch to 'gemini-pro'
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Error: Could not connect to Google AI. Check your API Key in Streamlit Secrets.")

# --- 2. CUSTOM DESIGN (CSS) ---
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* Style the Header */
    h1 {
        color: #4F8BF9; /* Electric Blue */
        text-align: center;
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    /* Style the Subheader text */
    .stMarkdown p {
        text-align: center;
        color: #b0b0b0;
    }

    /* Style the Optimize button */
    .stButton>button {
        width: 100%;
        background-color: #4F8BF9;
        color: white;
        border-radius: 12px;
        height: 50px;
        font-size: 18px;
        font-weight: 600;
        border: none;
        box-shadow: 0px 4px 15px rgba(79, 139, 249, 0.4);
        margin-top: 20px;
    }
    .stButton>button:hover {
        background-color: #3b6ccf;
        transform: translateY(-2px);
    }
    
    /* Green Download Button */
    .stDownloadButton>button {
        width: 100%;
        background-color: #00CC66;
        color: white;
        border-radius: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def read_word_doc(file):
    try:
        doc = Document(file)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except:
        return "Error reading document."

def create_docx(text):
    doc = Document()
    doc.add_heading('Optimized Resume', 0)
    for line in text.split('\n'):
        doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def scrape_url(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator=' ')
            return " ".join(text.split())
        else:
            return None
    except:
        return None

# --- 4. THE APP UI ---

# THIS WAS MISSING IN YOUR SCREENSHOT:
st.title("📄 AI Resume Optimizer")
st.markdown("Upload your current resume and a job description. The AI will rewrite it for you.")

# Sidebar
with st.sidebar:
    st.header("Step 1: Your Resume")
    uploaded_file = st.file_uploader("Upload Word Doc (.docx)", type=['docx'])
    
    st.header("Step 2: Job Description")
    jd_option = st.radio("Choose Input Method:", ["Paste Text", "Job Website URL"])
    
    jd_text = ""
    if jd_option == "Paste Text":
        jd_text = st.text_area("Paste Job Description Here", height=200)
    else:
        jd_url = st.text_input("Paste Job URL Here")
        if st.button("Fetch Job Data"):
            if jd_url:
                with st.spinner("Reading website..."):
                    fetched_data = scrape_url(jd_url)
                    if fetched_data:
                        jd_text = fetched_data
                        st.success("Job data loaded!")
                    else:
                        st.error("Could not read URL.")

    st.header("Step 3: Choose Mode")
    mode = st.radio("Goal:", ["Full Resume Rewrite", "ATS Optimization Check"])

# Main Logic
if st.button("✨ Optimize My CV"):
    if not uploaded_file:
        st.warning("Please upload a Resume.")
    elif not jd_text:
        st.warning("Please provide a Job Description.")
    else:
        resume_text = read_word_doc(uploaded_file)
        
        # The PROMPT Logic
        final_prompt = ""
        if mode == "Full Resume Rewrite":
            final_prompt = f"""
            Act as an expert Resume Writer. 
            STRICTLY OUTPUT ONLY THE RESUME CONTENT. 
            DO NOT Include conversational filler like "Here is the draft" or "I have optimized the resume".
            Start directly with the Candidate Name.
            
            Generate a full resume draft tailored to this job description. 
            Use my existing resume as a base for experience and skills.
            Focus on highlighting the most relevant qualifications and incorporating keywords.
            
            My Resume: {resume_text}
            Job Description: {jd_text}
            """
        else:
            final_prompt = f"""
            Act as an ATS (Applicant Tracking System) Specialist.
            Optimize my current resume by incorporating relevant keywords from the job description.
            
            My Resume: {resume_text}
            Job Description: {jd_text}
            
            Provide output as:
            1. List of Missing Keywords
            2. Rewritten Bullet Points
            """

        with st.spinner("AI is working its magic..."):
            try:
                response = model.generate_content(final_prompt)
                
                st.subheader("Your Optimized Result")
                st.markdown(response.text)
                
                # Download Button
                st.success("Done! Download your file below.")
                docx_file = create_docx(response.text)
                
                st.download_button(
                    label="📥 Download as Word Doc",
                    data=docx_file,
                    file_name="Optimized_Resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
            except Exception as e:
                st.error(f"AI Error: {e}")
