__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import os
import threading
import signal

os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
_original_signal = signal.signal

def threaded_signal_handler(sig, action):
    try:
        if threading.current_thread() is threading.main_thread():
            return _original_signal(sig, action)
    except ValueError:
        # Ignore the error if we are not in the main thread
        pass

signal.signal = threaded_signal_handler

import streamlit as st
import os
import json
import uuid
import shutil
from dotenv import load_dotenv
from fpdf import FPDF
from crewai import Agent, Task, Crew, Process, LLM
from tools import search_tool
# Import your custom tools
from analysis_tools import code_interpreter, file_lister, pdf_extractor, vision_tool
# Import CrewAI tools
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

# --- 1. Setup & Config ---
st.set_page_config(page_title="Autonomous Enterprise Agent", page_icon="🤖", layout="wide")
load_dotenv()

HISTORY_FILE = "chat_history.json"
DATA_DIR = "data"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as f:
        json.dump({}, f)

# --- 2. Helper Functions ---

def get_llm(model_choice, user_api_key):
    """Initialize the LLM based on UI selection"""
    if model_choice == "OpenAI (GPT-4o)":
        final_key = user_api_key if user_api_key else os.getenv("OPENAI_API_KEY")
        if not final_key:
            return None
        os.environ["OPENAI_API_KEY"] = final_key
        return LLM(model="gpt-4o", temperature=0)
    else:
        return LLM(model="ollama/phi3", base_url="http://localhost:11434")

