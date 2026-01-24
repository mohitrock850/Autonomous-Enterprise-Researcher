# =========================================================
#  🤖 AUTONOMOUS ENTERPRISE AGENT - ULTIMATE EDITION
# =========================================================

import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass 

import os
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import streamlit as st
import uuid
import shutil
import pandas as pd
import database as db
from dotenv import load_dotenv
from fpdf import FPDF
from crewai import Agent, Task, Crew, Process, LLM
from tools import search_tool
from analysis_tools import code_interpreter, file_lister, pdf_extractor, vision_tool
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="Autonomous Enterprise Agent", page_icon="🤖", layout="wide")
load_dotenv()

try:
    if "ADMIN_EMAIL" in st.secrets:
        os.environ["ADMIN_EMAIL"] = st.secrets["ADMIN_EMAIL"]
    if "ADMIN_PASSWORD" in st.secrets:
        os.environ["ADMIN_PASSWORD"] = st.secrets["ADMIN_PASSWORD"]
except FileNotFoundError:
    pass # Ignore if no secrets file is found (local mode)

db.init_db()

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# --- 2. GLOBAL DESIGN ASSETS ---

# CSS: Unindented to prevent errors
LANDING_CSS = """
<style>
    html { scroll-behavior: smooth; }
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); }
    
    /* FIX FOR TOP CUTOFF: Add padding to the main container */
    .block-container { padding-top: 3rem; padding-bottom: 5rem; max-width: 100%; }
    
    /* --- NAVIGATION --- */
    .nav-container {
        display: flex; justify-content: space-between; align-items: center;
        padding: 15px 40px; background: rgba(15, 23, 42, 0.9);
        backdrop-filter: blur(12px); position: sticky; top: 0; z-index: 999;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        border-radius: 0 0 20px 20px; /* Soft bottom corners */
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .nav-logo { 
        font-size: 2.2rem; font-weight: 800; 
        background: linear-gradient(90deg, #4f46e5, #06b6d4); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        cursor: pointer;
    }
    .nav-links { display: flex; gap: 25px; align-items: center; }
    .nav-link { 
        color: #cbd5e1; text-decoration: none; font-size: 1rem; font-weight: 600; 
        transition: color 0.3s; 
    }
    .nav-link:hover { color: #fff; text-shadow: 0 0 8px rgba(99, 102, 241, 0.6); }
    
    /* --- HERO --- */
    .hero-container { text-align: center; padding: 60px 20px 40px; animation: fadeIn 1.2s ease-out; }
    .hero-title { font-size: 5rem; font-weight: 900; color: white; line-height: 1.1; margin-bottom: 25px; }
    .hero-gradient { background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .hero-subtitle { font-size: 1.5rem; color: #94a3b8; max-width: 800px; margin: 0 auto 40px; }
    
    /* --- CARDS --- */
    .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 30px; margin-top: 40px; }
    .glass-card {
        background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px; padding: 30px; transition: all 0.3s ease;
    }
    .glass-card:hover { transform: translateY(-10px); border-color: #6366f1; background: rgba(30, 41, 59, 0.7); box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
    .icon-box { font-size: 3rem; margin-bottom: 20px; }
    .card-head { font-size: 1.4rem; font-weight: 700; color: white; margin-bottom: 10px; }
    .card-text { color: #cbd5e1; line-height: 1.6; font-size: 1rem; }

    /* --- SECTION HEADERS --- */
    .section-container { max-width: 1200px; margin: 0 auto; padding: 80px 20px; }
    .section-title { font-size: 3rem; font-weight: 800; color: white; text-align: center; margin-bottom: 60px; }
    .section-title span { color: #a855f7; }

    /* --- PRICING --- */
    .price-card { background: linear-gradient(145deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9)); border: 2px solid #6366f1; text-align: center; padding: 60px; border-radius: 30px; max-width: 800px; margin: 0 auto; position: relative; }
    .price-free { font-size: 5rem; font-weight: 800; color: white; margin: 10px 0; text-shadow: 0 0 20px rgba(99, 102, 241, 0.5); }

    /* --- FAQ ACCORDION --- */
    details {
        background: rgba(255,255,255,0.03); border-radius: 12px; margin-bottom: 15px; 
        border: 1px solid rgba(255,255,255,0.05); transition: all 0.3s;
        display: block; /* Ensure block display */
    }
    details:hover { background: rgba(255,255,255,0.06); }
    details > summary {
        padding: 20px; color: white; font-weight: 600; font-size: 1.2rem; cursor: pointer;
        list-style: none; display: flex; justify-content: space-between; align-items: center;
    }
    details > summary::after {
        content: '+'; font-size: 1.5rem; color: #a855f7; transition: transform 0.3s; font-weight: 800;
    }
    details[open] > summary::after { transform: rotate(45deg); color: #ec4899; }
    details > summary::-webkit-details-marker { display: none; }
    
    .faq-a { padding: 0 20px 20px; color: #94a3b8; line-height: 1.6; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px; font-size: 1.1rem; }

    /* --- CONTACT --- */
    .contact-box { background: linear-gradient(90deg, #4f46e5, #ec4899); padding: 50px; border-radius: 20px; text-align: center; margin-top: 40px; }
    
    /* --- ADMIN DASHBOARD --- */
    .admin-card { background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .admin-header { font-size: 1.8rem; font-weight: 700; color: white; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; }
    .admin-stat { font-size: 2.5rem; font-weight: 800; color: #6366f1; }
    .admin-label { color: #94a3b8; font-size: 1rem; text-transform: uppercase; letter-spacing: 1px; }

    /* --- BUTTONS --- */
    div.stButton > button { border-radius: 10px; font-weight: 700; border: none; padding: 0.8rem 1.6rem; transition: transform 0.2s; }
    div.stButton > button:hover { transform: scale(1.05); }
    
    /* Animation */
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>
"""

