"""CSRF認証の統合テスト"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import generate_csrf_token
from app.main import app


class TestCsrfAuthentication:
    """APIエンドポイントのCSRF認証テスト"""

    def test_protected_endpoint_requires_csrf_token(self, client: TestClient):
        """保護されたエンドポイントはCSRFトークンなしで401エラー"""
        response = client.post(
            "/api/summary/generate",
            json={
                "medical_text": "test",
                "department": "内科",
                "document_type": "診療情報提供書",
            },
        )
        assert response.status_code == 401
        assert "CSRFトークンが必要です" in response.json()["detail"]

    def test_protected_endpoint_with_invalid_token(self, client: TestClient):
        """無効なCSRFトークンで403エラー"""
        response = client.post(
            "/api/summary/generate",
            json={
                "medical_text": "test",
                "department": "内科",
                "document_type": "診療情報提供書",
            },
            headers={"X-CSRF-Token": "invalid.token"},
        )
        assert response.status_code == 403
        assert "無効または期限切れのCSRFトークンです" in response.json()["detail"]

    def test_protected_endpoint_with_valid_token(self, client: TestClient):
        """有効なCSRFトークンで認証成功"""
        mock_settings = MagicMock()
        mock_settings.csrf_secret_key = "test-csrf-secret-key"
        mock_settings.csrf_token_expire_minutes = 60

        token = generate_csrf_token(mock_settings)

        response = client.post(
            "/api/summary/generate",
            json={
                "medical_text": "test",
                "department": "内科",
                "document_type": "診療情報提供書",
            },
            headers={"X-CSRF-Token": token},
        )
        # CSRF認証は成功（他のエラーがあれば別の理由）
        assert response.status_code not in [401, 403]

    def test_evaluation_endpoint_requires_csrf_token(self, client: TestClient):
        """評価エンドポイントもCSRFトークン必須"""
        response = client.post(
            "/api/evaluation/evaluate",
            json={
                "document_type": "診療情報提供書",
                "input_text": "test",
                "output_summary": "test",
            },
        )
        assert response.status_code == 401
        assert "CSRFトークンが必要です" in response.json()["detail"]

    def test_web_pages_do_not_require_csrf(self, client: TestClient):
        """WebページUIはCSRF認証不要"""
        response = client.get("/")
        assert response.status_code == 200

    def test_admin_endpoints_do_not_require_csrf(self, client: TestClient):
        """管理用エンドポイント（/api/settings等）はCSRF認証不要"""
        response = client.get("/api/settings/departments")
        assert response.status_code == 200
        assert "departments" in response.json()

    def test_models_endpoint_does_not_require_csrf(self, client: TestClient):
        """モデル一覧エンドポイントはCSRF認証不要"""
        response = client.get("/api/summary/models")
        assert response.status_code == 200
