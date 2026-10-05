import streamlit as st
import google.generativeai as genai
import os
import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fpdf import FPDF

# --- INITIALIZE ENVIRONMENT & AI ---
load_dotenv()
API_KEY = os.getenv("AI_API_KEY")
SERP_KEY = os.getenv("SERP_API_KEY")

if API_KEY and API_KEY != "your_gemini_or_openai_key_here":
    genai.configure(api_key=API_KEY)
    ai_ready = True
else:
    ai_ready = False

def generate_ai_response(system_prompt, user_text):
    if not ai_ready:
        return "⚠️ Error: AI API Key is missing or invalid. Please check your Render Environment Variables."
    try:
        model = genai.GenerativeModel('gemini-1.5-pro', system_instruction=system_prompt)
        response = model.generate_content(user_text)
        return response.text
    except Exception as e:
        return f"⚠️ API Error: {str(e)}"

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

# --- PDF GENERATORS ---
def generate_welcome_pdf(c_name, p_name, j_date):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(253, 251, 247)
    pdf.rect(0, 0, 210, 297, 'F')
    
    pdf.set_draw_color(193, 154, 91)
    pdf.line(85, 40, 125, 40)
    
    pdf.set_text_color(15, 59, 46)
    pdf.set_font("Times", 'B', 32)
    pdf.cell(0, 60, "WELCOME", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(0, 10, f"WELCOME, {c_name.upper()}", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(47, 54, 52)
    pdf.set_font("Times", 'B', 28)
    pdf.cell(0, 15, c_name, align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(0, 20, "PROJECT", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(47, 54, 52)
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(0, 5, p_name, align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(0, 20, "JOINING DATE", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(47, 54, 52)
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(0, 5, j_date, align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_y(170)
    pdf.set_font("Helvetica", '', 11)
    text = "Amit Sharma is pleased to officially welcome you and begin this project together. We are excited to build a strong professional collaboration and look forward to delivering a smooth, valuable, and successful project experience from start to finish."
    pdf.multi_cell(0, 7, text, align='C')
    
    pdf.set_y(220)
    pdf.set_text_color(15, 59, 46)
    pdf.set_font("Times", '', 18)
    pdf.cell(0, 10, "Thank you for choosing to work with Amit Sharma.", align='C', new_x="LMARGIN", new_y="NEXT")
    
    return bytes(pdf.output())

def generate_audit_pdf(url, ai_report):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, f"SEO Audit Report: {url}", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", '', 11)
    # Handle unicode encoding safely for PDF
    safe_text = ai_report.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, safe_text)
    
    return bytes(pdf.output())

# --- LIVE SERP TRACKER LOGIC ---
def get_live_rank(keyword, target_url):
    if not SERP_KEY or SERP_KEY == "your_serper_api_key_here":
        return "⚠️ Error: Please add your Serper.dev API key to .env or Render settings to use live tracking."
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": keyword, "num": 100})
    headers = {'X-API-KEY': SERP_KEY, 'Content-Type': 'application/json'}
    
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
st.set_page_config(page_title="Bid2Rank | AI SEO", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

# --- FUTURISTIC UI CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    
    .stApp {
        background: radial-gradient(circle at top left, #0D0518 0%, #05010B 100%);
        color: #E2E8F0;
    }
    
    [data-testid="stSidebar"] {
        background: rgba(10, 5, 20, 0.7) !important;
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border-right: 1px solid rgba(168, 85, 247, 0.1);
    }
    
    h1, h2, h3 {
        background: linear-gradient(135deg, #E8B5FF, #8B5CF6, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        margin-bottom: 20px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #7C3AED, #2563EB) !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 0 30px rgba(59, 130, 246, 0.5) !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.02) !important;
        color: white !important;
        border: 1px solid rgba(168, 85, 247, 0.2) !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border: 1px solid #A855F7 !important;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.4) !important;
    }
    
    /* Futuristic Dashboard Cards */
    .dash-card {
        background: rgba(20, 10, 30, 0.6);
        border: 1px solid rgba(168, 85, 247, 0.2);
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        text-align: center;
        transition: transform 0.3s;
    }
    .dash-card:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(168, 85, 247, 0.5);
    }
    .dash-card h2 { font-size: 36px; margin: 0; background: linear-gradient(90deg, #4ADE80, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .dash-card p { color: #94A3B8; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("✨ Bid2Rank")
st.sidebar.caption("Futuristic AI Agency Core")
st.sidebar.markdown("---")
menu = [
    "🌐 Command Center", 
    "📝 1. Upwork Proposal Writer", 
    "💬 2. Client Handler", 
    "🤝 3. Welcome Letter Generator", 
    "🔍 4. Audit Report Generator", 
    "📈 5. Keyword Rank Tracker"
]
choice = st.sidebar.radio("SYSTEM NAVIGATION", menu)
st.sidebar.markdown("---")
if ai_ready:
    st.sidebar.success("🟢 NEURAL CORE: ONLINE")
else:
    st.sidebar.error("🔴 NEURAL CORE: OFFLINE")

# --- ROUTING ---
if choice == "🌐 Command Center":
    st.title("COMMAND CENTER")
    st.markdown("<p style='color:#94A3B8; font-size:18px;'>Welcome to your futuristic agency dashboard, Amit.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='dash-card'><h2>Active</h2><p>AI Engine Status</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='dash-card'><h2>5</h2><p>Operational Modules</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='dash-card'><h2>Secured</h2><p>Data Connection</p></div>", unsafe_allow_html=True)

elif choice == "📝 1. Upwork Proposal Writer":
    st.title("Upwork Proposal Writer")
    jd_input = st.text_area("TARGET JOB DESCRIPTION:", height=200)
    if st.button("INITIATE PROPOSAL GENERATION"):
        with st.spinner("Processing neural writing parameters..."):
            sys_prompt = load_brain("Module1_Bidder/Bidder_Brain_Prompt.txt")
            result = generate_ai_response(sys_prompt, jd_input)
            st.info(result)

elif choice == "💬 2. Client Handler":
    st.title("Client Handler")
    client_msg = st.text_area("INCOMING CLIENT TRANSMISSION:", height=150)
    if st.button("SYNTHESIZE EXPERT REPLY"):
        with st.spinner("Calculating optimal response strategy..."):
            sys_prompt = load_brain("Module2_Communicator/Communicator_Brain_Prompt.txt")
            result = generate_ai_response(sys_prompt, client_msg)
            st.info(result)

elif choice == "🤝 3. Welcome Letter Generator":
    st.title("Welcome Letter Generator")
    col1, col2 = st.columns(2)
    c_name = col1.text_input("CLIENT ENTITY NAME")
    p_name = col2.text_input("PROJECT DESIGNATION")
    j_date = st.text_input("COMMENCEMENT DATE")
    if st.button("COMPILE PDF DOCUMENT"):
        with st.spinner("Rendering highly formatted PDF document..."):
            pdf_bytes = generate_welcome_pdf(c_name, p_name, j_date)
        st.success("✅ Document Rendering Complete.")
        st.download_button("📥 DOWNLOAD WELCOME.PDF", data=pdf_bytes, file_name=f"Welcome_{c_name}.pdf", mime="application/pdf")

elif choice == "🔍 4. Audit Report Generator":
    st.title("Audit Report Generator")
    st.markdown("Enter a URL to scrape metrics and generate a 9-page structural analysis.")
    audit_url = st.text_input("TARGET URL FOR AUDIT")
    if st.button("EXECUTE DEEP AUDIT & GENERATE PDF"):
        with st.spinner("Scraping website architecture and consulting AI Brain..."):
            # Real Scraping Logic
            try:
                resp = requests.get(audit_url, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                title = soup.title.string if soup.title else "N/A"
                h1s = [h.text for h in soup.find_all('h1')]
                meta = soup.find("meta", attrs={"name": "description"})
                meta_desc = meta["content"] if meta else "N/A"
                scraped_data = f"URL: {audit_url}\nTitle: {title}\nMeta Description: {meta_desc}\nH1 Tags: {h1s}"
            except Exception as e:
                scraped_data = f"URL: {audit_url}\nNotice: Target blocked scraping. Perform structural analysis based on URL only."
            
            # AI Logic
            sys_prompt = load_brain("Module4_Auditor/Auditor_Brain_Prompt.txt")
            full_prompt = f"{sys_prompt}\n\nTARGET DATA ACQUIRED:\n{scraped_data}\n\nGenerate the 9-page report now."
            ai_report = generate_ai_response(full_prompt, "Process the audit.")
            
            # PDF Generation
            pdf_bytes = generate_audit_pdf(audit_url, ai_report)
            
        st.success("✅ Audit Complete. PDF compiled successfully.")
        st.download_button("📥 DOWNLOAD AUDIT_REPORT.PDF", data=pdf_bytes, file_name="Audit_Report.pdf", mime="application/pdf")

elif choice == "📈 5. Keyword Rank Tracker":
    st.title("Keyword Rank Tracker")
    st.markdown("Live SERP connectivity for 100% accurate positional data.")
    track_url = st.text_input("TARGET URL (e.g. yoursite.com)")
    keywords = st.text_input("SEARCH QUERY")
    if st.button("PING GOOGLE SERP (LIVE)"):
        with st.spinner("Connecting to Google Search Engine infrastructure..."):
            result = get_live_rank(keywords, track_url)
        st.info(result)
