import os
# FORCE disable TensorFlow so it doesn't conflict with PyTorch
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"

from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from sentence_transformers import CrossEncoder
import numpy as np

# --- 1. SETUP: Load the "Brain", "Memory", and "Re-ranker" ---

print("⚙️  Loading resources (Embeddings, FAISS, Re-ranker)...")

# A. Load Embeddings (for retrieval)
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# B. Load Vector Database (The "Memory")
# This defines 'vector_db' so the functions below can use it.
DB_PATH = "faiss_index"
try:
    vector_db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
except RuntimeError:
    print(f"❌ CRITICAL ERROR: Could not load '{DB_PATH}'.") 
    print("   Did you run 'ingest.py' first to create the database?")
    exit(1)

# C. Load Validator LLM (The "Editor")
llm = ChatOllama(model="phi3", format="json", temperature=0)

# D. Load Re-ranker (The "Second Opinion")
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')


# --- 2. TOOLS: Retrieval & Validation ---

def retrieve_documents(query, k_initial=10, k_final=3):
    """
    1. Retrieval: Get top 10 docs from FAISS (Broad Search)
    2. Re-ranking: sort them by actual relevance (Precise Filter)
    """
    print(f"🕵️  Broad Search for: '{query}'...")
    
    # Step 1: Broad Retrieval
    # Uses the global 'vector_db' defined above
    initial_docs = vector_db.similarity_search(query, k=k_initial)
    
    if not initial_docs:
        return []

    print(f"   - Found {len(initial_docs)} candidates. Re-ranking now...")

    # Step 2: Prepare pairs for the Cross-Encoder
    pairs = [[query, doc.page_content] for doc in initial_docs]
    
    # Step 3: Score the pairs
    scores = reranker.predict(pairs)
    
    # Step 4: Sort by highest score
    sorted_indices = np.argsort(scores)[::-1] # Sort descending
    
    top_docs = []
    for i in range(min(k_final, len(initial_docs))):
        idx = sorted_indices[i]
        best_doc = initial_docs[idx]
        
        # Optional: Print score for debugging
        # print(f"   Rank #{i+1}: Score {scores[idx]:.2f}")
        
        top_docs.append(best_doc)
        
    return top_docs

def validate_relevance(query, context_text):
    """
    Asks the LLM: 'Does this text actually answer the user's question?'
    """
    validator_prompt = PromptTemplate(
        template="""
        You are a strict data evaluator. 
        User Query: {query}
        Retrieved Document Snippet: {context}
        
        Check if the 'Retrieved Document Snippet' contains the specific information needed to answer the 'User Query'.
        If it is relevant, output "relevance": "yes".
        If it is unrelated or vague, output "relevance": "no".
        
        Provide your response in JSON format only:
        {{ "relevance": "yes/no", "reason": "short explanation" }}
        """,
        input_variables=["query", "context"]
    )
    
    chain = validator_prompt | llm
    response = chain.invoke({"query": query, "context": context_text})
    
    import json
    try:
        data = json.loads(response.content)
        return data
    except:
        return {"relevance": "error", "reason": "LLM failed to output JSON"}

# --- 3. MAIN TEST BLOCK ---
if __name__ == "__main__":
    print("\n--- Advanced Tool Test Mode ---")
    user_q = input("Enter a question about your PDF: ")
    
    # 1. Retrieve (With Re-ranking)
    retrieved_docs = retrieve_documents(user_q)
    
    if retrieved_docs:
        top_doc = retrieved_docs[0].page_content
        print(f"\n📄 Top Re-ranked Document:\n{top_doc[:300]}...\n")
        
        # 2. Validate
        print("⚖️  Validating relevance...")
        validation_result = validate_relevance(user_q, top_doc)
        print(f"📊 Validation Result: {validation_result}")
    else:
        print("❌ No documents found.")


# --- 4. CrewAI Native Tool ---
from crewai.tools import BaseTool

class EnterpriseSearchTool(BaseTool):
    name: str = "Enterprise Search Tool"
    description: str = "Useful to search for information in the enterprise knowledge base (PDFs). Always use this tool to find facts."

    def _run(self, query: str) -> str:
        # Call your existing logic
        docs = retrieve_documents(query, k_final=3)
        if not docs:
            return "No relevant documents found."
        return "\n\n".join([d.page_content for d in docs])

# Instantiate the tool
search_tool = EnterpriseSearchTool()