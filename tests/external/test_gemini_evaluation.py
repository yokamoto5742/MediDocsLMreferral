"""GeminiEvaluationClient のテスト"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from app.core.constants import MESSAGES
from app.external.gemini_evaluation import GeminiEvaluationClient
from app.utils.exceptions import APIError


class TestGeminiEvaluationClientInitialization:
    """GeminiEvaluationClient 初期化のテスト"""

    @patch("app.external.gemini_evaluation.get_settings")
    def test_init_with_settings(self, mock_get_settings):
        """初期化 - 設定から取得"""
        mock_settings = MagicMock()
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        client = GeminiEvaluationClient()

        assert client.default_model == "gemini-2.0-flash-thinking-exp-01-21"
        assert client.client is None

    @patch("app.external.gemini_evaluation.get_settings")
    def test_init_without_evaluation_model(self, mock_get_settings):
        """初期化 - evaluation_model なし"""
        mock_settings = MagicMock()
        mock_settings.gemini_evaluation_model = None
        mock_get_settings.return_value = mock_settings

        client = GeminiEvaluationClient()

        assert client.default_model is None


class TestGeminiEvaluationClientInitialize:
    """GeminiEvaluationClient initialize メソッドのテスト"""

    @patch("app.external.gemini_evaluation.genai.Client")
    @patch("app.external.gemini_evaluation.service_account.Credentials.from_service_account_info")
    @patch("app.external.gemini_evaluation.get_settings")
    def test_initialize_with_credentials_json_success(
        self, mock_get_settings, mock_from_service_account_info, mock_genai_client
    ):
        """initialize - GOOGLE_CREDENTIALS_JSON を使用して成功"""
        # 設定のモック
        mock_settings = MagicMock()
        mock_settings.google_project_id = "test-project-123"
        mock_settings.google_location = "us-central1"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"

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

        mock_settings.google_credentials_json = json.dumps(credentials_dict)
        mock_get_settings.return_value = mock_settings

        mock_credentials = MagicMock()
        mock_from_service_account_info.return_value = mock_credentials

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        client = GeminiEvaluationClient()
        result = client.initialize()

        assert result is True
        assert client.client is mock_client_instance

        # 認証情報が正しく作成されたことを確認
        mock_from_service_account_info.assert_called_once_with(
            credentials_dict,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )

        # クライアントが正しい引数で作成されたことを確認
        mock_genai_client.assert_called_once_with(
            vertexai=True,
            project="test-project-123",
            location="us-central1",
            credentials=mock_credentials,
        )

    @patch("app.external.gemini_evaluation.genai.Client")
    @patch("app.external.gemini_evaluation.get_settings")
    def test_initialize_without_credentials_json(
        self, mock_get_settings, mock_genai_client
    ):
        """initialize - GOOGLE_CREDENTIALS_JSON なし（デフォルト認証）"""
        mock_settings = MagicMock()
        mock_settings.google_project_id = "test-project-456"
        mock_settings.google_location = "global"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_settings.google_credentials_json = None
        mock_get_settings.return_value = mock_settings

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        client = GeminiEvaluationClient()
        result = client.initialize()

        assert result is True
        assert client.client is mock_client_instance

        # デフォルト認証でクライアントが作成されたことを確認
        mock_genai_client.assert_called_once_with(
            vertexai=True,
            project="test-project-456",
            location="global",
        )

    @patch("app.external.gemini_evaluation.get_settings")
    def test_initialize_missing_project_id(self, mock_get_settings):
        """initialize - GOOGLE_PROJECT_ID 未設定"""
        mock_settings = MagicMock()
        mock_settings.google_project_id = None
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        client = GeminiEvaluationClient()

        with pytest.raises(APIError) as exc_info:
            client.initialize()

        assert str(exc_info.value) == MESSAGES["VERTEX_AI_PROJECT_MISSING"]

    @patch("app.external.gemini_evaluation.get_settings")
    def test_initialize_invalid_json_format(self, mock_get_settings):
        """initialize - 不正なJSON形式"""
        mock_settings = MagicMock()
        mock_settings.google_project_id = "test-project"
        mock_settings.google_location = "global"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_settings.google_credentials_json = "{ invalid json format"
        mock_get_settings.return_value = mock_settings

        client = GeminiEvaluationClient()

        with pytest.raises(APIError) as exc_info:
            client.initialize()

        assert "認証情報JSONのパースに失敗しました" in str(exc_info.value)

    @patch("app.external.gemini_evaluation.service_account.Credentials.from_service_account_info")
    @patch("app.external.gemini_evaluation.get_settings")
    def test_initialize_missing_credential_fields(
        self, mock_get_settings, mock_from_service_account_info
    ):
        """initialize - 認証情報フィールド不足"""
        mock_settings = MagicMock()
        mock_settings.google_project_id = "test-project"
        mock_settings.google_location = "global"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"

        # 必須フィールドが欠けている認証情報
        incomplete_credentials = {
            "type": "service_account",
            # project_id が欠落
        }

        mock_settings.google_credentials_json = json.dumps(incomplete_credentials)
        mock_get_settings.return_value = mock_settings

        mock_from_service_account_info.side_effect = KeyError("project_id")

        client = GeminiEvaluationClient()

        with pytest.raises(APIError) as exc_info:
            client.initialize()

        assert "認証情報に必要なフィールドがありません" in str(exc_info.value)

    @patch("app.external.gemini_evaluation.genai.Client")
    @patch("app.external.gemini_evaluation.get_settings")
    def test_initialize_genai_client_error(self, mock_get_settings, mock_genai_client):
        """initialize - genai.Client 作成エラー"""
        mock_settings = MagicMock()
        mock_settings.google_project_id = "test-project"
        mock_settings.google_location = "global"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_settings.google_credentials_json = None
        mock_get_settings.return_value = mock_settings

        mock_genai_client.side_effect = Exception("API接続エラー")

        client = GeminiEvaluationClient()

        with pytest.raises(APIError) as exc_info:
            client.initialize()

        error_message = str(exc_info.value)
        assert "Vertex AI初期化エラー" in error_message
        assert "API接続エラー" in error_message

    @patch("app.external.gemini_evaluation.service_account.Credentials.from_service_account_info")
    @patch("app.external.gemini_evaluation.get_settings")
    def test_initialize_credentials_creation_error(
        self, mock_get_settings, mock_from_service_account_info
    ):
        """initialize - 認証情報作成エラー"""
        mock_settings = MagicMock()
        mock_settings.google_project_id = "test-project"
        mock_settings.google_location = "global"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"

        credentials_dict = {"type": "service_account"}
        mock_settings.google_credentials_json = json.dumps(credentials_dict)
        mock_get_settings.return_value = mock_settings

        mock_from_service_account_info.side_effect = Exception("認証情報作成失敗")

        client = GeminiEvaluationClient()

        with pytest.raises(APIError) as exc_info:
            client.initialize()

        assert "認証情報の処理中にエラーが発生しました" in str(exc_info.value)


class TestGeminiEvaluationClientGenerateContent:
    """GeminiEvaluationClient _generate_content メソッドのテスト"""

    @patch("app.external.gemini_evaluation.get_settings")
    def test_generate_content_success_with_low_thinking(self, mock_get_settings):
        """_generate_content - 正常系（ThinkingLevel.LOW）"""
        mock_settings = MagicMock()
        mock_settings.gemini_thinking_level = "LOW"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        # モッククライアントとレスポンス
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "評価結果: 良好です"
        mock_response.usage_metadata.prompt_token_count = 2000
        mock_response.usage_metadata.candidates_token_count = 1000

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiEvaluationClient()
        client.client = mock_client

        result = client._generate_content(
            prompt="評価プロンプト", model_name="gemini-2.0-flash-thinking-exp-01-21"
        )

        assert result == ("評価結果: 良好です", 2000, 1000)

        # generate_content が正しく呼ばれたことを確認
        call_args = mock_client.models.generate_content.call_args
        assert call_args[1]["model"] == "gemini-2.0-flash-thinking-exp-01-21"
        assert call_args[1]["contents"] == "評価プロンプト"

    @patch("app.external.gemini_evaluation.types")
    @patch("app.external.gemini_evaluation.get_settings")
    def test_generate_content_success_with_high_thinking(
        self, mock_get_settings, mock_types
    ):
        """_generate_content - 正常系（ThinkingLevel.HIGH）"""
        mock_settings = MagicMock()
        mock_settings.gemini_thinking_level = "HIGH"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        mock_types.ThinkingLevel.HIGH = "HIGH"
        mock_types.ThinkingLevel.LOW = "LOW"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "詳細な評価結果"
        mock_response.usage_metadata.prompt_token_count = 3000
        mock_response.usage_metadata.candidates_token_count = 1500

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiEvaluationClient()
        client.client = mock_client

        result = client._generate_content(
            prompt="評価プロンプト", model_name="gemini-2.0-flash-thinking-exp-01-21"
        )

        assert result == ("詳細な評価結果", 3000, 1500)

    @patch("app.external.gemini_evaluation.get_settings")
    def test_generate_content_no_text_attribute(self, mock_get_settings):
        """_generate_content - text 属性なし"""
        mock_settings = MagicMock()
        mock_settings.gemini_thinking_level = "LOW"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

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

        client = GeminiEvaluationClient()
        client.client = mock_client

        result = client._generate_content(prompt="プロンプト", model_name="test-model")

        assert result == ("文字列化されたレスポンス", 100, 50)

    @patch("app.external.gemini_evaluation.get_settings")
    def test_generate_content_no_usage_metadata(self, mock_get_settings):
        """_generate_content - usage_metadata なし"""
        mock_settings = MagicMock()
        mock_settings.gemini_thinking_level = "LOW"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "評価結果"
        # usage_metadata 属性なし
        delattr(mock_response, "usage_metadata")

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiEvaluationClient()
        client.client = mock_client

        result = client._generate_content(prompt="プロンプト", model_name="test-model")

        # usage_metadata がない場合は 0 を返す
        assert result == ("評価結果", 0, 0)

    @patch("app.external.gemini_evaluation.get_settings")
    def test_generate_content_api_error(self, mock_get_settings):
        """_generate_content - API呼び出しエラー"""
        mock_settings = MagicMock()
        mock_settings.gemini_thinking_level = "LOW"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception(
            "Vertex AI APIエラー"
        )

        client = GeminiEvaluationClient()
        client.client = mock_client

        with pytest.raises(APIError) as exc_info:
            client._generate_content(prompt="プロンプト", model_name="test-model")

        error_message = str(exc_info.value)
        assert "Vertex AI API呼び出しエラー" in error_message
        assert "Vertex AI APIエラー" in error_message

    @patch("app.external.gemini_evaluation.get_settings")
    def test_generate_content_thinking_level_config(self, mock_get_settings):
        """_generate_content - ThinkingLevel 設定確認"""
        mock_settings = MagicMock()
        mock_settings.gemini_thinking_level = "LOW"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "評価結果"
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiEvaluationClient()
        client.client = mock_client

        client._generate_content(prompt="プロンプト", model_name="test-model")

        # generate_content の config 引数を確認
        call_args = mock_client.models.generate_content.call_args
        config = call_args[1]["config"]
        assert config is not None


class TestGeminiEvaluationClientEdgeCases:
    """GeminiEvaluationClient エッジケース"""

    @patch("app.external.gemini_evaluation.get_settings")
    def test_generate_content_very_long_prompt(self, mock_get_settings):
        """_generate_content - 非常に長いプロンプト"""
        mock_settings = MagicMock()
        mock_settings.gemini_thinking_level = "LOW"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "評価結果"
        mock_response.usage_metadata.prompt_token_count = 100000
        mock_response.usage_metadata.candidates_token_count = 5000

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiEvaluationClient()
        client.client = mock_client

        long_prompt = "評価対象" * 50000
        result = client._generate_content(prompt=long_prompt, model_name="test-model")

        assert result == ("評価結果", 100000, 5000)

    @patch("app.external.gemini_evaluation.get_settings")
    def test_generate_content_special_characters(self, mock_get_settings):
        """_generate_content - 特殊文字を含むプロンプト"""
        mock_settings = MagicMock()
        mock_settings.gemini_thinking_level = "LOW"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "結果"
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiEvaluationClient()
        client.client = mock_client

        special_prompt = "特殊文字: \n\t\r\n!@#$%^&*(){}[]<>?/\\|`~"
        result = client._generate_content(
            prompt=special_prompt, model_name="test-model"
        )

        assert result[0] == "結果"

    @patch("app.external.gemini_evaluation.get_settings")
    def test_generate_content_empty_prompt(self, mock_get_settings):
        """_generate_content - 空のプロンプト"""
        mock_settings = MagicMock()
        mock_settings.gemini_thinking_level = "LOW"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "空レスポンス"
        mock_response.usage_metadata.prompt_token_count = 0
        mock_response.usage_metadata.candidates_token_count = 10

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiEvaluationClient()
        client.client = mock_client

        result = client._generate_content(prompt="", model_name="test-model")

        assert result == ("空レスポンス", 0, 10)

    @patch("app.external.gemini_evaluation.genai.Client")
    @patch("app.external.gemini_evaluation.get_settings")
    def test_initialize_empty_project_id(self, mock_get_settings, mock_genai_client):
        """initialize - 空の PROJECT_ID"""
        mock_settings = MagicMock()
        mock_settings.google_project_id = ""
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_get_settings.return_value = mock_settings

        client = GeminiEvaluationClient()

        with pytest.raises(APIError) as exc_info:
            client.initialize()

        assert MESSAGES["VERTEX_AI_PROJECT_MISSING"] in str(exc_info.value)

    @patch("app.external.gemini_evaluation.genai.Client")
    @patch("app.external.gemini_evaluation.get_settings")
    def test_initialize_empty_credentials_json(
        self, mock_get_settings, mock_genai_client
    ):
        """initialize - 空の GOOGLE_CREDENTIALS_JSON"""
        mock_settings = MagicMock()
        mock_settings.google_project_id = "test-project"
        mock_settings.google_location = "global"
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"
        mock_settings.google_credentials_json = ""
        mock_get_settings.return_value = mock_settings

        # 空文字列の場合はデフォルト認証が使われる
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        client = GeminiEvaluationClient()
        result = client.initialize()

        # 空文字列は False として扱われるため、デフォルト認証が使われて成功する
        assert result is True
        mock_genai_client.assert_called_once_with(
            vertexai=True,
            project="test-project",
            location="global",
        )
