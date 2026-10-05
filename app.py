import streamlit as st
import google.generativeai as genai
import os
import requests
import json
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fpdf import FPDF

# --- INITIALIZE ENVIRONMENT ---
load_dotenv()
API_KEY = os.getenv("AI_API_KEY")

if API_KEY and API_KEY != "your_gemini_or_openai_key_here":
    genai.configure(api_key=API_KEY)
    ai_ready = True
else:
    ai_ready = False

# FIX: Changed model to 'gemini-1.5-pro-latest' to fix the 404 error
def generate_ai_response(system_prompt, user_text):
    if not ai_ready:
        return "⚠️ Error: AI API Key is missing."
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest', system_instruction=system_prompt)
        response = model.generate_content(user_text)
        return response.text
    except Exception as e:
        # Fallback to standard gemini-pro if 1.5 fails
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(system_prompt + "\n\n" + user_text)
            return response.text
        except Exception as e2:
            return f"⚠️ API Error: {str(e2)}"

def load_brain(filepath):
    filename = filepath.split('/')[-1]
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "Error: Brain prompt file not found."

# --- PREMIUM PDF GENERATORS ---
def generate_welcome_pdf(c_name, p_name, j_date):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(253, 251, 247) # Beige background
    pdf.rect(0, 0, 210, 297, 'F')
    
    # Gold Line
    pdf.set_draw_color(193, 154, 91)
    pdf.set_line_width(0.5)
    pdf.line(85, 40, 125, 40)
    
    pdf.set_y(50)
    pdf.set_text_color(15, 59, 46) # Dark Green
    pdf.set_font("Times", 'B', 32)
    pdf.cell(0, 10, "WELCOME", align='C', ln=True)
    
    pdf.line(85, 70, 125, 70)
    
    pdf.set_y(90)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(0, 5, f"WELCOME, {c_name.upper()}", align='C', ln=True)
    
    pdf.set_text_color(47, 54, 52)
    pdf.set_font("Times", 'B', 32)
    pdf.cell(0, 15, c_name, align='C', ln=True)
    
    pdf.set_y(130)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(0, 5, "PROJECT", align='C', ln=True)
    
    pdf.set_text_color(47, 54, 52)
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(0, 8, p_name, align='C', ln=True)
    
    pdf.set_y(160)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(0, 5, "JOINING DATE", align='C', ln=True)
    
    pdf.set_text_color(47, 54, 52)
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(0, 8, j_date, align='C', ln=True)
    
    pdf.set_y(200)
    pdf.set_font("Helvetica", '', 11)
    text = "Amit Sharma is pleased to officially welcome you and begin this project together. We are excited to build a strong professional collaboration and look forward to delivering a smooth, valuable, and successful project experience from start to finish."
    pdf.multi_cell(0, 6, text, align='C')
    
    pdf.set_y(250)
    pdf.set_text_color(15, 59, 46)
    pdf.set_font("Times", '', 18)
    pdf.cell(0, 10, "Thank you for choosing to work with Amit Sharma.", align='C', ln=True)
    
    return bytes(pdf.output())

