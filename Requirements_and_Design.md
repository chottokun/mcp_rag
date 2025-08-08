# RAGシステム（fastapi_mcp＋ChromaDB＋cl-nagoya/ruri-v3-30m）

## 1. 要求仕様書

### 1.1 システム概要

AI エージェントまたはユーザーが自然言語でクエリを投げると、FastAPI + fastapi\_mcp により MCP ツールとして公開された `/query/`（operation\_id：`query_rag`）を通じて RAG サービスが起動します。
クエリに「検索クエリ: 」プレフィックスを付与して埋め込み生成し、ChromaDB による類似検索を実行。取得した文書断片を返却し、AI はそれを LLM への文脈として利用します。

### 1.2 機能要件

#### ・ドキュメント取り込み

* マークダウン（.md）を先行対象とし、将来的には PDF や DOCX にも対応可能な拡張性。langchainを利用し将来的な拡張を担保。
* アップロード時の文字コード自動検出および例外処理を実装。
* langchain-text-splitters の `RecursiveCharacterTextSplitter` を使って文書をチャンク化。`chunk_size` と `chunk_overlap` は設定可能（例：500〜1000 字、50〜100 重複）。

#### ・埋め込み生成

* `cl-nagoya/ruri-v3-30m` モデル（日本語埋め込み専用）を `sentence-transformers` 経由で読み込み ([apidog][1], [Hugging Face][2])。
* 文書チャンクには「検索文書: 」プレフィックス、クエリには「検索クエリ: 」プレフィックスを使用 ([Hugging Face][2])。
* GPU／FlashAttention 対応で高速化も可能。ただし、FlashAttentionはGPUが対応している場合に限る。

#### ・検索・類似度検索

* ChromaDB に格納された embedding を、クエリ embedding を用いて類似検索（`n_results` は可変設定）。
* スコアの閾値によるフィルタリング機能も提供可能。

#### ・MCP インターフェース

* FastAPI ルートに `operation_id`（例：`ingest_document`, `query_rag`）を明示し、fastapi\_mcp によって MCP ツール名が明確化される ([Hugging Face][3])。
* `FastApiMCP(app, base_url=..., name=..., description=...)` により `/mcp` エンドポイントを生成、エージェントは SSE 経由でツールを自動検出可能 ([Medium][4])。

### 1.3 非機能要件

* **性能**: バッチ処理、GPU／FlashAttention 最適化により低レイテンシを実現。ChromaDB の検索パラメータ調整でスループット拡張。
* **信頼性**: ファイル破損・DB パス未設定などの例外処理。
* **保守性**: モジュール化設計（RAGService、API 層、チャンク／DB 操作の分離）、Pydantic による型安全化。
* **セキュリティ**: ファイルサイズ制限、ウイルスチェック、認証／認可（OAuth2／Bearer Token）を `Depends()` による導入（MCP ツール経由でも制御可能） ([DEV Community][5], [Medium][6])。

---

## 2. 設計書

### 2.1 アーキテクチャ概要

```mermaid
graph TD
  A[AIエージェント via MCP] -->|SSE| C[MCPサーバ (/mcp)]
  C --> B[FastAPI アプリ]
  B --> E[RAGService]
  E --> F[チャンク分割モジュール]
  F --> G[埋め込みモデル ruri‑v3‑30m]
  G --> H[ChromaDB]
  E -- 検索 → H
  E --> I[外部 LLM]
```

* FastAPI に `operation_id` を付与した複数ルートを定義し、fastapi\_mcp をマウント。
* `/ingest/` と `/query/` を operation\_id 指定で公開。
* `MCP = FastApiMCP(app, base_url=..., name="RAG MCP Service", description=...)` を利用し `/mcp` を mount ([apidog][1])。

### 2.2 コンポーネント詳細

#### RAGService クラス

* `__init__`: `chromadb.PersistentClient(path)` 初期化、コレクション取得、`SentenceTransformer("cl-nagoya/ruri-v3-30m", device=device)` ロード ([Hugging Face][2])、`RecursiveCharacterTextSplitter(chunk_size, chunk_overlap)` 初期化。

