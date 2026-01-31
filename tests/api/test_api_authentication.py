"""API認証の統合テスト"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.core.config import get_settings
from app.main import app


class TestApiAuthentication:
    """APIエンドポイントの認証テスト"""

    def test_admin_api_does_not_require_authentication(
        self, client: TestClient
    ):
        """管理用API（プロンプト管理等）はAPI_KEY設定時も認証不要"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"
        mock_settings.prompt_management = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            # 管理用エンドポイントはAPIキーなしでアクセス可能
            response = client.get("/api/settings/departments")
            assert response.status_code not in [401, 403]

            response = client.get("/api/prompts/")
            assert response.status_code not in [401, 403]
        finally:
            app.dependency_overrides.clear()

    def test_public_api_requires_authentication_when_key_configured(
        self, client: TestClient
    ):
        """公開API（文書生成等）はAPI_KEY設定時、ヘッダーなしで401エラー"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"
        mock_settings.anthropic_model = "claude-3-5-sonnet-20241022"
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            # 文書生成APIはAPIキーが必要
            response = client.post(
                "/api/summary/generate",
                json={
                    "medical_text": "test",
                    "department": "default",
                    "doctor": "default",
                    "document_type": "他院への紹介",
                }
            )
            assert response.status_code == 401
            assert "APIキーが必要です" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_public_api_with_invalid_key(self, client: TestClient):
        """公開APIで無効なAPIキーの場合403エラー"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"
        mock_settings.anthropic_model = "claude-3-5-sonnet-20241022"
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            response = client.post(
                "/api/summary/generate",
                json={
                    "medical_text": "test",
                    "department": "default",
                    "doctor": "default",
                    "document_type": "他院への紹介",
                },
                headers={"X-API-Key": "wrong-key"},
            )
            assert response.status_code == 403
            assert "無効なAPIキーです" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_public_api_with_valid_key(self, client: TestClient):
        """公開APIで有効なAPIキーの場合認証成功"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"
        mock_settings.anthropic_model = "claude-3-5-sonnet-20241022"
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            response = client.post(
                "/api/summary/generate",
                json={
                    "medical_text": "test",
                    "department": "default",
                    "doctor": "default",
                    "document_type": "他院への紹介",
                },
                headers={"X-API-Key": "test-secret-key"},
            )
            # 認証は成功（他のエラーがあれば別の理由）
            assert response.status_code not in [401, 403]
        finally:
            app.dependency_overrides.clear()

    def test_web_pages_do_not_require_authentication(
        self, client: TestClient
    ):
        """WebページUIは認証不要"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            response = client.get("/")
            # トップページは認証なしでアクセス可能
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_development_mode_allows_access_without_key(
        self, client: TestClient
    ):
        """開発モード（API_KEY未設定）は認証なしでアクセス可能"""
        mock_settings = MagicMock()
        mock_settings.api_key = None
        mock_settings.prompt_management = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            response = client.get("/api/settings/departments")
            # 認証スキップされるため200または別のステータス
            assert response.status_code not in [401, 403]
        finally:
            app.dependency_overrides.clear()
