"""APIキー認証のテスト"""
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from app.core.security import verify_api_key


class TestVerifyApiKey:
    """verify_api_key関数のテスト"""

    def test_development_mode_no_api_key_configured(self):
        """MEDIDOCS_API_KEY未設定時は認証スキップ"""
        mock_settings = MagicMock()
        mock_settings.api_key = None

        # 同期関数として呼び出し
        import asyncio
        result = asyncio.run(verify_api_key(
            api_key_header=None, settings=mock_settings
        ))
        assert result is None

    def test_development_mode_with_header_still_allows(self):
        """MEDIDOCS_API_KEY未設定時はヘッダーがあっても認証スキップ"""
        mock_settings = MagicMock()
        mock_settings.api_key = None

        import asyncio
        result = asyncio.run(verify_api_key(
            api_key_header="any-key", settings=mock_settings
        ))
        assert result is None

    def test_missing_api_key_header(self):
        """APIキー未提供時は401エラー"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(verify_api_key(
                api_key_header=None, settings=mock_settings
            ))

        assert exc_info.value.status_code == 401
        assert "APIキーが必要です" in exc_info.value.detail

    def test_invalid_api_key(self):
        """無効なAPIキーは403エラー"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(verify_api_key(
                api_key_header="wrong-key", settings=mock_settings
            ))

        assert exc_info.value.status_code == 403
        assert "無効なAPIキーです" in exc_info.value.detail

    def test_valid_api_key(self):
        """有効なAPIキーで認証成功"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"

        import asyncio
        result = asyncio.run(verify_api_key(
            api_key_header="test-secret-key", settings=mock_settings
        ))
        assert result == "test-secret-key"