# HTML Parts - STRICTLY UNINDENTED TO FIX STYLING ERRORS
HERO_HTML = """
<div class="hero-container">
<div class="hero-title">Your Autonomous <br><span class="hero-gradient">AI Workforce</span></div>
<div class="hero-subtitle">Synthesize terabytes of internal documents, analyze real-time market data, and decode complex diagrams—all in a single, secure environment.</div>
</div>
"""

FEATURES_HTML = """
<div id="features" class="section-container">
<div class="section-title">Powerhouse <span>Capabilities</span></div>
<div class="grid-4">
<div class="glass-card">
<div class="icon-box">🧠</div>
<div class="card-head">Vector RAG</div>
<div class="card-text">Upload complex PDFs. The agent indexes every paragraph into a high-speed vector database for instant recall.</div>
</div>
<div class="glass-card">
<div class="icon-box">👁️</div>
<div class="card-head">Vision Analysis</div>
<div class="card-text">Detects, crops, and interprets charts, graphs, and technical diagrams automatically.</div>
</div>
<div class="glass-card">
<div class="icon-box">🌐</div>
<div class="card-head">Live Web</div>
<div class="card-text">Connects to Google Search API to verify internal data against real-time news and market trends.</div>
</div>
<div class="glass-card">
<div class="icon-box">🛡️</div>
<div class="card-head">Secure Core</div>
<div class="card-text">Bank-grade isolation. Each session is sandboxed with strict data wiping protocols.</div>
</div>
</div>
</div>

<div id="pricing" class="section-container">
<div class="section-title">Transparent <span>Pricing</span></div>
<div class="price-card">
<div style="color: #a855f7; letter-spacing: 2px; font-weight: 700;">OPEN SOURCE / BYOK MODEL</div>
<div class="price-free">$0 <span style="font-size:1.5rem; color:#94a3b8">/ month</span></div>
<div class="card-text" style="max-width: 600px; margin: 0 auto; font-size: 1.1rem;">We don't charge you a dime. Simply bring your own API keys (OpenAI & Serper). You only pay for what you use directly to the providers.</div>
</div>
</div>

<div id="faq" class="section-container">
<div class="section-title">Frequently Asked <span>Questions</span></div>
<div class="grid-2">
<details>
<summary>1. Is my data secure?</summary>
<div class="faq-a">Absolutely. We operate on a <strong>Strict Isolation Protocol</strong>.<br><br>1. <strong>Session Sandbox:</strong> Every time you upload a new PDF or refresh the page, the backend completely wipes the temporary 'data' folder.<br>2. <strong>No Training:</strong> Your data is processed in-memory for the duration of the chat and is never used to train our models.</div>
</details>
<details>
<summary>2. Do I need an OpenAI API Key?</summary>
<div class="faq-a">It depends on your preference:<br>- <strong>Cloud Mode (Recommended):</strong> Yes, you need an OpenAI Key (GPT-4o) for the highest quality Vision analysis and Code interpretation.<br>- <strong>Local Mode (Free):</strong> No, you can use Ollama (Phi-3) if you have it installed on your machine. This runs entirely offline.</div>
</details>
<details>
<summary>3. Can I upload multiple files?</summary>
<div class="faq-a">Currently, the Strict Mode supports <strong>one focused PDF at a time</strong>. This design choice ensures maximum accuracy and zero "context bleeding" (where the AI confuses facts from two different documents).</div>
</details>
<details>
<summary>4. What is the 'Vision' capability?</summary>
<div class="faq-a">Standard AI reads text, but ours sees pixels. When you enable Vision:<br>1. The system scans your PDF page-by-page.<br>2. It detects charts, graphs, and diagrams.<br>3. It crops these images and sends them to the Vision Model (GPT-4o) to interpret the data visually.</div>
</details>
<details>
<summary>5. How does Web Search work?</summary>
<div class="faq-a">We integrate with <strong>Serper Dev (Google Search API)</strong>. When the agent realizes internal data is insufficient (e.g., "What is the stock price *today*?"), it autonomously queries Google, reads the top results, and synthesizes the answer.</div>
</details>
<details>
<summary>6. Is this open source?</summary>
<div class="faq-a">Yes! This project is built on top of powerful open-source frameworks: LangChain, CrewAI, and Streamlit. You are free to inspect the code and modify it for your enterprise needs.</div>
</details>
<details>
<summary>7. Can I export the chat?</summary>
<div class="faq-a">Yes! Every response from the agent comes with a <strong>"Download Report"</strong> button. This generates a professional PDF document containing the full answer, formatted for business use.</div>
</details>
<details>
<summary>8. Does it work on mobile?</summary>
<div class="faq-a">Yes, the layout is fully responsive. You can upload documents and chat with your agent from any smartphone or tablet.</div>
</details>
<details>
<summary>9. Who built this?</summary>
<div class="faq-a">This Autonomous Enterprise solution was architected and designed by <strong>Mohit</strong>.</div>
</details>
<details>
<summary>10. How do I reset the memory?</summary>
<div class="faq-a">You have two options:<br>1. Click the <strong>"Clear All History"</strong> button in the sidebar.<br>2. Simply refresh the browser tab to start a completely fresh session.</div>
</details>
</div>
</div>

<div id="contact" class="section-container">
<div class="contact-box">
<div style="font-size: 2rem; font-weight: 700; color: white;">Deployed & Ready?</div>
<div style="font-size: 1.2rem; color: rgba(255,255,255,0.9); margin-top: 10px;">Contact us for Enterprise Support or Custom Features</div>
<div style="font-size: 2.2rem; font-weight: 800; color: white; margin-top: 20px;">Mohit</div>
<div style="font-size: 1.3rem; color: white; opacity: 0.9; margin-top: 5px;">mohittherockers@gmail.com</div>
</div>
</div>

<div style="text-align: center; margin-top: 50px; padding-bottom: 50px; color: #475569;">
© 2025 Autonomous Enterprise Solutions • Built with ❤️ by Mohit
</div>
"""

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "auth_mode" not in st.session_state: st.session_state.auth_mode = False 
if "user_email" not in st.session_state: st.session_state.user_email = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "is_admin" not in st.session_state: st.session_state.is_admin = False
if "admin_mode" not in st.session_state: st.session_state.admin_mode = False
if "current_session_id" not in st.session_state: st.session_state.current_session_id = str(uuid.uuid4())
if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. HELPER FUNCTIONS ---

