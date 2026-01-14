"""一時的な互換レイヤー - 旧utils.configのインターフェースを提供"""

from app.core.config import get_settings


def get_config() -> dict:
    """旧形式のconfig辞書を返す互換関数"""
    settings = get_settings()

    # デフォルトプロンプトテンプレート
    default_summary_prompt = """以下のカルテ情報を基に、診療情報提供書の内容を生成してください。

【主傷病名及び主要症状】
患者の主な診断名と症状を簡潔に記載してください。

【既往歴】
関連する既往歴を記載してください。

【症状経過】
現在までの症状の経過を時系列で記載してください。

【治療経過】
これまでに行った検査や治療の内容を記載してください。

【現在の処方】
現在の処方内容を記載してください（処方情報が提供されている場合）。

【紹介目的】
紹介の目的を記載してください（紹介目的が提供されている場合）。"""

    return {
        "PROMPTS": {
            "summary": default_summary_prompt
        }
    }
