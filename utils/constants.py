import os

from utils.config import APP_TYPE

DEFAULT_DEPARTMENT = ["default", "眼科"]
DEFAULT_DOCTOR = ["default"]

DEPARTMENT_DOCTORS_MAPPING = {
    "default": ["default", "医師共通"],
    "眼科": ["default", "橋本義弘"],
}

DEFAULT_DOCUMENT_TYPE = "診療情報提供書"
DOCUMENT_TYPES = ["他院への紹介", "紹介元への逆紹介", "返書", "最終返書"]
DOCUMENT_TYPE_OPTIONS = ["すべて", "他院への紹介", "紹介元への逆紹介", "返書", "最終返書"]

DOCUMENT_TYPE_TO_PURPOSE_MAPPING = {
    "他院への紹介": "精査加療依頼",
    "紹介元への逆紹介": "継続治療依頼",
    "返書": "受診報告",
    "最終返書": "治療経過報告",
}

DEFAULT_SECTION_NAMES = [
    "【主病名】",
    "【紹介目的】",
    "【既往歴】",
    "【症状経過】",
    "【治療経過】",
    "【現在の処方】",
    "【備考】"
]

TAB_NAMES = {
    "ALL": "全文",
    "MAIN_DISEASE": "【主病名】",
    "PURPOSE": "【紹介目的】",
    "HISTORY": "【既往歴】",
    "SYMPTOMS": "【症状経過】",
    "TREATMENT": "【治療経過】",
    "PRESCRIPTION": "【現在の処方】",
    "NOTE": "【備考】"
}

MESSAGES = {
    "PROMPT_UPDATED": "プロンプトを更新しました",
    "PROMPT_CREATED": "プロンプトを新規作成しました",
    "PROMPT_DELETED": "プロンプトを削除しました",

    "NO_DATA_FOUND": "指定期間のデータがありません",

    "FIELD_REQUIRED": "すべての項目を入力してください",
    "NO_INPUT": "⚠️ カルテ情報を入力してください",
    "INPUT_TOO_SHORT": "⚠️ 入力テキストが短すぎます",
    "INPUT_TOO_LONG": "⚠️ 入力テキストが長すぎます",
    "TOKEN_THRESHOLD_EXCEEDED": "⚠️ 入力テキストが長いため{original_model} から Gemini_Pro に切り替えます",
    "TOKEN_THRESHOLD_EXCEEDED_NO_GEMINI": "⚠️ Gemini APIの認証情報が設定されていないため処理できません。",

    # API認証関連のメッセージ
    "API_CREDENTIALS_MISSING": "⚠️ Gemini APIの認証情報が設定されていません。環境変数を確認してください。",
    "CLAUDE_API_CREDENTIALS_MISSING": "⚠️ Claude APIの認証情報が設定されていません。環境変数を確認してください。",
    "NO_API_CREDENTIALS": "⚠️ 使用可能なAI APIの認証情報が設定されていません。環境変数を確認してください。",
    "AWS_CREDENTIALS_MISSING": "⚠️ AWS認証情報が設定されていません。環境変数を確認してください。",
    "ANTHROPIC_MODEL_MISSING": "⚠️ ANTHROPIC_MODELが設定されていません。環境変数を確認してください。",
    "BEDROCK_INIT_ERROR": "Amazon Bedrock Claude API初期化エラー: {error}",
    "BEDROCK_API_ERROR": "Amazon Bedrock Claude API呼び出しエラー: {error}",

    # Vertex AI関連のエラーメッセージ
    "GOOGLE_PROJECT_ID_MISSING": "⚠️ GOOGLE_PROJECT_ID環境変数が設定されていません。",
    "GOOGLE_LOCATION_MISSING": "⚠️ GOOGLE_LOCATION環境変数が設定されていません。",
    "VERTEX_AI_INIT_ERROR": "Vertex AI初期化エラー: {error}",
    "VERTEX_AI_API_ERROR": "Vertex AI API呼び出しエラー: {error}",

    "EMPTY_RESPONSE": "レスポンスが空です",

    "COPY_INSTRUCTION": "💡 テキストエリアの右上にマウスを合わせて左クリックでコピーできます",
    "PROCESSING_TIME": "⏱️ 処理時間: {processing_time:.0f}秒",
}