def generate_audit_pdf(url, ai_report):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Cover Page (Dark Theme)
    pdf.add_page()
    pdf.set_fill_color(22, 22, 22) # Dark background like the Figma design
    pdf.rect(0, 0, 210, 297, 'F')
    
    pdf.set_y(100)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", 'B', 30)
    pdf.cell(0, 15, "Website Audit Report", align='L', ln=True)
    
    pdf.set_text_color(200, 150, 50) # Gold Accent
    pdf.set_font("Times", 'I', 36)
    pdf.cell(0, 15, url, align='L', ln=True)
    
    pdf.set_y(250)
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 10, "Prepared by Amit Sharma | SEO & Website Audit Specialist", align='L', ln=True)
    
    # Content Pages (Light theme for readability, similar to their report)
    pdf.add_page()
    pdf.set_fill_color(245, 240, 235) # Off-white background
    pdf.rect(0, 0, 210, 297, 'F')
    
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", '', 11)
    safe_text = ai_report.encode('latin-1', 'replace').decode('latin-1')
    
    # Split text by newlines and add to PDF
    for line in safe_text.split('\n'):
        if "--- PAGE" in line or "---" in line:
            pdf.add_page()
            pdf.set_fill_color(245, 240, 235)
            pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_font("Helvetica", 'B', 16)
            pdf.set_text_color(200, 100, 50)
            pdf.cell(0, 15, line.replace("---", "").strip(), ln=True)
            pdf.set_font("Helvetica", '', 11)
            pdf.set_text_color(30, 30, 30)
        else:
            pdf.multi_cell(0, 7, line)
            
    return bytes(pdf.output())

