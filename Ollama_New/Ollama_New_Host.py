
import os
import json
from pathlib import Path
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
import uvicorn
import traceback
import subprocess

# ================= CONFIG =================
EMBED_MODEL = "nomic-embed-text"
DEFAULT_LLM_MODEL = "gemma3:1b"
DATA_DIR = os.path.expanduser("./rag-data")
STORAGE_DIR = "./storage"
CHAT_HISTORY_FILE = os.path.expanduser("./rag-chat-history.json")
HOST = "0.0.0.0"
PORT = 8080

SIMILARITY_TOP_K = 6
RESPONSE_MODE = "tree_summarize"
SIMILARITY_THRESHOLD = 0.60
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
# =========================================

app = FastAPI(title="Local RAG Chat")

current_llm_model = DEFAULT_LLM_MODEL
index = None
chat_history = []

def get_ollama_models():
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        models = [line.split()[0].strip() for line in result.stdout.strip().splitlines()[1:] if line.strip()]
        return models if models else [DEFAULT_LLM_MODEL]
    except Exception:
        return [DEFAULT_LLM_MODEL]

def load_or_create_index():
    global index
    if Path(STORAGE_DIR).exists() and any(Path(STORAGE_DIR).iterdir()):
        try:
            storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
            index = load_index_from_storage(storage_context)
            print("✅ Loaded existing index")
        except Exception as e:
            print(f"Warning: Could not load index: {e}")
    return index

def load_chat_history():
    global chat_history
    if Path(CHAT_HISTORY_FILE).exists():
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                chat_history = json.load(f)
        except Exception:
            chat_history = []
    else:
        chat_history = []

def save_chat_history():
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(chat_history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Failed to save chat history: {e}")

# Initialize
embed_model = OllamaEmbedding(model_name=EMBED_MODEL, request_timeout=300.0)
llm = Ollama(model=current_llm_model, request_timeout=300.0, temperature=0.1)
Settings.embed_model = embed_model
Settings.llm = llm
Settings.node_parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)
load_or_create_index()
load_chat_history()

