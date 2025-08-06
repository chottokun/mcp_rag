# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from fastapi_mcp import FastApiMCP
from fastapi.security import HTTPBearer
from rag_service import RAGService
import uvicorn

app = FastAPI(title="RAG MCP Service")

rag = RAGService()

# セキュリティトークン認証（簡易例）
auth_scheme = HTTPBearer()

mcp = FastApiMCP(
    app,
    name="RAG Service MCP",
    description="MCP interface for RAG document ingestion and retrieval",
    auth_config=None,
    describe_all_responses=True,
    describe_full_response_schema=True,
)
mcp.mount()

class QueryResultItem(BaseModel):
    text: str
    metadata: dict
    distance: float

class QueryResponse(BaseModel):
    query: str
    results: list[QueryResultItem]

@app.post(
    "/ingest/",
    operation_id="ingest_document",
    summary="インジェスト文書",
    description="テキストファイルを受け取り埋め込み登録します。"
)
async def ingest_document(
    file: UploadFile = File(...),
    collection_name: str = "documents",
    token=Depends(auth_scheme),
):
    content = await file.read()
    # The RAGService now handles bytes and different file types
    rag.add_document(content, filename=file.filename, collection_name=collection_name)
    return {"message": f"'{file.filename}' を登録しました。"}

@app.get(
    "/query/",
    operation_id="query_rag",
    summary="RAG クエリ",
    description="クエリを受け取り類似文書を返します。",
    response_model=QueryResponse
)
async def query_endpoint(query: str, collection_name: str = "documents"):
    if not query:
        raise HTTPException(status_code=400, detail="query パラメータが必要です")
    result = rag.query_rag(query_text=query, n_results=3, collection_name=collection_name)
    return result

@app.get("/healthcheck", summary="Health Check")
async def healthcheck():
    """
    Returns a 200 OK status if the server is running.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
