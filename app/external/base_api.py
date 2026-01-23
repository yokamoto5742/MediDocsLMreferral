from abc import ABC, abstractmethod
from typing import Optional, Tuple, cast

from app.core.constants import DEFAULT_DOCUMENT_TYPE, DEFAULT_SUMMARY_PROMPT
from app.core.database import get_db_session
from app.services import prompt_service
from app.utils.exceptions import APIError


class BaseAPIClient(ABC):
    def __init__(self, api_key: str | None, default_model: str | None):
        self.api_key: str | None = api_key
        self.default_model: str | None = default_model

    @abstractmethod
    def initialize(self) -> bool:
        """APIクライアントを初期化します。成功時はTrueを返し、失敗時は例外を投げます。"""
        pass

    @abstractmethod
    def _generate_content(self, prompt: str, model_name: str) -> Tuple[str, int, int]:
        """
        プロンプトから要約を生成します。
        Args:
            prompt: 生成用プロンプト
            model_name: 使用するモデル名
        Returns:
            Tuple[str, int, int]: (生成された要約, 入力トークン数, 出力トークン数)
        Raises:
            APIError: API呼び出しに失敗した場合
        """
        pass

    def create_summary_prompt(
        self,
        medical_text: str,
        additional_info: str = "",
        referral_purpose: str = "",
        current_prescription: str = "",
        department: str = "default",
        document_type: str = DEFAULT_DOCUMENT_TYPE,
        doctor: str = "default",
    ) -> str:
        try:
            with get_db_session() as db:
                prompt_data = prompt_service.get_prompt(db, department, document_type, doctor)
                if prompt_data:
                    prompt_template = prompt_data.content
                else:
                    prompt_template = DEFAULT_SUMMARY_PROMPT
        except Exception:
            prompt_template = DEFAULT_SUMMARY_PROMPT

        prompt = f"{prompt_template}\n【カルテ情報】\n{medical_text}"

        if referral_purpose.strip():
            prompt += f"\n【紹介目的】\n{referral_purpose}"

        if current_prescription.strip():
            prompt += f"\n【現在の処方】\n{current_prescription}"

        prompt += f"\n【追加情報】{additional_info}"

        return prompt

    def get_model_name(
        self, department: str, document_type: str, doctor: str
    ) -> str | None:
        try:
            with get_db_session() as db:
                prompt_data = prompt_service.get_prompt(db, department, document_type, doctor)
                if prompt_data:
                    selected = prompt_data.selected_model
                    if selected is not None:
                        return cast(str, selected)
        except Exception:
            pass
        return self.default_model

    def generate_summary(
        self,
        medical_text: str,
        additional_info: str = "",
        referral_purpose: str = "",
        current_prescription: str = "",
        department: str = "default",
        document_type: str = DEFAULT_DOCUMENT_TYPE,
        doctor: str = "default",
        model_name: Optional[str] = None,
    ) -> Tuple[str, int, int]:
        try:
            self.initialize()

            if not model_name:
                model_name = self.get_model_name(department, document_type, doctor)

            if not model_name:
                raise APIError("モデル名が指定されていません")

            prompt = self.create_summary_prompt(
                medical_text,
                additional_info,
                referral_purpose,
                current_prescription,
                department,
                document_type,
                doctor,
            )

            return self._generate_content(prompt, model_name)

        except APIError as e:
            raise e
        except Exception as e:
            raise APIError(
                f"{self.__class__.__name__}でエラーが発生しました: {str(e)}"
            )
