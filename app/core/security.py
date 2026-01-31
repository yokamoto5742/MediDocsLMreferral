"""APIキー認証モジュール"""
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

# ヘッダー名の定義
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key_header: str | None = Depends(API_KEY_HEADER),
    settings: Settings = Depends(get_settings),
) -> str | None:
    """
    APIキーを検証する依存関数

    - MEDIDOCS_API_KEY環境変数が未設定の場合: 認証をスキップ（開発モード）
    - MEDIDOCS_API_KEY環境変数が設定済みの場合: ヘッダーのキーと照合
    """
    # 開発モード: MEDIDOCS_API_KEY未設定時は認証スキップ
    if settings.api_key is None:
        return None

    # 本番モード: APIキー検証
    if api_key_header is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="APIキーが必要です",
            headers={"WWW-Authenticate": "API-Key"},
        )

    if api_key_header != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無効なAPIキーです",
        )

    return api_key_header
