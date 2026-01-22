import os
# Force PyTorch/CPU settings to match tools.py
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"

from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

# Import our custom tools
from tools import retrieve_documents, validate_relevance

# --- 1. Define the "State" ---
# The State is the "Short-term Memory" of the agent.
# It keeps track of the question, the documents found, and the loop count.
class AgentState(TypedDict):
    question: str
    documents: List[str]
    loop_step: int

# --- 2. Define the Nodes (The Actions) ---

llm = ChatOllama(model="phi3", temperature=0)

def retrieve_node(state: AgentState):
    """
    Action: Search the vector database.
    """
    question = state["question"]
    print(f"\n--- 🔄 Step {state['loop_step']}: Retrieving Documents ---")
    
    # Use our tool from Step 3
    docs = retrieve_documents(question)
    
    # Extract just the text content to keep state clean
    doc_texts = [d.page_content for d in docs]
    
    return {"documents": doc_texts, "loop_step": state["loop_step"] + 1}

def grade_documents_node(state: AgentState):
    """
    Action: Check if the retrieved documents are relevant.
    This node doesn't change data, it just passes it to the 'Conditional Edge' logic.
    """
    print("--- ⚖️  Grading Documents ---")
    question = state["question"]
    documents = state["documents"]
    
    # We only check the first (best) document for speed in this demo
    if not documents:
        return {"documents": []} # No docs found
        
    validation = validate_relevance(question, documents[0])
    
    # We verify the result. If "yes", we keep the docs. If "no", we clear them.
    if validation['relevance'] == 'yes':
        print("   ✅ Validator: Documents are RELEVANT.")
        return {"documents": documents} # Keep them
    else:
        print("   ❌ Validator: Documents are IRRELEVANT.")
        return {"documents": []} # Clear them to trigger a re-try

def generate_node(state: AgentState):
    """
    Action: Generate the final answer using the relevant documents.
    """
    print("--- ✍️  Generating Final Answer ---")
    question = state["question"]
    documents = state["documents"]
    
    # Combine all docs into one context block
    context = "\n\n".join(documents)
    
    prompt = f"""
    You are an Enterprise Assistant. Use the following context to answer the user's question.
    If the answer is not in the context, say "I don't know".
    
    Context:
    {context}
    
    Question: 
    {question}
    
    Answer:
    """
    
    response = llm.invoke(prompt)
    print(f"\n🤖 FINAL ANSWER:\n{response.content}")
    return {}

def rewrite_query_node(state: AgentState):
    """
    Action: The documents were bad, so we rewrite the question to try again.
    """
    print("--- 🧠 Reasoning: Rewriting Query ---")
    question = state["question"]
    
    msg = [
        HumanMessage(content=f"""
        Look at the input and try to reason about the underlying semantic intent / meaning.
        Input: {question}
        
        Return ONLY the improved query string, nothing else.
        """)
    ]
    
    response = llm.invoke(msg)
    new_query = response.content
    print(f"   Original: '{question}' -> New: '{new_query}'")
    
    return {"question": new_query}


# --- 3. Define the Edges (The Logic) ---

def decide_next_step(state: AgentState):
    """
    The Traffic Cop: Decides where to go after Grading.
    """
    documents = state["documents"]
    loop_step = state["loop_step"]
    
    # Safety Valve: Don't loop forever. Stop after 3 tries.
    if loop_step > 3:
        print("--- 🛑 Max Retries Hit. Giving up. ---")
        return "generate" # Just give whatever we have
        
    if len(documents) > 0:
        # We have good docs (because 'grade_node' didn't clear them)
        return "generate"
    else:
        # We cleared the docs because they were bad. Retry!
        return "rewrite"


# --- 4. Build the Graph ---

workflow = StateGraph(AgentState)

# Add the nodes
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("grade", grade_documents_node)
workflow.add_node("rewrite", rewrite_query_node)
workflow.add_node("generate", generate_node)

# Set the Entry Point
workflow.set_entry_point("retrieve")

# Add the edges (Connections)
workflow.add_edge("retrieve", "grade")

# Conditional Edge: After grading, decide what to do
workflow.add_conditional_edges(
    "grade",
    decide_next_step,
    {
        "generate": "generate",
        "rewrite": "rewrite"
    }
)

# Connect the loop back
workflow.add_edge("rewrite", "retrieve")
workflow.add_edge("generate", END)

# Compile the machine
app = workflow.compile()

# --- 5. Run It ---
if __name__ == "__main__":
    print("\n🚀 Starting Autonomous Agent...")
    
    # Test Question (Try a tricky one!)
    user_input = input("Enter your question: ")
    
    inputs = {
        "question": user_input,
        "documents": [],
        "loop_step": 0
    }
    
    # Run the graph
    result = app.invoke(inputs)