from fastapi import FastAPI

from vector_store_pg import VectorStore
from llm_connector import LLMConnector
from config import EMBED_MODEL_PATH, DB_PARAMS


app = FastAPI()
db = VectorStore(EMBED_MODEL_PATH, DB_PARAMS)
llm = LLMConnector()

@app.get("/")
def root():
    return {"message": "API работает"}

@app.get("/generate")
def generate(query: str):
    chunks = db.hybrid_search(query)
    context = "\n\n".join([chunk["page_content"] for chunk in chunks])
    answer = "".join(llm.generate_response(query, context))
    return {"answer": answer}

@app.get("/health")
def check_health():
    return {"status": "ok"}
