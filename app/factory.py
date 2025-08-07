import os
import importlib
import logging
from typing import Optional, List

from fastapi import FastAPI, Depends
from fastapi_mcp import FastApiMCP
from .routers import rag as rag_router
from .auth_helpers import get_api_key

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_app(
    no_auth: bool = False, additional_modules: Optional[List[str]] = None
) -> FastAPI:
    """
    FastAPIアプリケーションを作成し、設定します。
    """
    app = FastAPI(
        title="MCP RAG Server",
        version="0.2.0",
        description=(
            "fastapi-mcpを使用してRAG機能を提供するサーバー"
        ),
    )

    # 認証依存関係の設定
    auth_dependencies = []
    if not no_auth and os.environ.get("API_KEY"):
        auth_dependencies.append(Depends(get_api_key))

    # RAGツールのルーターを登録
    app.include_router(
        router=rag_router.router,
        prefix="/rag",
        tags=["RAG"],
        dependencies=auth_dependencies, # Pass dependencies here
    )

    # 追加のツールモジュールを登録
    if additional_modules:
        for module_name in additional_modules:
            try:
                module = importlib.import_module(module_name)
                if (
                    hasattr(module, "router")
                    and hasattr(module, "prefix")
                    and hasattr(module, "tags")
                ):
                    app.include_router(
                        module.router,
                        prefix=module.prefix,
                        tags=module.tags,
                        dependencies=auth_dependencies,
                    )
                    logger.info(f"モジュール '{module_name}' からルーターを登録しました")
                else:
                    logger.warning(
                        f"モジュール '{module_name}' に登録可能なルーターが見つかりません"
                    )
            except ImportError as e:
                logger.error(f"モジュール '{module_name}' の読み込みに失敗しました: {e}")

    # fastapi-mcpのセットアップ
    mcp = FastApiMCP(
        app,
        name="MCP RAG Server",
        description="RAG機能を提供するサーバー",
        describe_all_responses=True,
        describe_full_response_schema=True,
    )

    # MCPサーバーのマウント
    mcp.mount()

    return app
