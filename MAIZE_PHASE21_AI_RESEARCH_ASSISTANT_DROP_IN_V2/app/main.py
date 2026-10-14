from __future__ import annotations
from fastapi import FastAPI
from .config import ASSISTANT_PORT, PROJECT_ROOT
from .assistant import ResearchAssistant
from .indexer import ProjectIndexer, MANIFEST_JSON
from .schemas import ChatRequest, SearchRequest, PredictionRequest
from .data_tools import project_file_search
from .model_tools import available_models, local_predict

assistant=ResearchAssistant()
app=FastAPI(title="Maize AI Research Assistant",version="0.1.0",description="Grounded AI assistant over the complete maize project folder.",docs_url="/docs",redoc_url="/redoc",openapi_url="/openapi.json")

@app.get("/health")
def health(): return {"status":"ok","project_root":str(PROJECT_ROOT)}

@app.get("/api/v1/assistant/status")
def status():
    manifest={}
    if MANIFEST_JSON.exists():
        import json; manifest=json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    return {"project_root":str(PROJECT_ROOT),"indexed_chunks":len(assistant.retriever.chunks),"llm_configured":assistant.provider is not None,"index_manifest":manifest}

@app.post("/api/v1/assistant/chat")
def chat(req:ChatRequest): return assistant.chat(req.question)

@app.post("/api/v1/assistant/search")
def search(req:SearchRequest): return {"items":assistant.retriever.search(req.query,req.top_k)}

@app.post("/api/v1/assistant/refresh-index")
def refresh_index():
    result=ProjectIndexer().build(); assistant.refresh(); return result

@app.get("/api/v1/assistant/sources")
def sources(query: str): return {"items":project_file_search(query)}

@app.get("/api/v1/assistant/tools")
def tools():
    from .assistant import TOOLS
    return {"tools":TOOLS}

@app.get("/api/v1/assistant/models")
def models(): return {"items":available_models(include_metadata=False)}

@app.post("/api/v1/assistant/predict")
def assistant_predict(req:PredictionRequest):
    domains={"yield":["yield"],"tlb":["tlb_regression","tlb_classifier"],"sdm":["sdm_regression","sdm_classifier"],"all":None}[req.domain]
    return local_predict(req.features,domains)

if __name__=="__main__":
    import uvicorn
    uvicorn.run("app.main:app",host="127.0.0.1",port=ASSISTANT_PORT,reload=False)