@app.get("/", response_class=HTMLResponse)
async def home():
    models = get_ollama_models()
    model_options = "".join(
        f'<option value="{m}" {"selected" if m == current_llm_model else ""}>{m}</option>'
        for m in models
    )

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>📚 Local RAG Chat</title>
    <style>
        body {{ font-family: system-ui, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }}
        .dark-mode {{ background: #121212; color: #eee; }}
        #chat {{ height: 620px; overflow-y: auto; border-radius: 16px; padding: 25px; background: white; display: flex; flex-direction: column; gap: 18px; }}
        .message {{ padding: 14px 18px; border-radius: 18px; max-width: 85%; }}
        .user {{ background: #007bff; color: white; align-self: flex-end; }}
        .assistant {{ background: #e9ecef; align-self: flex-start; }}
        .sources {{ font-size: 0.85em; margin-top: 10px; opacity: 0.85; border-top: 1px solid #ddd; padding-top: 8px; }}
        .input-area {{ display: flex; gap: 12px; margin-top: 20px; }}
        #question {{ flex: 1; padding: 16px; font-size: 17px; border: 2px solid #ccc; border-radius: 12px; }}
        button {{ padding: 12px 20px; border: none; border-radius: 12px; cursor: pointer; }}
        .controls {{ display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-top: 15px; }}
        select {{ padding: 12px; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>📚 Local RAG Chat</h1>
    <p class="subtitle">Documents in <code>./rag-data</code></p>
    
    <div id="chat"></div>
    
    <div class="input-area">
        <input type="text" id="question" placeholder="Ask a question about your documents..." autocomplete="off">
        <button onclick="sendQuestion()">Send</button>
    </div>
    
    <div class="controls">
        <button onclick="clearChat()">🗑️ Clear Chat</button>
        <!--
        <button onclick="reindex()">🔄 Re-index Documents</button>
        <label style="cursor:pointer; background:#28a745; color:white; padding:12px 20px; border-radius:12px;">
            📤 Upload Document
            <input type="file" id="fileInput" style="display:none;" onchange="uploadFile(event)">
        </label>
        <select id="modelSelect" onchange="changeModel(this.value)">
            {model_options}
        </select>
        -->
    </div>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('question');

        function appendMessage(role, content, sources = []) {{
            const div = document.createElement('div');
            div.className = `message ${{role}}`;
            let html = `<strong>${{role === 'user' ? 'You' : 'Assistant'}}:</strong><br>${{content.replace(/\\n/g, '<br>')}}`;
            if (sources && sources.length > 0) {{
                html += `<div class="sources"><strong>Sources:</strong><br>` + sources.map(s => `• ${{s}}`).join('<br>') + `</div>`;
            }}
            div.innerHTML = html;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}

        function loadHistory() {{
            fetch('/history').then(r => r.json()).then(data => {{
                chat.innerHTML = '';
                data.forEach(msg => appendMessage(msg.role, msg.content, msg.sources || []));
            }}).catch(() => {{}});
        }}

        async function sendQuestion() {{
            const q = input.value.trim();
            if (!q) return;
            appendMessage('user', q);
            input.value = '';
            const loading = document.createElement('div');
            loading.textContent = 'Thinking...';
            loading.style.alignSelf = 'flex-start';
            chat.appendChild(loading);
            chat.scrollTop = chat.scrollHeight;

            try {{
                const res = await fetch('/query', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                    body: new URLSearchParams({{question: q}})
                }});
                loading.remove();
                const data = await res.json();
                appendMessage('assistant', data.response || 'No response received.', data.sources || []);
            }} catch (err) {{
                loading.remove();
                appendMessage('assistant', 'Error: ' + err.message, []);
            }}
        }}

        async function reindex() {{
            if (!confirm('Re-index all documents now?')) return;
            try {{
                const res = await fetch('/reindex', {{method: 'POST'}});
                const data = await res.json();
                alert(data.message);
            }} catch (e) {{
                alert('Re-index failed: ' + (e.message || 'Check server terminal'));
            }}
        }}

        async function uploadFile(e) {{
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            try {{
                const res = await fetch('/upload', {{method: 'POST', body: formData}});
                const data = await res.json();
                alert(data.message);
                if (data.success) reindex();
            }} catch (err) {{
                alert('Upload failed');
            }}
        }}

        function clearChat() {{ if (confirm('Clear chat?')) {{ fetch('/clear_history', {{method: 'POST'}}); chat.innerHTML = ''; }} }}
        function changeModel(newModel) {{ alert('Model switching coming soon'); }}

        input.addEventListener('keypress', e => {{ if (e.key === 'Enter') sendQuestion(); }});
        window.onload = () => {{ input.focus(); loadHistory(); }};
        chat.addEventListener('click', () => input.focus());
    </script>
</body>
</html>
"""
    return HTMLResponse(html_content)

# === Endpoints ===
@app.post("/reindex")
async def reindex():
    global index
    try:
        reader = SimpleDirectoryReader(DATA_DIR, recursive=True)
        documents = reader.load_data()
        if not documents:
            return {"message": "No documents found in ./rag-data/. Add files first."}

        index = VectorStoreIndex.from_documents(
            documents,
            transformations=[SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)]
        )
        index.storage_context.persist(persist_dir=STORAGE_DIR)
        return {"message": f"✅ Successfully indexed {len(documents)} documents!"}
    except Exception as e:
        print(traceback.format_exc())
        return {"message": f"Re-index failed: {str(e)}"}

@app.post("/query")
async def query(question: str = Form(...)):
    global index, chat_history
    if not index:
        return {"response": "No documents indexed yet. Please re-index first.", "sources": []}
    try:
        postprocessors = [SimilarityPostprocessor(similarity_cutoff=SIMILARITY_THRESHOLD)]
        query_engine = index.as_query_engine(
            similarity_top_k=SIMILARITY_TOP_K,
            response_mode=RESPONSE_MODE,
            node_postprocessors=postprocessors
        )
        response = query_engine.query(question)
        sources = []
        for node in getattr(response, 'source_nodes', []):
            file_name = node.node.metadata.get('file_name', 'Unknown')
            excerpt = (node.node.text[:220] + "...") if len(node.node.text) > 220 else node.node.text
            sources.append(f"{file_name}: {excerpt}")
        answer = str(response)
        chat_history.append({"role": "user", "content": question, "sources": []})
        chat_history.append({"role": "assistant", "content": answer, "sources": sources})
        save_chat_history()
        return {"response": answer, "sources": sources}
    except Exception as e:
        print(traceback.format_exc())
        return {"response": f"Error: {str(e)}", "sources": []}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        file_path = Path(DATA_DIR) / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"message": f"✅ Uploaded {file.filename}", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    return chat_history

@app.post("/clear_history")
async def clear_history():
    global chat_history
    chat_history = []
    save_chat_history()
    return {"message": "Chat history cleared"}

if __name__ == "__main__":
    print(f"🚀 RAG Chat starting at http://localhost:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
