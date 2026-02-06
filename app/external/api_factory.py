import logging
from enum import Enum
from typing import Union

from app.core.config import get_settings
from app.core.constants import DEFAULT_DOCUMENT_TYPE
from app.external.base_api import BaseAPIClient
from app.external.claude_api import ClaudeAPIClient
from app.external.cloudflare_gemini_api import CloudflareGeminiAPIClient
from app.external.gemini_api import GeminiAPIClient
from app.utils.exceptions import APIError

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"


class APIFactory:
    @staticmethod
    def create_client(provider: Union[APIProvider, str]) -> BaseAPIClient:
        if isinstance(provider, str):
            try:
                provider = APIProvider(provider.lower())
            except ValueError:
                raise APIError(f"未対応のAPIプロバイダー: {provider}")

        if provider == APIProvider.GEMINI:
            settings = get_settings()
            if all([
                settings.cloudflare_account_id,
                settings.cloudflare_gateway_id,
                settings.cloudflare_aig_token,
            ]):
                logger.info("APIクライアント選択: CloudflareGeminiAPIClient (Cloudflare AI Gateway経由)")
                return CloudflareGeminiAPIClient()
            logger.info("APIクライアント選択: GeminiAPIClient (Direct Vertex AI)")
            return GeminiAPIClient()

        client_mapping = {
            APIProvider.CLAUDE: ClaudeAPIClient,
        }

        if provider in client_mapping:
            logger.info("APIクライアント選択: ClaudeAPIClient")
            return client_mapping[provider]()
        else:
            logger.error(f"未対応のAPIプロバイダー: {provider}")
            raise APIError(f"未対応のAPIプロバイダー: {provider}")

    @staticmethod
    def generate_summary_with_provider(
        provider: Union[APIProvider, str],
        medical_text: str,
        additional_info: str = "",
        referral_purpose: str = "",
        current_prescription: str = "",
        department: str = "default",
        document_type: str = DEFAULT_DOCUMENT_TYPE,
        doctor: str = "default",
        model_name: str | None = None,
    ):
        client = APIFactory.create_client(provider)
        return client.generate_summary(
            medical_text,
            additional_info,
            referral_purpose,
            current_prescription,
            department,
            document_type,
            doctor,
            model_name,
        )


    @staticmethod
    def generate_summary_stream_with_provider(
        provider: Union[APIProvider, str],
        medical_text: str,
        additional_info: str = "",
        referral_purpose: str = "",
        current_prescription: str = "",
        department: str = "default",
        document_type: str = DEFAULT_DOCUMENT_TYPE,
        doctor: str = "default",
        model_name: str | None = None,
    ):
        client = APIFactory.create_client(provider)
        return client.generate_summary_stream(
            medical_text,
            additional_info,
            referral_purpose,
            current_prescription,
            department,
            document_type,
            doctor,
            model_name,
        )


def generate_summary(provider: str, medical_text: str, **kwargs):
    return APIFactory.generate_summary_with_provider(provider, medical_text, **kwargs)


def generate_summary_stream(provider: str, medical_text: str, **kwargs):
    return APIFactory.generate_summary_stream_with_provider(provider, medical_text, **kwargs)
