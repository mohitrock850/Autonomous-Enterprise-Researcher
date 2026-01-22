import os
import sys
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from tools import search_tool
from analysis_tools import code_interpreter, file_lister, pdf_extractor, vision_tool

# --- 1. Load Secrets ---
load_dotenv()

def get_llm():
    """
    Select the AI Brain.
    """
    print("\n🧠 Select your AI Brain:")
    print("1. Local (Phi-3 via Ollama) - [Free, Privacy, Offline]")
    print("2. OpenAI (GPT-4o)        - [Best for Vision & Code Analysis]")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print(">> Using LOCAL (Phi-3)...")
        # Note: Local models struggle with complex Vision/Code tasks compared to GPT-4o
        return LLM(
            model="ollama/phi3",
            base_url="http://localhost:11434"
        )
    
    elif choice == "2":
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ Error: OPENAI_API_KEY not found in .env file.")
            print("Please add your key to the .env file.")
            sys.exit(1)
        print(">> Using OPENAI (GPT-4o)...")
        return LLM(
            model="gpt-4o",
            temperature=0
        )
    
    else:
        print("Invalid choice. Defaulting to Local (Phi-3).")
        return LLM(model="ollama/phi3", base_url="http://localhost:11434")

# Initialize the selected LLM
selected_llm = get_llm()

# --- 2. Define the Agents ---

# Researcher: Now capable of finding files, reading text, and extracting images
researcher = Agent(
    role='Senior Enterprise Researcher',
    goal='Gather all text AND visual data from the knowledge base.',
    verbose=True,
    memory=True,
    backstory=(
        "You are thorough. You don't just read text; you look for evidence in images."
        "1. First, search the vector database for text."
        "2. Second, CHECK THE FILE SYSTEM using 'List PDF Files' to see available documents."
        "3. If a PDF exists, run 'PDF Image Extractor' to get the charts/diagrams."
    ),
    tools=[search_tool, file_lister, pdf_extractor], 
    llm=selected_llm
)

# Analyst: Analyzes the extracted images and executes code for data
analyst = Agent(
    role='Senior Data & Vision Analyst',
    goal='Analyze the extracted text and the extracted images to form a complete picture.',
    verbose=True,
    memory=True,
    backstory=(
        "You receive raw text and lists of image paths."
        "1. If you see tabular data in the text, use 'Code Interpreter' to calculate trends/averages."
        "2. You must use the 'Vision Analyst' tool on EVERY image path provided by the Researcher."
        "3. You verify if the text matches the visual data."
    ),
    tools=[code_interpreter, vision_tool], 
    llm=selected_llm
)

# Writer: Synthesizes everything into a final report
writer = Agent(
    role='Lead Technical Writer',
    goal='Write a report that combines text facts with visual analysis.',
    verbose=True,
    memory=True,
    backstory="You write comprehensive reports. You explicitly mention: 'According to the chart in the document...'",
    llm=selected_llm
)

# --- 3. Define the Workflow ---

def run_crew(user_question):
    print(f"\n🚀 Starting Agentic Team for: '{user_question}'\n")

    # Task 1: Force the Researcher to look for text AND images
    task_research = Task(
        description=(
            f"Research the query: '{user_question}'.\n"
            "1. Use 'Enterprise Search Tool' to get text context.\n"
            "2. Use 'List PDF Files' to see what files are in the data folder.\n"
            "3. Use 'PDF Image Extractor' on the found PDF(s) to extract all images.\n"
            "OUTPUT: A summary of the text found AND a list of image file paths extracted."
        ),
        expected_output='Text summary + List of image paths (e.g., extracted_images/file_p1_i1.png).',
        agent=researcher
    )

    # Task 2: Analyze the images and data found
    task_analysis = Task(
        description=(
            "Review the Researcher's output.\n"
            "1. If image paths are listed, use the 'Vision Analyst' tool on EACH image to understand what it shows (charts, diagrams, etc.).\n"
            "2. If tabular data is found, use 'Code Interpreter' to check the numbers.\n"
            "3. Combine the visual insights with the text facts."
        ),
        expected_output='A technical analysis merging text data and visual descriptions.',
        agent=analyst,
        context=[task_research] 
    )

    # Task 3: Write Report 
    task_writing = Task(
        description=(
            f"Write a final answer to: '{user_question}'. "
            "Enhance the response by inserting a diagram tag in the format '' "
            "where X is a contextually relevant and domain-specific query to fetch a diagram "
            "(e.g., ''). "
            "Ensure you implicitly describe the insights from any charts or diagrams analyzed by the Analyst."
        ),
        expected_output='A professional report citing both text and visual evidence, including  tags where relevant.',
        agent=writer,
        context=[task_analysis] 
    )

    enterprise_crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[task_research, task_analysis, task_writing],
        process=Process.sequential 
    )

    result = enterprise_crew.kickoff()
    return result

# --- 4. Execution ---
if __name__ == "__main__":
    user_input = input("Enter your question: ")
    final_answer = run_crew(user_input)
    
    print("\n\n########################")
    print("## 🤖 FINAL CREW OUTPUT ##")
    print("########################\n")
    print(final_answer)