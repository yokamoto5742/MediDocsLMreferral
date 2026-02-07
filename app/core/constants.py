from enum import Enum


class ModelType(str, Enum):
    CLAUDE = "Claude"
    GEMINI_PRO = "Gemini_Pro"

# プロンプト管理
DEFAULT_DEPARTMENT = ["default", "眼科"]
DEFAULT_DOCTOR = ["default"]
DEPARTMENT_DOCTORS_MAPPING = {
    "default": ["default"],
    "眼科": ["default", "橋本義弘"],
}
DOCUMENT_TYPES = ["他院への紹介", "紹介元への逆紹介", "返書", "最終返書"]

# 統計情報
DEFAULT_STATISTICS_PERIOD_DAYS = 7

# 出力結果
DEFAULT_SECTION_NAMES = [
    "現在の処方",
    "備考",
]

# app/external/api_factory.py 他
DEFAULT_DOCUMENT_TYPE = "他院への紹介"
# app/external/base_api.py
DEFAULT_SUMMARY_PROMPT = """
以下のカルテ情報を要約してください。これまでの治療内容を記載してください。
"""
# app/utils/text_processor.py
# 【治療経過】: 内容 など(改行含む)
# 治療経過: 内容 など(改行含む)
# 治療経過（行全体がセクション名のみ）
SECTION_DETECTION_PATTERNS = [
    r'^[【\[■●\s]*{section}[】\]\s]*[:：]?\s*(.*)$',
    r'^{section}\s*[:：]?\s*(.*)$',
    r'^{section}\s*$',
]

# 診療情報提供者アプリ固有の設定
DOCUMENT_TYPE_TO_PURPOSE_MAPPING = {
    "他院への紹介": "精査加療依頼",
    "紹介元への逆紹介": "継続治療依頼",
    "返書": "受診報告",
    "最終返書": "治療経過報告",
}

MESSAGES = {
    "AI_DISCLAIMER": "生成AIは不正確な場合があります。回答をカルテでご確認ください。",
    "ANTHROPIC_MODEL_MISSING": "ANTHROPIC_MODELが設定されていません。環境変数を確認してください。",
    "API_CREDENTIALS_MISSING": "Gemini APIの認証情報が設定されていません。環境変数を確認してください。",
    "API_ERROR": "API エラーが発生しました",
    "AWS_CREDENTIALS_MISSING": "AWS認証情報が設定されていません。環境変数を確認してください。",
    "BEDROCK_API_ERROR": "Amazon Bedrock Claude API呼び出しエラー: {error}",
    "BEDROCK_INIT_ERROR": "Amazon Bedrock Claude API初期化エラー: {error}",
    "CLAUDE_API_CREDENTIALS_MISSING": "Claude APIの認証情報が設定されていません。環境変数を確認してください。",
    "CLOUDFLARE_GATEWAY_API_ERROR": "Cloudflare AI Gateway経由のAPI呼び出しエラー: {error}",
    "CLOUDFLARE_GATEWAY_SETTINGS_MISSING": "Cloudflare AI Gatewayの設定が不完全です。環境変数を確認してください",
    "EMPTY_RESPONSE": "レスポンスが空です",
    "EVALUATION_API_ERROR": "評価中にエラーが発生しました: {error}",
    "EVALUATION_MODEL_MISSING": "GEMINI_EVALUATION_MODEL環境変数が設定されていません",
    "EVALUATION_NO_OUTPUT": "評価対象の出力がありません",
    "EVALUATION_PROMPT_CREATED": "評価プロンプトを新規作成しました",
    "EVALUATION_PROMPT_DELETED": "評価プロンプトを削除しました",
    "EVALUATION_PROMPT_NOT_SET": "{document_type}の評価プロンプトが設定されていません",
    "EVALUATION_PROMPT_UPDATED": "評価プロンプトを更新しました",
    "FIELD_REQUIRED": "すべての項目を入力してください",
    "GENERATING": "作成中...",
    "GOOGLE_LOCATION_MISSING": "GOOGLE_LOCATION環境変数が設定されていません。",
    "GOOGLE_PROJECT_ID_MISSING": "GOOGLE_PROJECT_ID環境変数が設定されていません。",
    "INPUT_TOO_LONG": "入力テキストが長すぎます",
    "INPUT_TOO_SHORT": "入力文字数が少なすぎます",
    "MODEL_SWITCHED": "入力が長いため、モデルを {} に自動切替しました",
    "NO_API_CREDENTIALS": "使用可能なAI APIの認証情報が設定されていません。環境変数を確認してください。",
    "NO_DATA_FOUND": "指定期間のデータがありません",
    "NO_INPUT": "カルテ情報を入力してください",
    "PROCESSING_TIME": "作成時間",
    "PROMPT_CREATED": "プロンプトを新規作成しました",
    "PROMPT_DELETED": "プロンプトを削除しました",
    "PROMPT_UPDATED": "プロンプトを更新しました",
    "TOKEN_THRESHOLD_EXCEEDED": "入力テキストが長いため{original_model} から Gemini_Pro に切り替えます",
    "TOKEN_THRESHOLD_EXCEEDED_NO_GEMINI": "Gemini APIの認証情報が設定されていないため処理できません。",
    "VERTEX_AI_API_ERROR": "Vertex AI API呼び出しエラー: {error}",
    "VERTEX_AI_CREDENTIALS_ERROR": "認証情報の処理中にエラーが発生しました: {error}",
    "VERTEX_AI_CREDENTIALS_FIELD_MISSING": "認証情報に必要なフィールドがありません: {error}",
    "VERTEX_AI_CREDENTIALS_JSON_PARSE_ERROR": "認証情報JSONのパースに失敗しました: {error}",
    "VERTEX_AI_INIT_ERROR": "Vertex AI初期化エラー: {error}",
    "VERTEX_AI_PROJECT_MISSING": "GOOGLE_PROJECT_ID環境変数が設定されていません",
}