def get_llm(model_choice, user_api_key):
    if model_choice == "OpenAI (GPT-4o)":
        final_key = user_api_key if user_api_key else os.getenv("OPENAI_API_KEY")
        if not final_key: return None
        os.environ["OPENAI_API_KEY"] = final_key
        return LLM(model="gpt-4o", temperature=0)
    else:
        return LLM(model="ollama/phi3", base_url="http://localhost:11434")

def generate_pdf_report(content, filename="report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    safe_content = content.encode('latin-1', 'replace').decode('latin-1')
    for line in safe_content.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

# --- 5. AGENT LOGIC ---

def run_simple_chat(user_question, chat_history_context, llm_instance):
    chatbot = Agent(
        role='Helpful Assistant',
        goal='Answer the user question directly and concisely.',
        backstory="You are a helpful AI assistant.",
        llm=llm_instance
    )
    task = Task(description=f"User: {user_question}\nContext: {chat_history_context}", expected_output="Response.", agent=chatbot)
    crew = Crew(agents=[chatbot], tasks=[task], process=Process.sequential)
    return crew.kickoff()

def run_crew_logic(user_question, chat_history_context, llm_instance, specific_file, use_vision, use_web, target_url, serper_key):
    researcher_tools = [search_tool, file_lister, pdf_extractor]
    if use_web and serper_key:
        os.environ["SERPER_API_KEY"] = serper_key
        researcher_tools.append(SerperDevTool())
    if target_url:
        researcher_tools.append(ScrapeWebsiteTool(website_url=target_url))

    vision_instr = "Check 'List PDF Files' & run 'PDF Image Extractor' for images." if use_vision else "Do NOT extract images."
    web_instr = "If internal data is insufficient, use 'Search the internet' (Serper)." if use_web else ""
    url_instr = f"Analyze the specific website content at: {target_url}" if target_url else ""
    file_instr = f"Focus your research on the file '{specific_file}'." if specific_file else "Search across all available data."

    researcher = Agent(
        role='Senior Enterprise Researcher',
        goal=f'Gather data from internal docs, files, and external web sources. {file_instr}',
        verbose=True, memory=True,
        backstory=(f"You are a thorough researcher. 1. Search the vector database. 2. {vision_instr} 3. {web_instr} 4. {url_instr}"),
        tools=researcher_tools, llm=llm_instance
    )
    analyst = Agent(
        role='Senior Data Analyst',
        goal='Analyze trends from text, code, and vision.',
        verbose=True, memory=True,
        backstory=("You analyze data trends. If you see tabular data, use 'Code Interpreter'. If image paths are provided, you MUST use 'Vision Analyst'."),
        tools=[code_interpreter, vision_tool], llm=llm_instance
    )
    writer = Agent(
        role='Lead Technical Writer',
        goal='Write a final report.',
        verbose=True, memory=True,
        backstory="You write professional reports citing sources.",
        llm=llm_instance
    )

    context_str = f"\nContext: {chat_history_context}" if chat_history_context else ""
    task_research = Task(
        description=(f"Research query: '{user_question}'.{context_str}\nTarget PDF: {specific_file if specific_file else 'None'}\nTarget URL: {target_url if target_url else 'None'}\nOUTPUT: Summary of found text, image paths, and web findings."),
        expected_output='Comprehensive research summary.',
        agent=researcher
    )
    task_analysis = Task(
        description="Analyze findings. Run Vision on images. Run Code on tables.",
        expected_output='Technical analysis.',
        agent=analyst, context=[task_research] 
    )
    task_writing = Task(
        description=(f"Write a final answer to: '{user_question}'. Synthesize all findings into a clear report."),
        expected_output='Final professional report.',
        agent=writer, context=[task_analysis] 
    )
    crew = Crew(agents=[researcher, analyst, writer], tasks=[task_research, task_analysis, task_writing], process=Process.sequential)
    return crew.kickoff()

# --- 6. LANDING PAGE ---

def landing_page():
    st.markdown(LANDING_CSS, unsafe_allow_html=True)
    
    # --- IF AUTH MODE (Login/Signup Page) ---
    if st.session_state.auth_mode:
        # Padded container to avoid top cutoff
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Header for Auth Page: Logo (Home Link) and Back Button
        c1, c2, c3 = st.columns([1, 6, 1])
        
        with c1:
             if st.button("⬅️ Back", use_container_width=True):
                st.session_state.auth_mode = False
                st.rerun()

        with c3:
             if st.button("🏠 Home", use_container_width=True, type="secondary"):
                st.session_state.auth_mode = False
                st.rerun()

        st.divider()
        
        # Center the Login Form
        col_spacer1, col_form, col_spacer2 = st.columns([1, 2, 1])
        with col_form:
            st.markdown("<h2 style='text-align: center; color: white; margin-bottom: 30px;'>Access Portal</h2>", unsafe_allow_html=True)
            tab1, tab2, tab3 = st.tabs(["👤 Login", "📝 Register", "🛡️ Admin"])
            
            with tab1:
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.button("Sign In", key="btn_signin", use_container_width=True, type="primary"):
                    result = db.login_user(email, password)
                    if result:
                        full_name, is_admin_flag = result
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.user_name = full_name
                        st.session_state.is_admin = bool(is_admin_flag)
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

            with tab2:
                new_name = st.text_input("Full Name")
                new_email = st.text_input("New Email")
                new_pass = st.text_input("New Password", type="password")
                if st.button("Create Account", use_container_width=True, type="primary"):
                    if db.register_user(new_email, new_pass, new_name):
                        st.success("Account created! Please Login.")
                    else:
                        st.error("Email exists.")
            
            with tab3:
                st.info("System Admin Access Only")
                adm_email = st.text_input("Admin Email", key="adm_email")
                adm_pass = st.text_input("Admin Password", type="password", key="adm_pass")
                if st.button("Access Panel", use_container_width=True):
                    result = db.login_user(adm_email, adm_pass)
                    if result and result[1] == 1:
                        st.session_state["admin_mode"] = True
                        st.session_state.logged_in = True
                        st.session_state.user_name = result[0]
                        st.session_state.user_email = adm_email
                        st.session_state.is_admin = True
                        st.rerun()
                    else:
                        st.error("Access Denied")

    # --- IF LANDING PAGE (Hero) ---
    else:
        # Navbar with Links inside a container
        st.markdown("""
        <div class="nav-container">
            <div class="nav-logo">🤖 Autonomous Enterprise Agent</div>
            <div class="nav-links">
                <a href="#features" class="nav-link">Features</a>
                <a href="#pricing" class="nav-link">Pricing</a>
                <a href="#faq" class="nav-link">FAQ</a>
                <a href="#note-on-local-llms" class="nav-link">Note on Local LLMs</a>
                <a href="#contact" class="nav-link">Contact</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hero Content
        st.markdown(HERO_HTML, unsafe_allow_html=True)
        
        # BIG "Try Now" Button (Centered)
        c_cta1, c_cta2, c_cta3 = st.columns([1, 1, 1])
        with c_cta2:
            st.markdown("<br>", unsafe_allow_html=True) 
            if st.button("🚀 Login / Sign Up Now", type="primary", use_container_width=True):
                st.session_state.auth_mode = True
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

        # Features & Rest of Page
        st.markdown(FEATURES_HTML, unsafe_allow_html=True)
        
        # --- NEW SECTION: LOCAL LLM NOTICE ---
        st.divider()
        st.markdown("""
        <div id="note-on-local-llms" style="text-align: center; max-width: 800px; margin: 0 auto; padding: 20px;">
            <h3 style="color: #cbd5e1;">⚠️ Note on Local Models</h3>
            <p style="color: #94a3b8; font-size: 1.1rem;">
                While this Enterprise Agent supports Local LLMs (like Phi-3 & Llama 3.1), 
                this cloud deployment does not have GPU acceleration enabled due to high server costs.
                To use Local Models effectively, please clone this repository and run it on your own machine.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display the image if it exists, with smaller size
        if os.path.exists("screenshots/local_llm.png"):
            st.image("screenshots/local_llm.png", caption="Local Model Architecture (Running Locally)", use_container_width=True)

# --- 7. MAIN EXECUTION FLOW ---
if not st.session_state.logged_in:
    landing_page()
    st.stop()

# --- 8. LOGGED IN UI ---

# --- ADMIN DASHBOARD ---
if st.session_state.is_admin and st.session_state.admin_mode:
    st.markdown(LANDING_CSS, unsafe_allow_html=True)
    
    # Top Header
    c_ad1, c_ad2 = st.columns([8, 2])
    with c_ad1:
        st.markdown(f"<h1 style='color:white;'>🛡️ Admin Command Center</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8; margin-top:-15px;'>Welcome, Commander {st.session_state.user_name}</p>", unsafe_allow_html=True)
    with c_ad2:
        if st.button("🚪 Exit Panel", use_container_width=True):
            st.session_state.admin_mode = False
            st.rerun()
            
    st.divider()
    
    # Stats Row
    users = db.get_all_users()
    total_users = len(users)
    total_admins = len([u for u in users if u[2] == 1])
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1: st.markdown("""<div class="admin-card"><div class="admin-stat">"""+str(total_users)+"""</div><div class="admin-label">Total Users</div></div>""", unsafe_allow_html=True)
    with col_stat2: st.markdown("""<div class="admin-card"><div class="admin-stat">"""+str(total_admins)+"""</div><div class="admin-label">Admins</div></div>""", unsafe_allow_html=True)
    with col_stat3: st.markdown("""<div class="admin-card"><div class="admin-stat">Active</div><div class="admin-label">System Status</div></div>""", unsafe_allow_html=True)

    # User Management Section
    st.markdown("""<div class="admin-card">""", unsafe_allow_html=True)
    st.markdown("""<div class="admin-header">👥 User Database</div>""", unsafe_allow_html=True)
    
    df = pd.DataFrame(users, columns=["Email", "Name", "Is Admin"])
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    c_del1, c_del2 = st.columns([3, 1])
    with c_del1: del_user = st.selectbox("Select User to Remove", [u[0] for u in users])
    with c_del2:
        st.markdown("<br>", unsafe_allow_html=True) # align button
        if st.button("🗑️ Delete User", type="primary", use_container_width=True):
            if del_user == st.session_state.user_email: st.error("You cannot delete yourself!")
            else:
                if db.delete_user(del_user):
                    st.success(f"User {del_user} eliminated.")
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True) # Close card

    # NEW: Create Admin Section
    st.markdown("""<div class="admin-card" style="border-color: #a855f7;">""", unsafe_allow_html=True)
    st.markdown("""<div class="admin-header" style="color: #e9d5ff;">⚡ Grant Admin Access</div>""", unsafe_allow_html=True)
    
    c_new1, c_new2, c_new3 = st.columns(3)
    with c_new1: new_adm_name = st.text_input("New Admin Name")
    with c_new2: new_adm_email = st.text_input("New Admin Email")
    with c_new3: new_adm_pass = st.text_input("New Admin Password", type="password")
        
    if st.button("✨ Create New Administrator", use_container_width=True):
        if new_adm_email and new_adm_pass:
            if db.register_user(new_adm_email, new_adm_pass, new_adm_name, is_admin=True):
                st.success(f"Administrator {new_adm_name} created successfully!")
                st.rerun()
            else: st.error("User already exists.")
        else: st.warning("Please fill all fields.")
            
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- USER MODE (Chat Interface) ---
with st.sidebar:
    if st.button("⬅️ Home / Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.messages = []
        st.session_state.admin_mode = False
        st.rerun()
        
    st.divider()
    st.write(f"👤 **{st.session_state.user_name}**")
    
    st.header("🔐 API Keys")
    user_api_key = st.text_input("OpenAI Key", type="password")
    serper_api_key = st.text_input("Serper Key", type="password")
    st.divider()
    
    st.header("🧠 Configuration")
    model_option = st.selectbox("Select Brain:", ["OpenAI (GPT-4o)", "Local (Phi-3)"])
    
    st.divider()
    st.header("📂 Knowledge Base")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    current_pdf_name = None
    if uploaded_file:
        for filename in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path): os.unlink(file_path)
                elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception: pass
        os.makedirs(os.path.join(DATA_DIR, "extracted_images"), exist_ok=True)
        save_path = os.path.join(DATA_DIR, uploaded_file.name)
        with open(save_path, "wb") as f: f.write(uploaded_file.getbuffer())
        current_pdf_name = uploaded_file.name
        st.success(f"Loaded: {current_pdf_name}")
    target_url = st.text_input("Target Website URL")
    st.divider()
    st.subheader("⚙️ Capabilities")
    use_vision = st.checkbox("Extract Images", value=True)
    use_web = st.checkbox("Enable Web Search", value=False)
    st.divider()
    st.header("🗂️ My Chats")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    user_sessions = db.get_user_sessions(st.session_state.user_email)
    for s_id, s_title in reversed(user_sessions):
        if st.button(f"💬 {s_title}", key=s_id, use_container_width=True):
            st.session_state.current_session_id = s_id
            st.session_state.messages = db.get_session_history(s_id)
            st.rerun()

st.title("🤖 Autonomous Enterprise Agent")
st.caption(f"Session: {st.session_state.current_session_id} | Brain: {model_option}")

if current_pdf_name:
    st.info(f"📄 **Active Document:** {current_pdf_name}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask your research team..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    db.save_message(st.session_state.user_email, st.session_state.current_session_id, "user", prompt)
    if len(st.session_state.messages) == 1:
        title = prompt[:30] + "..."
        db.save_session_title(st.session_state.user_email, st.session_state.current_session_id, title)

    llm = get_llm(model_option, user_api_key)
    if llm is None:
        st.error("⛔ OpenAI Key missing.")
        st.stop()
    
    with st.chat_message("assistant"):
        with st.spinner("🚀 Thinking..."):
            try:
                recent_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-3:]])
                if not use_vision and not use_web:
                    response_obj = run_simple_chat(prompt, recent_history, llm)
                    final_text = str(response_obj) + "\n\n---\n*💡 **Tip:** Select capabilities (Vision/Web) in the sidebar to switch to Enterprise Agent power mode.*"
                else:
                    if use_web and not serper_api_key: st.warning("⚠️ Web Search enabled but Serper Key missing.")
                    response_obj = run_crew_logic(prompt, recent_history, llm, current_pdf_name, use_vision, use_web, target_url, serper_api_key)
                    final_text = str(response_obj)
                st.markdown(final_text)
                st.session_state.messages.append({"role": "assistant", "content": final_text})
                db.save_message(st.session_state.user_email, st.session_state.current_session_id, "assistant", final_text)
                
                pdf_file = generate_pdf_report(final_text)
                with open(pdf_file, "rb") as f:
                    st.download_button("📥 Download Report", f, file_name="report.pdf")
            except Exception as e:
                st.error(f"Error: {e}")