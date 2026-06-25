
import os, time
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama


# ================= CONFIG =================
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "gemma3:1b"            # Change to your model
DATA_DIR = "./rag-data"            # Put documents to be added here
STORAGE_DIR = "./storage"          # Persistent vector store on disk
# =========================================


# Set up Ollama embedding and LLM
embed_model = OllamaEmbedding(model_name=EMBED_MODEL, request_timeout=600.0)
llm = Ollama(model=LLM_MODEL, request_timeout=600.0, temperature=0.1)
Settings.embed_model = embed_model
Settings.llm = llm


# Load existing index from disk
def load_index():
    storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
    return load_index_from_storage(storage_context)


# Ask a question over your documents
def query(question: str, top_k: int = 5):
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
    while True: # interactive querying
        q = input("\nAsk a question (or type 'exit' to quit): ")
        if q.lower() in ['exit', 'quit']: break
        print("Thinking ...")
        query(q)

print("Finished")
