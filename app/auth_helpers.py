import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    """
    APIキーを検証します。
    """
    # Check for the key inside the function
    api_key_env = os.environ.get("API_KEY")

    if not api_key_env:
        # API_KEYが設定されていない場合は認証をスキップ
        return None

    # "Bearer " プレフィックスを削除
    if api_key and api_key.startswith("Bearer "):
        key = api_key.split(" ")[1]
    else:
        key = api_key

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )

    if key == api_key_env:
        return key
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
