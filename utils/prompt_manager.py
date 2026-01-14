"""一時的な互換レイヤー - 旧utils.prompt_managerのインターフェースを提供"""

from typing import Optional

from app.core.database import get_db_session
from app.services import prompt_service


def get_prompt(
    department: str,
    document_type: str,
    doctor: str,
) -> Optional[dict]:
    """
    旧形式のプロンプト辞書を返す互換関数

    Returns:
        プロンプトが見つかった場合は辞書、見つからない場合はNone
        辞書形式: {"content": str, "selected_model": str}
    """
    try:
        with get_db_session() as db:
            prompt = prompt_service.get_prompt(
                db=db,
                department=department,
                document_type=document_type,
                doctor=doctor,
            )

            if prompt is None:
                return None

            return {
                "content": prompt.content,
                "selected_model": getattr(prompt, "model", None),
            }
    except Exception:
        # データベースエラーの場合はNoneを返す
        return None
