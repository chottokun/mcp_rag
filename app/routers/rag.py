from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
# No longer need Depends or HTTPBearer here
from ..rag_service import RAGService

router = APIRouter()

rag = RAGService()

# The auth_scheme is removed.

class QueryResultItem(BaseModel):
    text: str
    metadata: dict
    distance: float

class QueryResponse(BaseModel):
    query: str
    results: list[QueryResultItem]

@router.post(
    "/ingest/",
    operation_id="ingest_document",
    summary="インジェスト文書",
    description="テキストファイルを受け取り埋め込み登録します。"
)
async def ingest_document(
    file: UploadFile = File(...),
    collection_name: str = "documents",
    # The token dependency is removed from the signature
):
    content = await file.read()
    rag.add_document(content, filename=file.filename, collection_name=collection_name)
    return {"message": f"'{file.filename}' を登録しました。"}

@router.get(
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

@router.get("/healthcheck", summary="Health Check")
async def healthcheck():
    """
    Returns a 200 OK status if the server is running.
    """
    return {"status": "ok"}
