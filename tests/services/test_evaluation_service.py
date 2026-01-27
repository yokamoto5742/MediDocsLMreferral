"""Evaluation Service のテスト"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.constants import MESSAGES
from app.schemas.evaluation import EvaluationResponse
from app.services.evaluation_service import (
    build_evaluation_prompt,
    create_or_update_evaluation_prompt,
    delete_evaluation_prompt,
    execute_evaluation,
    get_all_evaluation_prompts,
    get_evaluation_prompt,
)


class TestGetEvaluationPrompt:
    """get_evaluation_prompt 関数のテスト"""

    def test_get_evaluation_prompt_exists(self):
        """評価プロンプト取得 - 存在する場合"""
        mock_db = MagicMock()
        mock_prompt = MagicMock()
        mock_prompt.document_type = "他院への紹介"
        mock_prompt.content = "評価プロンプト内容"
        mock_prompt.is_active = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_prompt

        result = get_evaluation_prompt(mock_db, "他院への紹介")

        assert result is mock_prompt
        assert result.document_type == "他院への紹介"

    def test_get_evaluation_prompt_not_exists(self):
        """評価プロンプト取得 - 存在しない場合"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_evaluation_prompt(mock_db, "返書")

        assert result is None


class TestGetAllEvaluationPrompts:
    """get_all_evaluation_prompts 関数のテスト"""

    def test_get_all_evaluation_prompts(self):
        """全評価プロンプト取得 - 正常系"""
        mock_db = MagicMock()
        mock_prompts = [
            MagicMock(document_type="他院への紹介"),
            MagicMock(document_type="返書"),
        ]

        mock_db.query.return_value.order_by.return_value.all.return_value = mock_prompts

        result = get_all_evaluation_prompts(mock_db)

        assert len(result) == 2
        assert result[0].document_type == "他院への紹介"
        assert result[1].document_type == "返書"

    def test_get_all_evaluation_prompts_empty(self):
        """全評価プロンプト取得 - 空リスト"""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.all.return_value = []

        result = get_all_evaluation_prompts(mock_db)

        assert len(result) == 0


class TestCreateOrUpdateEvaluationPrompt:
    """create_or_update_evaluation_prompt 関数のテスト"""

    def test_create_evaluation_prompt_new(self):
        """評価プロンプト作成 - 新規作成"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        success, message = create_or_update_evaluation_prompt(
            mock_db, "他院への紹介", "新しい評価プロンプト"
        )

        assert success is True
        assert message == MESSAGES["EVALUATION_PROMPT_CREATED"]
        mock_db.add.assert_called_once()

        # 追加されたプロンプトを検証
        added_prompt = mock_db.add.call_args[0][0]
        assert added_prompt.document_type == "他院への紹介"
        assert added_prompt.content == "新しい評価プロンプト"
        assert added_prompt.is_active is True

    def test_create_evaluation_prompt_update(self):
        """評価プロンプト作成 - 更新"""
        mock_db = MagicMock()
        mock_existing = MagicMock()
        mock_existing.content = "古いプロンプト"
        mock_existing.is_active = False

        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

        success, message = create_or_update_evaluation_prompt(
            mock_db, "他院への紹介", "更新されたプロンプト"
        )

        assert success is True
        assert message == MESSAGES["EVALUATION_PROMPT_UPDATED"]
        assert mock_existing.content == "更新されたプロンプト"
        assert mock_existing.is_active is True
        mock_db.add.assert_not_called()

    def test_create_evaluation_prompt_empty_content(self):
        """評価プロンプト作成 - 空の内容"""
        mock_db = MagicMock()

        success, message = create_or_update_evaluation_prompt(
            mock_db, "他院への紹介", ""
        )

        assert success is False
        assert message == "評価プロンプトの内容を入力してください"
        mock_db.add.assert_not_called()


class TestDeleteEvaluationPrompt:
    """delete_evaluation_prompt 関数のテスト"""

    def test_delete_evaluation_prompt_success(self):
        """評価プロンプト削除 - 正常系"""
        mock_db = MagicMock()
        mock_prompt = MagicMock()
        mock_prompt.document_type = "他院への紹介"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_prompt

        success, message = delete_evaluation_prompt(mock_db, "他院への紹介")

        assert success is True
        assert message == MESSAGES["EVALUATION_PROMPT_DELETED"]
        mock_db.delete.assert_called_once_with(mock_prompt)

    def test_delete_evaluation_prompt_not_found(self):
        """評価プロンプト削除 - 存在しない場合"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        success, message = delete_evaluation_prompt(mock_db, "返書")

        assert success is False
        assert message == "返書の評価プロンプトが見つかりません"
        mock_db.delete.assert_not_called()


