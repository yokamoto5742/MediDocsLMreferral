"""GeminiAPIClient のテスト"""

import json
import os
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest

from app.core.constants import MESSAGES
from app.external.gemini_api import GeminiAPIClient
from app.utils.exceptions import APIError


class TestGeminiAPIClientInitialization:
    """GeminiAPIClient 初期化のテスト"""

    @patch("app.external.gemini_api.settings")
    def test_init_with_settings(self, mock_settings):
        """初期化 - 設定から取得"""
        mock_settings.gemini_model = "gemini-1.5-pro-002"

        client = GeminiAPIClient()

        assert client.default_model == "gemini-1.5-pro-002"
        assert client.client is None

    @patch("app.external.gemini_api.settings")
    def test_init_without_gemini_model(self, mock_settings):
        """初期化 - gemini_model なし"""
        mock_settings.gemini_model = None

        client = GeminiAPIClient()

        assert client.default_model is None


class TestGeminiAPIClientInitialize:
    """GeminiAPIClient initialize メソッドのテスト"""

    @patch("app.external.gemini_api.genai.Client")
    @patch("app.external.gemini_api.service_account.Credentials.from_service_account_info")
    @patch("app.external.gemini_api.settings")
    def test_initialize_with_credentials_json_success(
        self, mock_settings, mock_from_service_account_info, mock_genai_client
    ):
        """initialize - GOOGLE_CREDENTIALS_JSON を使用して成功"""
        # 設定のモック
        mock_settings.google_project_id = "test-project-123"
        mock_settings.google_location = "us-central1"

        # 認証情報のモック
        credentials_dict = {
            "type": "service_account",
            "project_id": "test-project-123",
            "private_key_id": "key123",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }

        mock_credentials = MagicMock()
        mock_from_service_account_info.return_value = mock_credentials

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        # 環境変数を設定
        with patch.dict(
            os.environ, {"GOOGLE_CREDENTIALS_JSON": json.dumps(credentials_dict)}
        ):
            client = GeminiAPIClient()
            result = client.initialize()

        assert result is True
        assert client.client is mock_client_instance

        # 認証情報が正しく作成されたことを確認
        mock_from_service_account_info.assert_called_once_with(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        # クライアントが正しい引数で作成されたことを確認
        mock_genai_client.assert_called_once_with(
            vertexai=True,
            project="test-project-123",
            location="us-central1",
            credentials=mock_credentials,
        )

    @patch("app.external.gemini_api.genai.Client")
    @patch("app.external.gemini_api.settings")
    def test_initialize_without_credentials_json(
        self, mock_settings, mock_genai_client
    ):
        """initialize - GOOGLE_CREDENTIALS_JSON なし（デフォルト認証）"""
        mock_settings.google_project_id = "test-project-456"
        mock_settings.google_location = "global"

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        with patch.dict(os.environ, {}, clear=True):
            client = GeminiAPIClient()
            result = client.initialize()

        assert result is True
        assert client.client is mock_client_instance

        # デフォルト認証でクライアントが作成されたことを確認
        mock_genai_client.assert_called_once_with(
            vertexai=True,
            project="test-project-456",
            location="global",
        )

    @patch("app.external.gemini_api.settings")
    def test_initialize_missing_project_id(self, mock_settings):
        """initialize - GOOGLE_PROJECT_ID 未設定"""
        mock_settings.google_project_id = None

        client = GeminiAPIClient()

        with pytest.raises(APIError) as exc_info:
            client.initialize()

        assert str(exc_info.value) == MESSAGES["GOOGLE_PROJECT_ID_MISSING"]

    @patch("app.external.gemini_api.settings")
    def test_initialize_invalid_json_format(self, mock_settings):
        """initialize - 不正なJSON形式"""
        mock_settings.google_project_id = "test-project"

        invalid_json = "{ invalid json format"

        with patch.dict(os.environ, {"GOOGLE_CREDENTIALS_JSON": invalid_json}):
            client = GeminiAPIClient()

            with pytest.raises(APIError) as exc_info:
                client.initialize()

            assert "GOOGLE_CREDENTIALS_JSON環境変数の解析エラー" in str(exc_info.value)

    @patch("app.external.gemini_api.service_account.Credentials.from_service_account_info")
    @patch("app.external.gemini_api.settings")
    def test_initialize_missing_credential_fields(
        self, mock_settings, mock_from_service_account_info
    ):
        """initialize - 認証情報フィールド不足"""
        mock_settings.google_project_id = "test-project"
        mock_settings.google_location = "global"

        # 必須フィールドが欠けている認証情報
        incomplete_credentials = {
            "type": "service_account",
            # project_id が欠落
        }

        mock_from_service_account_info.side_effect = KeyError("project_id")

        with patch.dict(
            os.environ, {"GOOGLE_CREDENTIALS_JSON": json.dumps(incomplete_credentials)}
        ):
            client = GeminiAPIClient()

            with pytest.raises(APIError) as exc_info:
                client.initialize()

            assert "認証情報に必要なフィールドが不足" in str(exc_info.value)

    @patch("app.external.gemini_api.genai.Client")
    @patch("app.external.gemini_api.settings")
    def test_initialize_genai_client_error(self, mock_settings, mock_genai_client):
        """initialize - genai.Client 作成エラー"""
        mock_settings.google_project_id = "test-project"
        mock_settings.google_location = "global"

        mock_genai_client.side_effect = Exception("API接続エラー")

        with patch.dict(os.environ, {}, clear=True):
            client = GeminiAPIClient()

            with pytest.raises(APIError) as exc_info:
                client.initialize()

            error_message = str(exc_info.value)
            assert "Vertex AI初期化エラー" in error_message
            assert "API接続エラー" in error_message

    @patch("app.external.gemini_api.service_account.Credentials.from_service_account_info")
    @patch("app.external.gemini_api.settings")
    def test_initialize_credentials_creation_error(
        self, mock_settings, mock_from_service_account_info
    ):
        """initialize - 認証情報作成エラー"""
        mock_settings.google_project_id = "test-project"
        mock_settings.google_location = "global"

        credentials_dict = {"type": "service_account"}
        mock_from_service_account_info.side_effect = Exception("認証情報作成失敗")

        with patch.dict(
            os.environ, {"GOOGLE_CREDENTIALS_JSON": json.dumps(credentials_dict)}
        ):
            client = GeminiAPIClient()

            with pytest.raises(APIError) as exc_info:
                client.initialize()

            assert "認証情報の作成エラー" in str(exc_info.value)


class TestGeminiAPIClientGenerateContent:
    """GeminiAPIClient _generate_content メソッドのテスト"""

    @patch("app.external.gemini_api.settings")
    def test_generate_content_success_with_low_thinking(self, mock_settings):
        """_generate_content - 正常系（ThinkingLevel.LOW）"""
        mock_settings.gemini_thinking_level = "LOW"

        # モッククライアントとレスポンス
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "生成されたサマリー"
        mock_response.usage_metadata.prompt_token_count = 2000
        mock_response.usage_metadata.candidates_token_count = 1000

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiAPIClient()
        client.client = mock_client

        result = client._generate_content(
            prompt="テストプロンプト", model_name="gemini-1.5-pro-002"
        )

        assert result == ("生成されたサマリー", 2000, 1000)

        # generate_content が正しく呼ばれたことを確認
        call_args = mock_client.models.generate_content.call_args
        assert call_args[1]["model"] == "gemini-1.5-pro-002"
        assert call_args[1]["contents"] == "テストプロンプト"

    @patch("app.external.gemini_api.types")
    @patch("app.external.gemini_api.settings")
    def test_generate_content_success_with_high_thinking(
        self, mock_settings, mock_types
    ):
        """_generate_content - 正常系（ThinkingLevel.HIGH）"""
        mock_settings.gemini_thinking_level = "HIGH"

        mock_types.ThinkingLevel.HIGH = "HIGH"
        mock_types.ThinkingLevel.LOW = "LOW"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "高品質サマリー"
        mock_response.usage_metadata.prompt_token_count = 3000
        mock_response.usage_metadata.candidates_token_count = 1500

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiAPIClient()
        client.client = mock_client

        result = client._generate_content(
            prompt="プロンプト", model_name="gemini-1.5-pro-002"
        )

        assert result == ("高品質サマリー", 3000, 1500)

    @patch("app.external.gemini_api.settings")
    def test_generate_content_no_text_attribute(self, mock_settings):
        """_generate_content - text 属性なし"""
        mock_settings.gemini_thinking_level = "LOW"

        mock_client = MagicMock()

        # text 属性がないレスポンスオブジェクトを作成
        class NoTextResponse:
            def __init__(self):
                self.usage_metadata = MagicMock()
                self.usage_metadata.prompt_token_count = 100
                self.usage_metadata.candidates_token_count = 50

            def __str__(self):
                return "文字列化されたレスポンス"

        mock_response = NoTextResponse()
        mock_client.models.generate_content.return_value = mock_response

        client = GeminiAPIClient()
        client.client = mock_client

        result = client._generate_content(prompt="プロンプト", model_name="test-model")

        assert result == ("文字列化されたレスポンス", 100, 50)

    @patch("app.external.gemini_api.settings")
    def test_generate_content_no_usage_metadata(self, mock_settings):
        """_generate_content - usage_metadata なし"""
        mock_settings.gemini_thinking_level = "LOW"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "サマリー"
        # usage_metadata 属性なし
        delattr(mock_response, "usage_metadata")

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiAPIClient()
        client.client = mock_client

        result = client._generate_content(prompt="プロンプト", model_name="test-model")

        # usage_metadata がない場合は 0 を返す
        assert result == ("サマリー", 0, 0)

    @patch("app.external.gemini_api.settings")
    def test_generate_content_api_error(self, mock_settings):
        """_generate_content - API呼び出しエラー"""
        mock_settings.gemini_thinking_level = "LOW"

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception(
            "Vertex AI APIエラー"
        )

        client = GeminiAPIClient()
        client.client = mock_client

        with pytest.raises(APIError) as exc_info:
            client._generate_content(prompt="プロンプト", model_name="test-model")

        error_message = str(exc_info.value)
        assert "Vertex AI API呼び出しエラー" in error_message
        assert "Vertex AI APIエラー" in error_message

    @patch("app.external.gemini_api.settings")
    def test_generate_content_thinking_level_config(self, mock_settings):
        """_generate_content - ThinkingLevel 設定確認"""
        mock_settings.gemini_thinking_level = "LOW"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "テキスト"
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiAPIClient()
        client.client = mock_client

        client._generate_content(prompt="プロンプト", model_name="test-model")

        # generate_content の config 引数を確認
        call_args = mock_client.models.generate_content.call_args
        config = call_args[1]["config"]
        assert config is not None


class TestGeminiAPIClientIntegration:
    """GeminiAPIClient 統合テスト"""

    @patch("app.external.gemini_api.genai.Client")
    @patch("app.services.prompt_service.get_prompt")
    @patch("app.core.database.get_db_session")
    @patch("app.external.gemini_api.settings")
    def test_full_generate_summary_flow(
        self, mock_settings, mock_db_session, mock_get_prompt, mock_genai_client
    ):
        """完全な文書生成フロー"""
        # 設定のモック
        mock_settings.google_project_id = "test-project"
        mock_settings.google_location = "global"
        mock_settings.gemini_model = "gemini-1.5-pro-002"
        mock_settings.gemini_thinking_level = "HIGH"

        # プロンプトのモック
        mock_db = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_db
        mock_get_prompt.return_value = None

        # クライアントとレスポンスのモック
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "生成された診療情報提供書"
        mock_response.usage_metadata.prompt_token_count = 3000
        mock_response.usage_metadata.candidates_token_count = 1500

        mock_client_instance.models.generate_content.return_value = mock_response
        mock_genai_client.return_value = mock_client_instance

        # テスト実行
        with patch.dict(os.environ, {}, clear=True):
            client = GeminiAPIClient()
            result = client.generate_summary(
                medical_text="患者情報",
                additional_info="追加情報",
                referral_purpose="精査依頼",
                current_prescription="処方内容",
                department="default",
                document_type="他院への紹介",
                doctor="default",
            )

        assert result == ("生成された診療情報提供書", 3000, 1500)

    @patch("app.external.gemini_api.settings")
    def test_generate_summary_initialization_error(self, mock_settings):
        """generate_summary - 初期化エラー"""
        mock_settings.google_project_id = None

        client = GeminiAPIClient()

        with pytest.raises(APIError) as exc_info:
            client.generate_summary(medical_text="データ")

        assert MESSAGES["GOOGLE_PROJECT_ID_MISSING"] in str(exc_info.value)


class TestGeminiAPIClientEdgeCases:
    """GeminiAPIClient エッジケース"""

    @patch("app.external.gemini_api.settings")
    def test_generate_content_very_long_prompt(self, mock_settings):
        """_generate_content - 非常に長いプロンプト"""
        mock_settings.gemini_thinking_level = "LOW"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "サマリー"
        mock_response.usage_metadata.prompt_token_count = 100000
        mock_response.usage_metadata.candidates_token_count = 5000

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiAPIClient()
        client.client = mock_client

        long_prompt = "あ" * 200000
        result = client._generate_content(prompt=long_prompt, model_name="test-model")

        assert result == ("サマリー", 100000, 5000)

    @patch("app.external.gemini_api.settings")
    def test_generate_content_special_characters(self, mock_settings):
        """_generate_content - 特殊文字を含むプロンプト"""
        mock_settings.gemini_thinking_level = "LOW"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "結果"
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiAPIClient()
        client.client = mock_client

        special_prompt = "特殊文字: \n\t\r\n!@#$%^&*(){}[]<>?/\\|`~"
        result = client._generate_content(
            prompt=special_prompt, model_name="test-model"
        )

        assert result[0] == "結果"

    @patch("app.external.gemini_api.settings")
    def test_generate_content_empty_prompt(self, mock_settings):
        """_generate_content - 空のプロンプト"""
        mock_settings.gemini_thinking_level = "LOW"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "空レスポンス"
        mock_response.usage_metadata.prompt_token_count = 0
        mock_response.usage_metadata.candidates_token_count = 10

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiAPIClient()
        client.client = mock_client

        result = client._generate_content(prompt="", model_name="test-model")

        assert result == ("空レスポンス", 0, 10)

    @patch("app.external.gemini_api.genai.Client")
    @patch("app.external.gemini_api.settings")
    def test_initialize_empty_project_id(self, mock_settings, mock_genai_client):
        """initialize - 空の PROJECT_ID"""
        mock_settings.google_project_id = ""

        client = GeminiAPIClient()

        with pytest.raises(APIError) as exc_info:
            client.initialize()

        assert MESSAGES["GOOGLE_PROJECT_ID_MISSING"] in str(exc_info.value)

    @patch("app.external.gemini_api.genai.Client")
    @patch("app.external.gemini_api.service_account.Credentials.from_service_account_info")
    @patch("app.external.gemini_api.settings")
    def test_initialize_empty_credentials_json(
        self, mock_settings, mock_from_service_account_info, mock_genai_client
    ):
        """initialize - 空の GOOGLE_CREDENTIALS_JSON"""
        mock_settings.google_project_id = "test-project"
        mock_settings.google_location = "global"

        # 空文字列の場合は os.environ.get() が空文字列を返すが、
        # if google_credentials_json: は False になるためデフォルト認証が使われる
        # デフォルト認証の成功をシミュレート
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        with patch.dict(os.environ, {"GOOGLE_CREDENTIALS_JSON": ""}):
            client = GeminiAPIClient()
            result = client.initialize()

        # 空文字列は False として扱われるため、デフォルト認証が使われて成功する
        assert result is True
        mock_genai_client.assert_called_once_with(
            vertexai=True,
            project="test-project",
            location="global",
        )
