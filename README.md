# MCP RAG Server

このリポジトリは、FastAPI + `fastapi-mcp` + ChromaDB を用いた RAG (Retrieval-Augmented Generation) サービスの動作可能なMCPサーバの実装です。
ドキュメントの取り込み、埋め込み生成 (`cl-nagoya/ruri-v3-30m`)、類似検索、そしてMCP経由でのクエリ応答まで、一連の機能を提供します。

## 特徴

- **アプリケーションファクトリ**: `app/factory.py` の `create_app` により、テスト容易性と設定の柔軟性が向上しました。
- **複数コレクション対応**: ChromaDB内で名前付きのコレクションを複数作成し、ドキュメントを分離・管理できます。
- **ファイルインジェスト**: テキスト、Markdown、PDFなど、さまざまな形式のファイルをアップロードして処理します。
- **類似検索**: コサイン類似度を用いて関連性の高いテキストチャンクを検索し、そのスコアと共に返却します。
- **MCP対応API**: `fastapi-mcp` を通じて、AIエージェントが利用可能なエンドポイントを公開します。
- **設定可能な認証**: 環境変数 `API_KEY` を設定するだけで、簡単にAPI認証を有効化できます。

## セットアップ

1.  **リポジトリのクローン:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **仮想環境の作成と依存関係のインストール:**
    このプロジェクトでは `uv` を推奨しますが、`venv` と `pip` も利用可能です。
    ```bash
    # uv を使用する場合
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt

    # venv/pip を使用する場合
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

## 実行方法

1.  **(任意) 認証の設定:**
    APIを保護する場合、環境変数 `API_KEY` を設定します。`.env` ファイルを作成するのが便利です。
    ```
    # .env
    API_KEY="your-secret-api-key"
    ```
    `API_KEY` が設定されていない場合、認証は無効になります。

2.  **FastAPIサーバの起動:**
    プロジェクトのルートディレクトリから以下のコマンドを実行します。
    ```bash
    uvicorn app.main:app --reload
    ```
    サーバは `http://127.0.0.1:8000` で起動します。

3.  **APIドキュメントへのアクセス:**
    - **Swagger UI**: `http://127.0.0.1:8000/docs`
    - **MCPエンドポイント**: `http://127.0.0.1:8000/mcp`

## APIエンドポイント

### 1. ドキュメントのインジェスト

- **URL**: `/rag/ingest/`
- **メソッド**: `POST`
- **説明**: 指定されたコレクションにファイルをアップロードしてインジェストします。
- **Query Parameters**:
    - `collection_name` (string, optional): ドキュメントを追加するコレクション名。デフォルトは `"documents"`。
- **ヘッダー**:
    - `Authorization`: `Bearer your-secret-api-key` (認証が有効な場合)
- **ボディ**: `multipart/form-data` 形式で、`file` フィールドにドキュメントを含めます。
- **`curl` での例**:
    ```bash
    curl -X POST "http://127.0.0.1:8000/rag/ingest/?collection_name=my_collection" \
         -H "Authorization: Bearer your-secret-api-key" \
         -F "file=@/path/to/your/document.pdf"
    ```

### 2. 類似ドキュメントのクエリ

- **URL**: `/rag/query/`
- **メソッド**: `GET`
- **説明**: クエリテキストに類似するドキュメントをコレクション内から検索します。
- **Query Parameters**:
    - `query` (string, required): 検索するテキスト。
    - `collection_name` (string, optional): 検索対象のコレクション名。デフォルトは `"documents"`。
- **`curl` での例**:
    ```bash
    curl -X GET "http://127.0.0.1:8000/rag/query/?query=what%20is%20fastapi&collection_name=my_collection"
    ```

### 3. ヘルスチェック

- **URL**: `/rag/healthcheck`
- **メソッド**: `GET`
- **説明**: サービスの稼働状況を確認します。
- **`curl` での例**:
    ```bash
    curl -X GET http://127.0.0.1:8000/rag/healthcheck
    ```

### 4. ドキュメントの削除

- **URL**: `/rag/delete_document/`
- **メソッド**: `POST`
- **説明**: 指定されたコレクションからファイル名に基づいてドキュメントを削除します。
- **ボディ**: `application/json` 形式で、`filename` と `collection_name` を含めます。
- **`curl` での例**:
    ```bash
    curl -X POST "http://127.0.0.1:8000/rag/delete_document/" \
         -H "Authorization: Bearer your-secret-api-key" \
         -H "Content-Type: application/json" \
         -d '{"filename": "document_to_delete.txt", "collection_name": "my_collection"}'
    ```
