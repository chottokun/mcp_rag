# プロジェクト概要
このリポジトリは、FastAPI + fastapi_mcp + ChromaDB + cl-nagoya/ruri-v3-30m を用いた RAG（Retrieval-Augmented Generation）サービスの動作可能なMCPサーバの実装です。
ドキュメントの取り込みから、埋め込み生成、類似検索、MCP経由でのクエリ応答までを含みます。

# 目的
- RAGサービスの基本構成を示すサンプルを提供する
- fastapi_mcp を活用して MCP ツールとして公開する
- ChromaDB による埋め込み管理と検索を実装する
- cl-nagoya/ruri-v3-30m による日本語埋め込みを活用する

# 制約
- FastAPI_mpc を使用すること
- ChromaDB はローカル永続化モード（PersistentClient）で使用すること
- ChromaDB はそれぞれの情報に応じた複数のDBを持ち、一つ以上のDBを指定してRAGを実施する
- SentenceTransformer による埋め込み生成は CPU モードで動作させる（初期設定）。GPUでの動作もできる、実装とすること。
- 外部ライブラリは pip でインストール可能なものに限る
- 認証は HTTPBearer による簡易トークン認証を使用する。認証の利用する・しないは選択できる。
- 仮想環境ツールとしてUVの利用を許可する。
- TDD（テスト駆動開発）を行うこと。
  
# 優先タスク
1. `rag_service.py` の `add_document` メソッドに、ファイル種別（例：PDF, Markdown）に応じた前処理を追加してください。
2. `/query/` エンドポイントに、検索結果のスコア（類似度）を含めて返すようにしてください。
3. `main.py` に `/healthcheck` エンドポイントを追加し、サービスの稼働状況を確認できるようにしてください。
4. `agent.md` の内容をもとに、README.md にプロジェクト概要と実行手順を整理してください。