def generate_pdf_report(content, filename="report.pdf"):
    """Generates a PDF file from the agent's text output"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    
    # Handle basic unicode by replacing common non-latin chars
    safe_content = content.encode('latin-1', 'replace').decode('latin-1')
    
    for line in safe_content.split('\n'):
        pdf.multi_cell(0, 10, line)
    
    pdf.output(filename)
    return filename

def save_chat(session_id, title, messages):
    try:
        with open(HISTORY_FILE, "r") as f: data = json.load(f)
    except: data = {}
    data[session_id] = {"title": title, "messages": messages}
    with open(HISTORY_FILE, "w") as f: json.dump(data, f, indent=4)

def load_history():
    try:
        with open(HISTORY_FILE, "r") as f: return json.load(f)
    except: return {}

# --- 3. The CrewAI Core Logic ---

def run_crew_logic(user_question, chat_history_context, llm_instance, specific_file, use_vision, use_web, target_url, serper_key):
    """
    Dynamically assembles the Agent Team based on enabled features.
    """
    
    # --- Dynamic Tool Loading ---
    researcher_tools = [search_tool, file_lister, pdf_extractor]
    
    # Add Web Search if enabled
    if use_web and serper_key:
        os.environ["SERPER_API_KEY"] = serper_key
        researcher_tools.append(SerperDevTool())
    
    # Add Website Scraper if URL provided
    if target_url:
        researcher_tools.append(ScrapeWebsiteTool(website_url=target_url))

    # --- Instructions ---
    vision_instr = "Check 'List PDF Files' & run 'PDF Image Extractor' for images." if use_vision else "Do NOT extract images."
    web_instr = "If internal data is insufficient, use 'Search the internet' (Serper)." if use_web else ""
    url_instr = f"Analyze the specific website content at: {target_url}" if target_url else ""
    file_instr = f"Focus your research on the file '{specific_file}'." if specific_file else "Search across all available data."

    # 1. Researcher
    researcher = Agent(
        role='Senior Enterprise Researcher',
        goal=f'Gather data from internal docs, files, and external web sources if enabled. {file_instr}',
        verbose=True,
        memory=True,
        backstory=(
            "You are a thorough researcher. "
            "1. Search the vector database. "
            f"2. {vision_instr} "
            f"3. {web_instr} "
            f"4. {url_instr}"
        ),
        tools=researcher_tools, 
        llm=llm_instance
    )

    # 2. Analyst
    analyst = Agent(
        role='Senior Data Analyst',
        goal='Analyze trends from text, code, and vision.',
        verbose=True,
        memory=True,
        backstory=(
            "You analyze data trends. "
            "If you see tabular data, use 'Code Interpreter'. "
            "If image paths are provided, you MUST use 'Vision Analyst'."
        ),
        tools=[code_interpreter, vision_tool], 
        llm=llm_instance
    )

    # 3. Writer
    writer = Agent(
        role='Lead Technical Writer',
        goal='Write a final report.',
        verbose=True,
        memory=True,
        backstory="You write professional reports citing sources (internal PDF or external Web).",
        llm=llm_instance
    )

    # --- Tasks ---
    context_str = f"\nContext: {chat_history_context}" if chat_history_context else ""
    
    task_research = Task(
        description=(
            f"Research query: '{user_question}'.{context_str}\n"
            f"Target PDF: {specific_file if specific_file else 'None'}\n"
            f"Target URL: {target_url if target_url else 'None'}\n"
            "OUTPUT: Summary of found text, image paths, and web findings."
        ),
        expected_output='Comprehensive research summary.',
        agent=researcher
    )

    task_analysis = Task(
        description="Analyze findings. Run Vision on images. Run Code on tables.",
        expected_output='Technical analysis.',
        agent=analyst,
        context=[task_research] 
    )

 # Task 3: Write Report (Corrected)
    task_writing = Task(
        description=(
            f"Write a final answer to: '{user_question}'. "
            "Enhance the response by inserting a diagram tag in the format '' "
            "where X is a contextually relevant and domain-specific query to fetch a diagram "
            "(e.g., ''). "
            "Synthesize all findings into a clear report."
        ),
        expected_output='Final professional report.',
        agent=writer,
        context=[task_analysis] 
    )

    crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[task_research, task_analysis, task_writing],
        process=Process.sequential 
    )

    return crew.kickoff()

# --- 4. Streamlit UI Layout ---

with st.sidebar:
    st.header("🔐 API Keys")
    user_api_key = st.text_input("OpenAI Key", type="password", help="Required for GPT-4o Agent")
    serper_api_key = st.text_input("Serper Key (Google Search)", type="password", help="Required for Web Search")
    
    st.divider()
    
    st.header("🧠 Configuration")
    model_option = st.selectbox("Select Brain:", ["OpenAI (GPT-4o)", "Local (Phi-3)"])
    
    st.divider()
    
    # --- KNOWLEDGE BASE SECTION  ---
    st.header("📂 Knowledge Base")
    uploaded_file = st.file_uploader("Upload PDF (Strict Mode: Clears Old Data)", type=["pdf"])
    
    current_pdf_name = None
    if uploaded_file:
        # 1. Clear existing data to ensure "Strict Isolation"
        for filename in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                st.error(f"Error clearing data: {e}")
        
        # 2. Re-create images folder
        os.makedirs(os.path.join(DATA_DIR, "extracted_images"), exist_ok=True)
        
        # 3. Save the new file
        save_path = os.path.join(DATA_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        current_pdf_name = uploaded_file.name
        st.success(f"Loaded: {current_pdf_name}")
    
    target_url = st.text_input("Target Website URL", placeholder="https://example.com")
    
    st.divider()
    st.subheader("⚙️ Capabilities")
    use_vision = st.checkbox("Extract Images", value=True)
    use_web = st.checkbox("Enable Web Search", value=False, help="Requires Serper Key")

    st.divider()
    
    # --- HISTORY SECTION ---
    st.header("🗂️ Chat History")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    history = load_history()
    for session_id, data in reversed(list(history.items())):
        if st.button(f"💬 {data['title']}", key=session_id, use_container_width=True):
            st.session_state.current_session_id = session_id
            st.session_state.messages = data['messages']
            st.rerun()
            
    if st.button("🗑️ Clear All History", use_container_width=True, type="primary"):
        with open(HISTORY_FILE, "w") as f: json.dump({}, f)
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

# --- 5. Main Content Area ---

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.messages = []

st.title("🤖 Autonomous Enterprise Agent")
st.caption(f"Session: {st.session_state.current_session_id} | Brain: {model_option}")

# Display active PDF context if any
if current_pdf_name:
    st.info(f"📄 **Active Document:** {current_pdf_name}")

# Display Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input Logic
if prompt := st.chat_input("Ask your research team..."):
    # Show User Message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Initialize LLM
    llm = get_llm(model_option, user_api_key)
    
    # Check Blocks
    if llm is None:
        st.error("⛔ OpenAI Key missing. Please enter it in the sidebar.")
        st.stop()
    
    if use_web and not serper_api_key:
        st.warning("⚠️ Web Search enabled but Serper Key missing. Agent may fail if it tries to search.")

    # Run Agent
    with st.chat_message("assistant"):
        with st.spinner("🚀 Analyzing..."):
            try:
                # Get Context from last 3 messages
                recent_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-3:]])
                
                # EXECUTE CREW
                response = run_crew_logic(prompt, recent_history, llm, current_pdf_name, use_vision, use_web, target_url, serper_api_key)
                
                final_text = str(response)
                st.markdown(final_text)
                st.session_state.messages.append({"role": "assistant", "content": final_text})
                
                # Generate Title if new chat
                if len(st.session_state.messages) <= 2:
                    title = prompt[:30] + "..."
                else:
                    title = history.get(st.session_state.current_session_id, {}).get("title", "New Chat")
                
                save_chat(st.session_state.current_session_id, title, st.session_state.messages)
                
                # PDF Download Button
                pdf_file = generate_pdf_report(final_text)
                with open(pdf_file, "rb") as f:
                    st.download_button("📥 Download Report (PDF)", f, file_name="agent_report.pdf")
                
            except Exception as e:
                st.error(f"Error: {e}") 
