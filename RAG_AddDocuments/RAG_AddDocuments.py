import os, time
from pathlib import Path
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

# ================= CONFIG =================
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "gemma3:1b"     # Change to your model
DATA_DIR = "./rag-data"            # Put documents to be added here
STORAGE_DIR = "./storage"          # Persistent vector store on disk
# =========================================

# Set up Ollama embedding and LLM
embed_model = OllamaEmbedding(model_name=EMBED_MODEL, request_timeout=600.0)
llm = Ollama(model=LLM_MODEL, request_timeout=600.0, temperature=0.1)

Settings.embed_model = embed_model
Settings.llm = llm

# Create storage directory if it doesn't exist
os.makedirs(STORAGE_DIR, exist_ok=True)

def add_documents():
    """Add (or re-index) all documents in DATA_DIR"""
    print("Loading documents...")
    reader = SimpleDirectoryReader(DATA_DIR)
    documents = reader.load_data()
    
    if not documents:
        print("No documents found!")
        return None
    
    # Build or update index
    print("Indexing...")
    index = VectorStoreIndex.from_documents(documents)
    
    # Persist to disk for future use
    print("Persisting...")
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    print(f"✅ Indexed {len(documents)} documents and saved to {STORAGE_DIR}")
    return index

def load_index():
    """Load existing index from disk"""
    storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
    return load_index_from_storage(storage_context)

def query(question: str, top_k: int = 5):
    """Ask a question over your documents"""
    startThinking = time.perf_counter()
    index = load_index()
    query_engine = index.as_query_engine(similarity_top_k=top_k, response_mode="compact")
    response = query_engine.query(question)
    print("\n" + "="*50)
    print(f"Question: {question}")
    print(f"Answer: {response}")
    doneThinking = time.perf_counter()
    print(f"(Responded in {int(doneThinking - startThinking)} seconds)")
    print("="*50)
    return response

if __name__ == "__main__":
    # First run: add documents
    if not Path(STORAGE_DIR).exists() or not any(Path(STORAGE_DIR).iterdir()):
        add_documents()
    else:
        print("Loading existing index...")
    
    # Interactive querying
    while True:
        q = input("\nAsk a question (or type 'exit' to quit): ")
        if q.lower() in ['exit', 'quit']:
            break
        query(q)

print("Finished")