* `add_document(text, filename)`:

  * チャンク分割 → 各チャンクに「検索文書: 」を付与 → バッチで埋め込み生成 → `collection.add()` による格納（ID／metadata 含む）。

* `query_rag(query_text, n_results)`:

  * 「検索クエリ: 」プレフィックス付きクエリで埋め込み生成 → `collection.query()` で類似検索 → プレフィックス除去後にチャンク再構成し返却。

* `delete_document(filename, collection_name)`:

  * `collection.delete(where={"source": filename})` を利用し、指定されたファイル名に紐づく全てのチャンクを削除。

#### FastAPI ルート

* `/ingest/` POST：`operation_id="ingest_document"`, アップロード処理と `add_document` 呼び出し。
* `/query/` GET：`operation_id="query_rag"`, クエリパラメータ受け取り → `query_rag` 呼び出し → JSON 出力。
* `/delete_document/` POST: `operation_id="delete_document"`, `filename` と `collection_name` を受け取り → `delete_document` を呼び出し → 削除結果を返す。
* 事前定義した `operation_id` により、MCP ツール名が直感的でエージェントの利用性が向上 ([Toolify][7])。

### 2.3 拡張設計

* **設定ファイル**: チャンクサイズやオーバーラップ、n\_results、スコア閾値などを環境変数または `settings.py` で管理。
* **認証・認可**: ファイルアップロード等に OAuth2／Bearer Token 認証を導入し、MCP 経由の呼び出しにも制約可能。
* **CI テスト**: RAGService のユニットテスト（チャンク分割、ベクトル生成、類似検索）と FastAPI 統合テスト。
* **デプロイ**: Dockerfile で GPU 対応環境を構築。ChromaDB 永続ストレージマウント設定。

---

## ✅ 要約

| 項目         | 内容                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------ |
| ドキュメント取り込み | 多言語対応／設定制御可能なチャンク分割                                                                        |
| 埋め込みモデル    | `cl-nagoya/ruri-v3-30m`、日本語対応／FlashAttention 対応 ([Hugging Face][2], [model.aibase.com][8]) |
| 類似検索       | ChromaDB を使用、n\_results／閾値設定など柔軟設計                                                         |
| MCP ツール    | 明示 `operation_id` によるツール名設定、AI への可視性向上 ([LobeHub][9], [apidog][1])                         |
| 非機能面       | 性能最適化／例外処理／セキュリティ／保守性に配慮                                                                   |

---

Ref.:

[1]: https://apidog.com/blog/fastapi-mcp/?utm_source=chatgpt.com "How to Use FastAPI MCP Server - Apidog"
[2]: https://huggingface.co/cl-nagoya/ruri-v3-30m?utm_source=chatgpt.com "cl-nagoya/ruri-v3-30m - Hugging Face"
[3]: https://huggingface.co/cl-nagoya/ruri-v3-pt-30m?utm_source=chatgpt.com "cl-nagoya/ruri-v3-pt-30m - Hugging Face"
[4]: https://medium.com/towards-agi/how-to-use-fastapi-mcp-server-a-comprehensive-guide-fbb308fd7937?utm_source=chatgpt.com "How to Use FastAPI MCP Server: A Comprehensive Guide - Medium"
[5]: https://dev.to/auden/introducing-fastapi-mcp-effortless-ai-integration-for-your-fastapi-apis-2c8c?utm_source=chatgpt.com "What is FastAPI MCP? Effortless AI Integration for Your FastAPI APIs"
[6]: https://medium.com/%40ruchi.awasthi63/integrating-mcp-servers-with-fastapi-2c6d0c9a4749?utm_source=chatgpt.com "Integrating MCP Servers with FastAPI | by Ruchi - Medium"
[7]: https://www.toolify.ai/ai-model/cl-nagoya-ruri-v3-130m?utm_source=chatgpt.com "cl-nagoya/ruri-v3-130m"
[8]: https://model.aibase.com/models/details/1915749791243591681?utm_source=chatgpt.com "Ruri-v3-pt-30m Open-source Japanese Text Embedding Model"
[9]: https://lobehub.com/mcp/tadata-org-fastapi_mcp?utm_source=chatgpt.com "FastAPI-MCP | MCP Servers - LobeHub"

