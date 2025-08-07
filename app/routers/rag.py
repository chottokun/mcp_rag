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

class DeleteRequest(BaseModel):
    filename: str
    collection_name: str = "documents"

@router.post(
    "/delete_document/",
    operation_id="delete_document",
    summary="ドキュメントを削除",
    description="ファイル名を指定して、埋め込み済みのドキュメントを削除します。"
)
async def delete_document_endpoint(request: DeleteRequest):
    """
    Deletes a document from the specified collection based on the filename.
    """
    try:
        rag.delete_document(filename=request.filename, collection_name=request.collection_name)
        return {"message": f"'{request.filename}' was successfully deleted from collection '{request.collection_name}'."}
    except Exception as e:
        # A more specific exception might be better, but for now, this is a safeguard.
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting the document: {e}")
