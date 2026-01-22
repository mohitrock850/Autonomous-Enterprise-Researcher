import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

# Configuration
PDF_PATH = "knowledge.pdf"
DB_PATH = "faiss_index"

def ingest_documents():
    # 1. Load the Data
    # In a real enterprise app, you would have logic here to handle 
    # different file types (confluence, slack dumps, etc.)
    if not os.path.exists(PDF_PATH):
        print(f"❌ Error: Could not find {PDF_PATH}. Please add a PDF to the folder.")
        return

    print(f"📄 Loading {PDF_PATH}...")
    loader = PyPDFLoader(PDF_PATH)
    raw_documents = loader.load()
    print(f"   - Loaded {len(raw_documents)} pages.")

    # 2. Chunking Strategy (Crucial for RAG)
    # We split text into chunks of 1000 characters.
    # 'chunk_overlap=200' ensures that sentences aren't cut in half 
    # at the edge of a chunk.
    print("✂️  Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    chunks = text_splitter.split_documents(raw_documents)
    print(f"   - Created {len(chunks)} text chunks.")

    # 3. Create Embeddings & Store in Vector DB
    # We use 'nomic-embed-text' to turn text into numbers.
    print("🧠 Creating Vector Embeddings (this may take a moment)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # FAISS (Facebook AI Similarity Search) creates the efficient index
    vector_db = FAISS.from_documents(documents=chunks, embedding=embeddings)

    # 4. Save to Disk
    # We save this so we don't have to re-process the PDF every time.
    vector_db.save_local(DB_PATH)
    print(f"✅ Success! Knowledge base saved to folder: '{DB_PATH}'")

if __name__ == "__main__":
    ingest_documents()