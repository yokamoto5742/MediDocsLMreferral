import json
import os
from typing import Tuple

from google import genai
from google.genai import types
from google.oauth2 import service_account

from app.core.config import get_settings
from app.core.constants import MESSAGES
from app.external.base_api import BaseAPIClient
from app.utils.exceptions import APIError

settings = get_settings()


class GeminiAPIClient(BaseAPIClient):
    def __init__(self):
        super().__init__(None, settings.gemini_model)
        self.client = None

    def initialize(self) -> bool:
        try:
            if not settings.google_project_id:
                raise APIError(MESSAGES["GOOGLE_PROJECT_ID_MISSING"])

            google_credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")

            if google_credentials_json:
                try:
                    credentials_dict = json.loads(google_credentials_json)

                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_dict,
                        scopes=["https://www.googleapis.com/auth/cloud-platform"],
                    )

                    self.client = genai.Client(
                        vertexai=True,
                        project=settings.google_project_id,
                        location=settings.google_location,
                        credentials=credentials,
                    )

                    print(
                        f"Vertex AI Client initialized successfully for project: {settings.google_project_id}"
                    )

                except json.JSONDecodeError as e:
                    raise APIError(f"GOOGLE_CREDENTIALS_JSON環境変数の解析エラー: {str(e)}")
                except KeyError as e:
                    raise APIError(f"認証情報に必要なフィールドが不足: {str(e)}")
                except Exception as e:
                    raise APIError(f"認証情報の作成エラー: {str(e)}")
            else:
                self.client = genai.Client(
                    vertexai=True,
                    project=settings.google_project_id,
                    location=settings.google_location,
                )

            return True
        except APIError:
            raise
        except Exception as e:
            raise APIError(MESSAGES["VERTEX_AI_INIT_ERROR"].format(error=str(e)))

    def _generate_content(self, prompt: str, model_name: str) -> Tuple[str, int, int]:
        try:
            if not self.client:
                raise APIError("Clientが初期化されていません")

            thinking_level = (
                types.ThinkingLevel.LOW
                if settings.gemini_thinking_level == "LOW"
                else types.ThinkingLevel.HIGH
            )
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level=thinking_level)
                ),
            )

            if hasattr(response, "text"):
                summary_text = response.text or MESSAGES["EMPTY_RESPONSE"]
            else:
                summary_text = str(response)

            input_tokens = 0
            output_tokens = 0

            if hasattr(response, "usage_metadata"):
                usage_metadata = response.usage_metadata
                if usage_metadata:
                    input_tokens = usage_metadata.prompt_token_count or 0
                    output_tokens = usage_metadata.candidates_token_count or 0

            return summary_text, input_tokens, output_tokens
        except Exception as e:
            raise APIError(MESSAGES["VERTEX_AI_API_ERROR"].format(error=str(e)))