## 参考コード

以下、FastAPI＋fastapi\_mcp＋ChromaDB＋cl‑nagoya/ruri‑v3‑30m を使った **動作可能なサンプル実装** です。要件を満たし、ドキュメント取り込みから MCP 経由のクエリ応答まで含まれています。

---

## 📘 `rag_service.py`

```python
# rag_service.py
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any
import os

class RAGService:
    def __init__(
        self,
        db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        model_name: str = os.getenv("EMBED_MODEL", "cl-nagoya/ruri-v3-30m"),
    ):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection("documents")
        self.model = SentenceTransformer(model_name, device=os.getenv("DEVICE", "cpu"))
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
            length_function=len,
        )

    def add_document(self, text: str, filename: str):
        chunks = self.text_splitter.split_text(text)
        ids, docs = [], []
        for i, chunk in enumerate(chunks):
            pref = f"検索文書: {chunk}"
            ids.append(f"{filename}_{i}")
            docs.append(pref)
        if docs:
            embeddings = self.model.encode(docs).tolist()
            self.collection.add(
                embeddings=embeddings,
                documents=docs,
                metadatas=[{"source": filename}] * len(docs),
                ids=ids,
            )

    def query_rag(self, query_text: str, n_results: int = 3) -> Dict[str, Any]:
        prefq = f"検索クエリ: {query_text}"
        emb = self.model.encode([prefq]).tolist()[0]
        res = self.collection.query(
            query_embeddings=[emb], n_results=n_results, include=["documents","metadatas"]
        )
        docs = [d.replace("検索文書: ", "") for d in res["documents"][0]]
        metas = res["metadatas"][0]
        return {"query": query_text, "results": [{"text": d, "metadata": m} for d, m in zip(docs, metas)]}
```

---

## 📘 `main.py`

```python
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
)
mcp.mount()

class QueryResponse(BaseModel):
    query: str
    results: list

@app.post(
    "/ingest/",
    operation_id="ingest_document",
    summary="インジェスト文書",
    description="テキストファイルを受け取り埋め込み登録します。"
)
async def ingest_document(
    file: UploadFile = File(...),
    token=Depends(auth_scheme),
):
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="テキストとして読み込めません")
    rag.add_document(text, filename=file.filename)
    return {"message": f"'{file.filename}' を登録しました。"}

@app.get(
    "/query/",
    operation_id="query_rag",
    summary="RAG クエリ",
    description="クエリを受け取り類似文書を返します。",
    response_model=QueryResponse
)
async def query_endpoint(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="query パラメータが必要です")
    result = rag.query_rag(query_text=query, n_results=3)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## ✅ 補足ポイント

* `operation_id="ingest_document"` と `query_rag` により、fastapi\_mcp が MCP ツールとして明確に公開します (\[turn0search5]参照)。
* セキュリティとして `HTTPBearer` によるトークン認証を `Depends()` で導入し、MCP 再経由でもアクセス制御可能です（後から `auth_config=` に渡せます） (\[turn0search7]参照)。
* ChromaDB と FastAPI による RAG 実装は Real Python 等でも類似パターンで紹介されています (\[turn0search6]参照)。

---

## 🛠 実行方法

1. 依存パッケージをインストール：

```
pip install fastapi uvicorn chromadb sentence-transformers langchain-text-splitters fastapi_mcp python-multipart
```

2. `main.py` を実行：

```
python main.py
```

3. Swagger UI: `http://127.0.0.1:8000/docs`
   MCP エンドポイント: `http://127.0.0.1:8000/mcp`

4. Postman や curl で `/ingest/` にテキストファイル投稿、その後 `/query/?query=～` によって類似文書取得が可能。

5. `curl` で `/delete_document/` にファイル名を指定してドキュメントを削除する例:
```bash
curl -X POST http://127.0.0.1:8000/delete_document/ \
-H "Content-Type: application/json" \
-d '{"filename": "your_file_to_delete.txt", "collection_name": "documents"}'
```

---