# --- LIVE SERP TRACKER LOGIC ---
def get_live_rank(keyword, target_url, serp_key):
    if not serp_key:
        return "⚠️ Error: Please enter your Serper.dev API key below to fetch live Google data."
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": keyword, "num": 100})
    headers = {'X-API-KEY': serp_key, 'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=payload)
        data = response.json()
        if "organic" in data:
            for res in data["organic"]:
                if target_url.lower() in res.get("link", "").lower():
                    page = (res['position'] - 1) // 10 + 1
                    return f"🎯 **RANK FOUND!** Your URL is currently at **Position #{res['position']}** (Page {page}) on Google."
            return f"❌ **Not Found:** The URL is not in the Top 100 results for '{keyword}'."
        return "⚠️ Error: Invalid response from Google."
    except Exception as e:
        return f"⚠️ API Connection Error: {str(e)}"

# --- PORTAL CONFIGURATION ---
st.set_page_config(page_title="Bid2Rank | Pro SEO Suite", page_icon="⚡", layout="wide")

# --- NEW FULL-WIDTH UI CSS (REMOVED SIDEBAR) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="collapsedControl"] { display: none; }
    
    /* Clean Dark Background */
    .stApp { background-color: #0A0A0F; color: #F8FAFC; }
    
    /* Top Navigation Tabs Styling */
    div[data-testid="stRadio"] > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        background: #111118;
        padding: 10px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        flex-wrap: wrap;
    }
    
    /* Headers */
    h1 { color: #FFFFFF; font-weight: 800; font-size: 2.5rem; margin-bottom: 1rem; }
    h2, h3 { color: #94A3B8; font-weight: 600; }
    
    /* Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border: 1px solid #3B82F6 !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: #2563EB !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 15px 30px !important;
        font-weight: 600 !important;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover { background: #1D4ED8 !important; transform: translateY(-2px); }
    </style>
""", unsafe_allow_html=True)

# --- TOP NAVIGATION ---
st.markdown("<h1 style='text-align: center; color: #FFFFFF;'>⚡ Bid2Rank Agency Suite</h1>", unsafe_allow_html=True)

menu = [
    "Upwork Proposal Writer", 
    "Client Handler", 
    "Welcome Letter Generator", 
    "Audit Report Generator", 
    "Keyword Rank Tracker"
]
choice = st.radio("", menu, horizontal=True)
st.markdown("---")

# --- ROUTING ---
if choice == "Upwork Proposal Writer":
    st.markdown("### 📝 Upwork Proposal Writer")
    jd_input = st.text_area("Paste Target Job Description:", height=200)
    if st.button("Generate Expert Proposal"):
        with st.spinner("Analyzing JD & Writing..."):
            sys_prompt = load_brain("Module1_Bidder/Bidder_Brain_Prompt.txt")
            st.info(generate_ai_response(sys_prompt, jd_input))

elif choice == "Client Handler":
    st.markdown("### 💬 Client Handler")
    client_msg = st.text_area("Paste Incoming Client Message:", height=150)
    if st.button("Synthesize Expert Reply"):
        with st.spinner("Drafting Response..."):
            sys_prompt = load_brain("Module2_Communicator/Communicator_Brain_Prompt.txt")
            st.info(generate_ai_response(sys_prompt, client_msg))

elif choice == "Welcome Letter Generator":
    st.markdown("### 🤝 Welcome Letter Generator")
    col1, col2 = st.columns(2)
    c_name = col1.text_input("Client Name (e.g. Robert)")
    p_name = col2.text_input("Project Name (e.g. Website SEO & Digital Growth)")
    j_date = st.text_input("Joining Date (e.g. 05 October 2026)")
    
    if st.button("Generate Professional Welcome PDF"):
        with st.spinner("Rendering PDF..."):
            pdf_bytes = generate_welcome_pdf(c_name, p_name, j_date)
            st.success("✅ Document Rendered!")
            st.download_button("📥 DOWNLOAD WELCOME.PDF", data=pdf_bytes, file_name=f"Welcome_{c_name}.pdf", mime="application/pdf")

elif choice == "Audit Report Generator":
    st.markdown("### 🔍 Audit Report Generator")
    st.markdown("*(Note: Deep auditing takes 30-60 seconds. The AI will scrape the site and generate a multi-page PDF).*")
    audit_url = st.text_input("Target Website URL")
    
    if st.button("Execute Deep Audit & Generate PDF"):
        progress_text = "Operation in progress. Please wait."
        my_bar = st.progress(0, text="Starting scraping protocol...")
        
        # 1. Scraping
        try:
            my_bar.progress(30, text="Scraping website meta data & H1 tags...")
            resp = requests.get(audit_url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.title.string if soup.title else "N/A"
            h1s = [h.text.strip() for h in soup.find_all('h1')]
            meta = soup.find("meta", attrs={"name": "description"})
            meta_desc = meta["content"] if meta else "N/A"
            scraped_data = f"URL: {audit_url}\nTitle: {title}\nMeta Description: {meta_desc}\nH1 Tags: {h1s}"
        except Exception:
            scraped_data = f"URL: {audit_url}\nNotice: Target blocked scraping. Performing structural analysis based on URL only."
            
        # 2. AI Analysis
        my_bar.progress(60, text="Analyzing 7-point SEO checklist with AI...")
        sys_prompt = load_brain("Module4_Auditor/Auditor_Brain_Prompt.txt")
        full_prompt = f"{sys_prompt}\n\nTARGET DATA ACQUIRED:\n{scraped_data}\n\nStrictly format output into 9 sections (--- PAGE 1 ---, etc.)"
        ai_report = generate_ai_response(full_prompt, "Process the audit.")
        
        # 3. PDF Generation
        my_bar.progress(90, text="Compiling dark-theme PDF report...")
        pdf_bytes = generate_audit_pdf(audit_url, ai_report)
        
        my_bar.progress(100, text="Audit Complete!")
        st.success("✅ Audit Complete. PDF compiled successfully.")
        st.download_button("📥 DOWNLOAD AUDIT_REPORT.PDF", data=pdf_bytes, file_name="Audit_Report.pdf", mime="application/pdf")

elif choice == "Keyword Rank Tracker":
    st.markdown("### 📈 Keyword Rank Tracker")
    st.warning("To get accurate live data, you must provide a free Serper.dev API key.")
    manual_serp_key = st.text_input("Enter your Serper.dev API Key (Get from serper.dev):", type="password")
    
    track_url = st.text_input("Target URL (e.g. yoursite.com)")
    keywords = st.text_input("Search Query")
    
    if st.button("Ping Google SERP (Live)"):
        with st.spinner("Scanning Google Top 100..."):
            # Use manual key if provided, else try env
            active_key = manual_serp_key if manual_serp_key else SERP_KEY
            result = get_live_rank(keywords, track_url, active_key)
        st.info(result)
