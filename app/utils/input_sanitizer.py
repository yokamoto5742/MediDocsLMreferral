import re


def sanitize_medical_text(text: str) -> str:
    """
    医療テキストのサニタイゼーション

    XSS対策とプロンプトインジェクション軽減のため入力を整形
    医療情報の可読性を保ちつつ危険なパターンを除去
    """
    if not text:
        return text

    # スクリプトタグの完全除去
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # イベントハンドラ属性の除去
    text = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)

    # 制御文字の除去（改行とタブは保持）
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    return text


def sanitize_prompt_text(text: str) -> str:
    """
    プロンプトテキストのサニタイゼーション

    医師が設定するプロンプトに対する基本的な整形
    """
    if not text:
        return text

    return sanitize_medical_text(text)
