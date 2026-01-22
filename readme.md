# 🤖 Autonomous Enterprise Research Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red?logo=streamlit&logoColor=white)
![CrewAI](https://img.shields.io/badge/Orchestration-CrewAI-orange)
![LangChain](https://img.shields.io/badge/Framework-LangChain-1C3C3C?logo=langchain&logoColor=white)

![OpenAI](https://img.shields.io/badge/Cloud_LLM-GPT--4o-412991?logo=openai&logoColor=white)
![Ollama](https://img.shields.io/badge/Local_LLM-Ollama-black?logo=ollama&logoColor=white)
![Microsoft Phi-3](https://img.shields.io/badge/Model-Phi--3-00A4EF?logo=microsoft&logoColor=white)

![PyMuPDF](https://img.shields.io/badge/PDF-PyMuPDF-firebrick)
![Google Serper](https://img.shields.io/badge/Web_Search-Serper_Dev-4285F4?logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

> **A production-grade, multi-modal autonomous agent capable of synthesizing proprietary internal data (PDFs) with real-time web intelligence to generate professional business reports.**

## 📸 Project Showcase

<table width="100%">
  <tr>
    <td align="center" width="50%">
      <h3>Multi-Modal Analysis (Vision RAG)</h3>
      <img src="screenshots/pdf_result_Sharp.gif" width="98%" />
      <br/>
      <em>Extracts and analyzes charts from PDFs</em>
    </td>
    <td align="center" width="50%">
      <h3>Real-Time Web Search</h3>
      <img src="screenshots/live_api_result.png" width="98%" />
      <br/>
      <em>Fetches live financial / market data</em>
    </td>
  </tr>
</table>

<br/>

<table width="100%">
  <tr>
    <td align="center" width="50%">
      <h3>Local LLM Support (Privacy)</h3>
      <img src="screenshots/local_llm.png" width="98%" />
      <br/>
      <em>Runs offline on local hardware via Ollama</em>
    </td>
    <td align="center" width="50%">
      <h3>Website Scraping</h3>
      <img src="screenshots/website_result_Sharp.gif" width="98%" />
      <br/>
      <em>Reads and summarizes specific URLs</em>
    </td>
  </tr>
</table>


## 🚀 Key Features

* **🧠 Hybrid Brain Architecture:** Seamlessly switch between **Cloud (GPT-4o)** for high-fidelity reasoning and **Local (Phi-3 via Ollama)** for privacy and cost-savings.
* **👁️ Multi-Modal RAG (Vision + Text):** Unlike standard RAG, this agent detects images in PDFs, extracts them, and uses Vision Language Models (VLM) to interpret charts and diagrams.
* **🌍 Active Web Connection:** Equipped with **Serper (Google Search)** and **Website Scraping** tools to verify internal data against live internet sources.
* **🛡️ Strict Data Isolation:** Implements a "Strict Mode" that auto-wipes previous session data upon new file uploads to prevent context bleeding and ensure security.
* **📂 Code Interpreter:** Embedded Python REPL allows the agent to write and execute code for precise data calculation and tabulation.

---

## 🏗️ System Architecture

The system uses **CrewAI** to orchestrate a hierarchical team of agents. The flow is dynamic based on user configuration (e.g., if "Vision" is disabled, the Vision Tool is removed from the Researcher's toolkit to save resources).

```mermaid
graph TD
    User[👤 User] -->|Uploads PDF / Prompts| UI[💻 Streamlit UI]
    UI -->|Configures| Brain{🧠 Brain Selector}
    
    Brain -->|Cloud| GPT[OpenAI GPT-4o]
    Brain -->|Local| Phi[Ollama Phi-3]
    
    UI -->|Triggers| Crew[🤖 CrewAI Orchestrator]
    
    subgraph "Agentic Team"
        Res[🔎 Researcher Agent]
        Ana[📊 Analyst Agent]
        Wri[✍️ Writer Agent]
    end
    
    Crew --> Res
    Res -->|Passes Data| Ana
    Ana -->|Passes Insights| Wri
    
    subgraph "Tool Belt"
        T1[📄 File Lister]
        T2[🔍 Vector Search]
        T3[🖼️ Vision Tool]
        T4[🐍 Code Interpreter]
        T5[🌐 Serper Google Search]
        T6[🕸️ Website Scraper]
    end
    
    Res -.-> T1 & T2 & T5 & T6
    Ana -.-> T3 & T4
    
    Wri -->|Final Report| Report[📄 PDF Report]
```
# 🛠️ Tech Stack

> A detailed breakdown of the technologies, libraries, and frameworks powering the **Autonomous Enterprise Research Agent**.

---

## 🐍 Core Runtime & Language
| Technology | Badge | Description |
| :--- | :--- | :--- |
| **Python** | ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white) | The backbone of the application. Chosen for its extensive ecosystem in AI, Data Science, and PDF processing. |

---

## 🧠 Artificial Intelligence (The Brains)
| Technology | Badge | Role in Project |
| :--- | :--- | :--- |
| **CrewAI** | ![CrewAI](https://img.shields.io/badge/Orchestration-CrewAI-orange) | **Agent Orchestrator.** Manages the hierarchical team (Researcher, Analyst, Writer), delegates tasks, and handles inter-agent communication. |
| **LangChain** | ![LangChain](https://img.shields.io/badge/Framework-LangChain-green) | **Logic Layer.** Provides the underlying chain management and tool interfaces used by CrewAI agents. |
| **OpenAI GPT-4o** | ![OpenAI](https://img.shields.io/badge/Cloud_LLM-GPT--4o-black?logo=openai&logoColor=white) | **Primary Intelligence.** Handles complex reasoning, high-fidelity vision analysis, and final report generation. |
| **Ollama** | ![Ollama](https://img.shields.io/badge/Local_LLM-Ollama-white?logo=ollama&logoColor=black) | **Local Inference Engine.** Powers the "Privacy Mode" by running the **Microsoft Phi-3** model locally on your machine. |
| **Microsoft Phi-3** | ![Phi-3](https://img.shields.io/badge/Model-Phi--3_Mini-blueviolet) | **Local Model.** A lightweight (3.8B param) model chosen for high performance on consumer hardware (8GB-16GB RAM). |

---

## 💻 User Interface (The Face)
| Technology | Badge | Role in Project |
| :--- | :--- | :--- |
| **Streamlit** | ![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red?logo=streamlit&logoColor=white) | **Application UI.** Renders the chat interface, file uploader, sidebar configurations, and real-time agent status updates. |

---

## 👁️ Computer Vision & Data Processing
| Technology | Badge | Role in Project |
| :--- | :--- | :--- |
| **PyMuPDF (Fitz)** | ![PDF](https://img.shields.io/badge/PDF-PyMuPDF-darkred) | **Extraction Engine.** High-speed extraction of text, metadata, and raw image bytes from uploaded PDF documents. |
| **Pillow (PIL)** | ![Images](https://img.shields.io/badge/Imaging-Pillow-yellow) | **Image Optimization.** Resizes and compresses extracted charts (to <800px) to prevent API token overflow errors (Fixes 429 error). |
| **LiteLLM** | ![LiteLLM](https://img.shields.io/badge/Proxy-LiteLLM-lightgrey) | **Model Abstraction.** Standardizes API calls, allowing the system to switch between OpenAI and Ollama seamlessly. |

---

## 🌍 External Intelligence (The Tools)
| Technology | Badge | Role in Project |
| :--- | :--- | :--- |
| **Serper Dev** | ![Google](https://img.shields.io/badge/Search-Google_API-4285F4?logo=google&logoColor=white) | **Web Search Tool.** Allows the Researcher agent to perform live Google searches for real-time stock prices, news, and facts. |
| **ScrapeWebsiteTool**| ![Scraper](https://img.shields.io/badge/Tool-Web_Scraper-purple) | **Content Reader.** Enables the agent to visit specific URLs provided by the user and summarize their content. |

---

## 📂 Utilities & Infrastructure
* **`python-dotenv`**: Manages sensitive API keys (OpenAI, Serper) securely via `.env` files.
* **`FPDF`**: Generates the final, downloadable professional PDF report from the agent's markdown output.
* **`JSON`**: Handles the persistent storage for the "Long Term Memory" (Chat History) feature.

---

## 🧬 System Dependency Graph

```mermaid
graph LR
    User --> Streamlit
    Streamlit --> CrewAI
    
    subgraph "AI Engines"
        CrewAI --> OpenAI[GPT-4o]
        CrewAI --> Ollama[Phi-3 Local]
    end
    
    subgraph "Data Tools"
        CrewAI --> PyMuPDF[PDF Parser]
        PyMuPDF --> Pillow[Image Compressor]
        CrewAI --> Serper[Google Search]
    end
    
    CrewAI --> FPDF[Report Generator]
```
## ⚙️ Installation & Setup

### 1️⃣ Clone Repository
```bash
git clone https://github.com/yourusername/autonomous-enterprise-researcher.git
cd autonomous-enterprise-researcher
```

### 2️⃣ Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```
### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
> **⚠️ Note:** Ensure `litellm` and `crewai-tools` are installed, as they are critical for the hybrid LLM switching.

## 🤖 Local LLM Setup (Ollama)

### Why Phi-3?
Lightweight, fast, and runs smoothly on **8–16GB RAM** systems.

### Install Ollama
👉 https://ollama.com

### Pull Model
```bash
ollama pull phi3
```

### Start Server
```bash
ollama serve
```
## 🚦 Usage

### Run App
```bash
streamlit run app.py
```
### Sidebar Configuration
- 🔑 **API Keys** – OpenAI (Cloud) & Serper (Web)
- 🧠 **Brain Selection** – Local (Phi-3) or Cloud (GPT-4o)
- 📎 **Upload PDF** – Drag & drop

### Example Queries
- “Analyze the growth trend in Figure 1”
- “Search the web for NVIDIA’s latest stock price”

### Export
- 📥 **Download Report** → Clean PDF summary

```markdown
### 🧪 Testing with Sample Data
We have provided sample data to help you test the agent's capabilities immediately.

1.  **Locate the Sample PDF:**
    * Find the file `Global Electric Vehicle.pdf` in the **root directory** of this project.
    * Upload this file using the **Sidebar** in the app.
2.  **Run the Test Query:**
    * Ask the agent: *"Analyze the growth trend of EVs based on the chart in the document."*
    * The agent will use the **Vision Tool** to read the chart and generate a report.
3.  **View Sample Code:**
    * Check `report.py` to see an example of how the reporting logic is structured programmatically.
```

## 📂 Project Structure

```text
autonomous-enterprise-researcher/
├── data/                       # Directory for active PDF analysis (Auto-cleared in Strict Mode)
├── screenshots/                # Demo images and GIFs used in this README
├── Global Electric Vehicle.pdf # Sample PDF file for testing the Vision Agent
├── analysis_tools.py           # Custom logic for Vision Tool, PDF Extraction, and Code Interpreter
├── app.py                      # Main Streamlit application (Frontend & UI Logic)
├── crew_ai_agent.py            # Core Agent orchestration logic and Crew definition
├── graph.py                    # Utility for graph-based logic or visualizations
├── ingest.py                   # Data ingestion scripts for vector database handling
├── tools.py                    # Configuration for standard tools (Serper Dev, Website Scraper)
├── report.pdf                  # Sample output generated by the agent
├── requirements.txt            # Python dependencies list
├── .gitignore                  # Git ignore rules for secrets and temp files
└── README.md                   # Project documentation
```

## 🔮 Future Roadmap
- [ ] 🎙️ **Voice Interface** – Add `st.audio_input` for voice-to-text querying
- [ ] 🐳 **Docker Support** – Containerize the application for easy deployment
- [ ] 📚 **Multi-Document Compare** – Analyze multiple PDFs simultaneously

---

## 📄 License
Distributed under the **MIT License**.  
See `LICENSE` for more information.

---

### ❤️ Built with love by **Mohit**





