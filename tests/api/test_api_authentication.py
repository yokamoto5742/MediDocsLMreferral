"""API認証の統合テスト"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.core.config import get_settings
from app.main import app


class TestApiAuthentication:
    """APIエンドポイントの認証テスト"""

    def test_api_endpoint_requires_authentication_when_key_configured(
        self, client: TestClient
    ):
        """MEDIDOCS_API_KEY設定時、ヘッダーなしで401エラー"""
        # settingsのapi_keyをオーバーライド
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"
        mock_settings.prompt_management = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            # 認証が必要なエンドポイント (/api/summary/generate) を使用
            response = client.post(
                "/api/summary/generate",
                json={
                    "medical_text": "test",
                    "department": "内科",
                    "document_type": "診療情報提供書",
                },
            )
            assert response.status_code == 401
            assert "APIキーが必要です" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_api_endpoint_with_invalid_key(self, client: TestClient):
        """無効なAPIキーで403エラー"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"
        mock_settings.prompt_management = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            # 認証が必要なエンドポイント (/api/summary/generate) を使用
            response = client.post(
                "/api/summary/generate",
                json={
                    "medical_text": "test",
                    "department": "内科",
                    "document_type": "診療情報提供書",
                },
                headers={"X-API-Key": "wrong-key"},
            )
            assert response.status_code == 403
            assert "無効なAPIキーです" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_api_endpoint_with_valid_key(self, client: TestClient):
        """有効なAPIキーで認証成功"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"
        mock_settings.prompt_management = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            # 認証が必要なエンドポイント (/api/summary/generate) を使用
            response = client.post(
                "/api/summary/generate",
                json={
                    "medical_text": "test",
                    "department": "内科",
                    "document_type": "診療情報提供書",
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
        """開発モード（MEDIDOCS_API_KEY未設定）は認証なしでアクセス可能"""
        mock_settings = MagicMock()
        mock_settings.api_key = None
        mock_settings.prompt_management = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            # 認証が必要なエンドポイント (/api/summary/generate) を使用
            response = client.post(
                "/api/summary/generate",
                json={
                    "medical_text": "test",
                    "department": "内科",
                    "document_type": "診療情報提供書",
                },
            )
            # 認証スキップされるため200または別のステータス
            assert response.status_code not in [401, 403]
        finally:
            app.dependency_overrides.clear()

    def test_admin_endpoints_do_not_require_authentication(
        self, client: TestClient
    ):
        """管理用エンドポイント（/api/settings等）はAPIキー設定時も認証不要"""
        mock_settings = MagicMock()
        mock_settings.api_key = "test-secret-key"
        mock_settings.prompt_management = True
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            # 管理用エンドポイントは認証なしでアクセス可能
            response = client.get("/api/settings/departments")
            assert response.status_code == 200
            assert "departments" in response.json()
        finally:
            app.dependency_overrides.clear()
