"""CSRF認証モジュール"""
import hashlib
import hmac
import secrets
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

# ヘッダー名の定義
CSRF_TOKEN_HEADER = APIKeyHeader(name="X-CSRF-Token", auto_error=False)


def _get_secret_key(settings: Settings) -> bytes:
    """CSRF署名用の秘密鍵を取得"""
    if settings.csrf_secret_key:
        return settings.csrf_secret_key.encode("utf-8")
    # 未設定時はランダム生成（サーバー再起動で無効化）
    return secrets.token_bytes(32)


# サーバー起動時の秘密鍵をキャッシュ
_SECRET_KEY_CACHE: dict[str, bytes] = {}


def get_secret_key(settings: Settings) -> bytes:
    """秘密鍵をキャッシュして返す（設定値ごとにキャッシュ）"""
    cache_key = settings.csrf_secret_key or "_random_"
    if cache_key not in _SECRET_KEY_CACHE:
        _SECRET_KEY_CACHE[cache_key] = _get_secret_key(settings)
    return _SECRET_KEY_CACHE[cache_key]


def generate_csrf_token(settings: Settings = Depends(get_settings)) -> str:
    """CSRFトークンを生成（タイムスタンプ + HMAC署名）"""
    timestamp = int(time.time())
    secret_key = get_secret_key(settings)
    signature = hmac.new(
        secret_key, str(timestamp).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{timestamp}.{signature}"


def verify_csrf_token(token: str, settings: Settings) -> bool:
    """CSRFトークンを検証（署名 + 有効期限チェック）"""
    try:
        timestamp_str, signature = token.split(".", 1)
        timestamp = int(timestamp_str)
    except (ValueError, AttributeError):
        return False

    # 有効期限チェック
    current_time = int(time.time())
    expire_seconds = settings.csrf_token_expire_minutes * 60
    if current_time - timestamp > expire_seconds:
        return False

    # 署名検証
    secret_key = get_secret_key(settings)
    expected_signature = hmac.new(
        secret_key, str(timestamp).encode("utf-8"), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


async def require_csrf_token(
    csrf_token: str | None = Depends(CSRF_TOKEN_HEADER),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    CSRFトークンを検証する依存関数

    UI経由のリクエストのみ許可し、外部APIクライアントを遮断
    """
    if csrf_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CSRFトークンが必要です",
            headers={"WWW-Authenticate": "CSRF-Token"},
        )

    if not verify_csrf_token(csrf_token, settings):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無効または期限切れのCSRFトークンです",
        )

    return csrf_token