class TestBuildEvaluationPrompt:
    """build_evaluation_prompt 関数のテスト"""

    def test_build_evaluation_prompt(self):
        """評価プロンプト構築 - 正常系"""
        prompt_template = "以下の出力を評価してください。"
        input_text = "患者は60歳男性。"
        current_prescription = "メトホルミン500mg"
        additional_info = "HbA1c 7.5%"
        output_summary = "主病名: 糖尿病"

        result = build_evaluation_prompt(
            prompt_template,
            input_text,
            current_prescription,
            additional_info,
            output_summary
        )

        assert prompt_template in result
        assert "【カルテ記載】" in result
        assert input_text in result
        assert "【現在の処方】" in result
        assert current_prescription in result
        assert "【追加情報】" in result
        assert additional_info in result
        assert "【生成された出力】" in result
        assert output_summary in result

    def test_build_evaluation_prompt_empty_fields(self):
        """評価プロンプト構築 - 空のフィールド"""
        prompt_template = "評価してください"
        result = build_evaluation_prompt(
            prompt_template, "", "", "", "出力内容"
        )

        assert prompt_template in result
        assert "【カルテ記載】" in result
        assert "【生成された出力】" in result
        assert "出力内容" in result


class TestExecuteEvaluation:
    """execute_evaluation 関数のテスト"""

    @patch("app.services.evaluation_service.GeminiAPIClient")
    @patch("app.services.evaluation_service.get_db_session")
    @patch("app.services.evaluation_service.settings")
    def test_execute_evaluation_success(
        self, mock_settings, mock_get_db_session, mock_client_class
    ):
        """評価実行 - 正常系"""
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"

        # モックDB
        mock_db = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # モックプロンプト
        mock_prompt = MagicMock()
        mock_prompt.content = "評価プロンプト"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_prompt

        # モッククライアント
        mock_client = MagicMock()
        mock_client._generate_content.return_value = (
            "評価結果: 良好です",
            1000,
            500
        )
        mock_client_class.return_value = mock_client

        result = execute_evaluation(
            document_type="他院への紹介",
            input_text="患者情報",
            current_prescription="処方内容",
            additional_info="追加情報",
            output_summary="出力内容"
        )

        assert result.success is True
        assert result.evaluation_result == "評価結果: 良好です"
        assert result.input_tokens == 1000
        assert result.output_tokens == 500
        assert result.processing_time >= 0
        assert result.error_message is None

        mock_client.initialize.assert_called_once()
        mock_client._generate_content.assert_called_once()

    @patch("app.services.evaluation_service.settings")
    def test_execute_evaluation_no_output(self, mock_settings):
        """評価実行 - 出力なしエラー"""
        result = execute_evaluation(
            document_type="他院への紹介",
            input_text="患者情報",
            current_prescription="",
            additional_info="",
            output_summary=""
        )

        assert result.success is False
        assert result.error_message == MESSAGES["EVALUATION_NO_OUTPUT"]
        assert result.input_tokens == 0
        assert result.output_tokens == 0

    @patch("app.services.evaluation_service.settings")
    def test_execute_evaluation_model_missing(self, mock_settings):
        """評価実行 - モデル未設定エラー"""
        mock_settings.gemini_evaluation_model = None

        result = execute_evaluation(
            document_type="他院への紹介",
            input_text="患者情報",
            current_prescription="",
            additional_info="",
            output_summary="出力内容"
        )

        assert result.success is False
        assert result.error_message == MESSAGES["EVALUATION_MODEL_MISSING"]
        assert result.input_tokens == 0
        assert result.output_tokens == 0

    @patch("app.services.evaluation_service.get_db_session")
    @patch("app.services.evaluation_service.settings")
    def test_execute_evaluation_prompt_not_set(
        self, mock_settings, mock_get_db_session
    ):
        """評価実行 - プロンプト未設定エラー"""
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"

        # モックDB
        mock_db = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = execute_evaluation(
            document_type="他院への紹介",
            input_text="患者情報",
            current_prescription="",
            additional_info="",
            output_summary="出力内容"
        )

        assert result.success is False
        assert "他院への紹介" in result.error_message
        assert "評価プロンプトが設定されていません" in result.error_message
        assert result.input_tokens == 0
        assert result.output_tokens == 0

    @patch("app.services.evaluation_service.GeminiAPIClient")
    @patch("app.services.evaluation_service.get_db_session")
    @patch("app.services.evaluation_service.settings")
    def test_execute_evaluation_api_error(
        self, mock_settings, mock_get_db_session, mock_client_class
    ):
        """評価実行 - API呼び出しエラー"""
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"

        # モックDB
        mock_db = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # モックプロンプト
        mock_prompt = MagicMock()
        mock_prompt.content = "評価プロンプト"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_prompt

        # モッククライアントでエラー
        from app.utils.exceptions import APIError

        mock_client = MagicMock()
        mock_client._generate_content.side_effect = APIError("API接続エラー")
        mock_client_class.return_value = mock_client

        result = execute_evaluation(
            document_type="他院への紹介",
            input_text="患者情報",
            current_prescription="",
            additional_info="",
            output_summary="出力内容"
        )

        assert result.success is False
        assert "API接続エラー" in result.error_message
        assert result.input_tokens == 0
        assert result.output_tokens == 0

    @patch("app.services.evaluation_service.GeminiAPIClient")
    @patch("app.services.evaluation_service.get_db_session")
    @patch("app.services.evaluation_service.settings")
    def test_execute_evaluation_general_exception(
        self, mock_settings, mock_get_db_session, mock_client_class
    ):
        """評価実行 - 一般的な例外"""
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"

        # モックDB
        mock_db = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # モックプロンプト
        mock_prompt = MagicMock()
        mock_prompt.content = "評価プロンプト"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_prompt

        # モッククライアントで例外
        mock_client = MagicMock()
        mock_client._generate_content.side_effect = Exception("予期しないエラー")
        mock_client_class.return_value = mock_client

        result = execute_evaluation(
            document_type="他院への紹介",
            input_text="患者情報",
            current_prescription="",
            additional_info="",
            output_summary="出力内容"
        )

        assert result.success is False
        assert "評価中にエラーが発生しました" in result.error_message
        assert "予期しないエラー" in result.error_message
        assert result.input_tokens == 0
        assert result.output_tokens == 0

    @patch("app.services.evaluation_service.GeminiAPIClient")
    @patch("app.services.evaluation_service.get_db_session")
    @patch("app.services.evaluation_service.settings")
    def test_execute_evaluation_with_all_fields(
        self, mock_settings, mock_get_db_session, mock_client_class
    ):
        """評価実行 - 全フィールド指定"""
        mock_settings.gemini_evaluation_model = "gemini-2.0-flash-thinking-exp-01-21"

        # モックDB
        mock_db = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db

        # モックプロンプト
        mock_prompt = MagicMock()
        mock_prompt.content = "詳細な評価プロンプト"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_prompt

        # モッククライアント
        mock_client = MagicMock()
        mock_client._generate_content.return_value = (
            "詳細な評価結果",
            2000,
            1000
        )
        mock_client_class.return_value = mock_client

        result = execute_evaluation(
            document_type="他院への紹介",
            input_text="詳細な患者情報" * 100,
            current_prescription="複数の処方薬",
            additional_info="詳細な追加情報",
            output_summary="詳細な出力内容"
        )

        assert result.success is True
        assert result.evaluation_result == "詳細な評価結果"
        assert result.input_tokens == 2000
        assert result.output_tokens == 1000

        # build_evaluation_prompt が正しく呼ばれたことを確認
        call_args = mock_client._generate_content.call_args[0][0]
        assert "詳細な評価プロンプト" in call_args
        assert "【カルテ記載】" in call_args
        assert "【現在の処方】" in call_args
        assert "【追加情報】" in call_args
        assert "【生成された出力】" in call_args
