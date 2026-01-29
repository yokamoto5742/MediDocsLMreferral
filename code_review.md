# コードレビュー - MediDocsLMreferral

## 概要

可読性・メンテナンス性・KISSの原則に基づきコードをレビューした結果を優先度順に記載する

---

## 優先度: 高

### 1. エラーレスポンス構築の重複（DRY原則違反）

**ファイル**: `app/services/summary_service.py:82-197`

`execute_summary_generation`関数内で同一構造の`SummaryResponse`エラーレスポンスを4回繰り返している

**現状**:
```python
return SummaryResponse(
    success=False,
    output_summary="",
    parsed_summary={},
    input_tokens=0,
    output_tokens=0,
    processing_time=0,
    model_used=model,
    model_switched=False,
    error_message=error_msg,
)
```

**改善案**: ヘルパー関数の導入
```python
def _error_response(error_msg: str, model: str, model_switched: bool = False) -> SummaryResponse:
    return SummaryResponse(
        success=False,
        output_summary="",
        parsed_summary={},
        input_tokens=0,
        output_tokens=0,
        processing_time=0,
        model_used=model,
        model_switched=model_switched,
        error_message=error_msg,
    )
```

---

### 2. モデル名取得ロジックの重複

**ファイル**:
- `app/services/summary_service.py:30-63` (`determine_model`)
- `app/external/base_api.py:65-80` (`get_model_name`)

同一のDB呼び出しでプロンプトからモデル名を取得するロジックが2箇所に存在

**改善案**: `prompt_service`に`get_selected_model`関数を追加し、ロジックを集約
```python
# app/services/prompt_service.py
def get_selected_model(
    db: Session, department: str, document_type: str, doctor: str
) -> str | None:
    prompt = get_prompt(db, department, document_type, doctor)
    if prompt and prompt.selected_model:
        return str(prompt.selected_model)
    return None
```

---

### 3. マジックストリングの散在

**ファイル**: 複数箇所

"Claude", "Gemini_Pro", "claude", "gemini" などの文字列リテラルが以下に分散:
- `app/services/summary_service.py:56, 66-76`
- `app/external/api_factory.py:9-13`
- `app/schemas/summary.py:11`

**改善案**: 既存の`APIProvider` Enumを拡張して統一的に使用
```python
# app/core/constants.py
class ModelType(Enum):
    CLAUDE = "Claude"
    GEMINI_PRO = "Gemini_Pro"

# プロバイダーとの対応表
MODEL_PROVIDER_MAPPING = {
    ModelType.CLAUDE: APIProvider.CLAUDE,
    ModelType.GEMINI_PRO: APIProvider.GEMINI,
}
```

---

### 4. 関数内インポートによるコードの不明瞭化

**ファイル**: `app/services/summary_service.py:42-44`

```python
def determine_model(...):
    if not model_explicitly_selected:
        try:
            from app.core.database import get_db_session  # 関数内インポート
            from app.services import prompt_service       # 関数内インポート
```

循環インポート回避のためと推測されるが、設計上の問題を示唆

**改善案**:
- モジュール構造を見直し、循環参照を解消
- または、関数のパラメータとしてDBセッションを受け取る設計に変更

---

## 優先度: 中

### 5. APIレスポンスの冗長な再構築

**ファイル**: `app/api/summary.py:10-34`

`execute_summary_generation`が既に`SummaryResponse`を返すのに、APIエンドポイントで再度構築している

**現状**:
```python
def generate_summary(request: SummaryRequest):
    result = execute_summary_generation(...)
    return SummaryResponse(
        success=result.success,
        output_summary=result.output_summary,
        # ... すべてのフィールドを手動でコピー
    )
```

**改善案**: 直接返却
```python
def generate_summary(request: SummaryRequest):
    return execute_summary_generation(
        medical_text=request.medical_text,
        ...
    )
```

---

### 6. 型ヒントの欠落

**ファイル**: `app/utils/text_processor.py`

```python
def format_output_summary(summary_text):  # 型ヒントなし
def parse_output_summary(summary_text):   # 型ヒントなし
```

**改善案**:
```python
def format_output_summary(summary_text: str) -> str:
def parse_output_summary(summary_text: str) -> dict[str, str]:
```

---

### 7. ClaudeAPIClientとGeminiAPIClientの設定取得方法の不一致

**ファイル**:
- `app/external/claude_api.py:16-19` - `os.getenv`を直接使用
- `app/external/gemini_api.py:17` - `get_settings()`を使用

**現状** (ClaudeAPIClient):
```python
self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
```

**改善案**: `Settings`クラスを統一的に使用
```python
def __init__(self):
    settings = get_settings()
    self.aws_access_key_id = settings.aws_access_key_id
    self.aws_secret_access_key = settings.aws_secret_access_key
```

---

### 8. 例外処理パターンの不統一

**現状**:
- 一部は`APIError`を発生
- 一部は`ValueError`を発生
- 一部はエラーメッセージ文字列を返却

**改善案**:
- サービス層では常にドメイン固有の例外を使用
- API層でHTTP例外に変換

---

## 優先度: 低

### 9. parse_output_summaryのネスト深度

**ファイル**: `app/utils/text_processor.py:23-73`

4重ネストのループ構造で可読性が低い

**改善案**: セクション検出ロジックを関数に抽出
```python
def _detect_section(line: str, sections: list[str]) -> tuple[str | None, str]:
    """セクション名と残りのコンテンツを検出"""
    ...

def parse_output_summary(summary_text: str) -> dict[str, str]:
    sections = {section: "" for section in DEFAULT_SECTION_NAMES}
    current_section = None

    for line in summary_text.split('\n'):
        line = line.strip()
        if not line:
            continue

        detected, content = _detect_section(line, list(sections.keys()) + list(section_aliases.keys()))
        if detected:
            current_section = section_aliases.get(detected, detected)
            if content:
                sections[current_section] = content
        elif current_section:
            sections[current_section] += ("\n" if sections[current_section] else "") + line

    return sections
```

---

### 10. ログ出力の一貫性不足

**現状**:
- `save_usage`では`logging.error`を使用
- 他の関数では例外を投げるのみ

**改善案**: ロギング方針を統一
- エラーは必ずログ出力
- ビジネスロジックエラーは例外として伝播

---

### 11. SummaryUsageモデルのカラム名不整合

**ファイル**: `app/models/usage.py:12-13`

```python
document_type = Column("document_types", String(100))  # 単数形と複数形の混在
model = Column("model_detail", String(100))            # 属性名とカラム名の乖離
```

カラム名が実際の属性名と異なり、混乱の原因になる

---

## 全体評価

| 項目 | 評価 |
|------|------|
| ディレクトリ構成 | 良好 - 責任分離が明確 |
| 型ヒント | 概ね良好 - 一部欠落あり |
| エラーハンドリング | 要改善 - パターンの統一が必要 |
| DRY原則 | 要改善 - 重複ロジックあり |
| 可読性 | 良好 - 関数サイズは適切 |
| テストカバレッジ | 良好 - 120+テストケース |

---

## 推奨する対応順序

1. エラーレスポンスヘルパー関数の導入（影響範囲が限定的）
2. マジックストリングのEnum化（一貫性向上）
3. APIレスポンスの冗長構築を削除（シンプルな修正）
4. 型ヒントの追加（静的解析の恩恵）
5. モデル名取得ロジックの集約（設計改善）
