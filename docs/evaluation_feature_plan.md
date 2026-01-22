# 出力評価機能 実装計画

## 概要
出力評価機能と評価プロンプト管理画面を追加する

## 1. データベース層

### 1.1 新規: `app/models/evaluation_prompt.py`
```python
class EvaluationPrompt(Base):
    __tablename__ = "evaluation_prompts"

    id = Column(Integer, primary_key=True)
    document_type = Column(String(100), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 1.2 新規: Alembicマイグレーション
- `evaluation_prompts`テーブル作成

### 1.3 修正: `app/models/__init__.py`
- `EvaluationPrompt`をエクスポート

## 2. 設定層

### 2.1 修正: `app/core/config.py`
```python
gemini_evaluation_model: str | None = None  # 追加
```

### 2.2 修正: `app/core/constants.py`
評価関連メッセージを追加

## 3. External API層

### 3.1 修正: `app/external/gemini_evaluation.py`
- `get_settings()`から設定値を取得するよう修正

## 4. スキーマ層

### 4.1 新規: `app/schemas/evaluation.py`
- `EvaluationRequest` - 評価リクエスト
- `EvaluationResponse` - 評価レスポンス
- `EvaluationPromptRequest` - プロンプト保存リクエスト
- `EvaluationPromptResponse` - プロンプトレスポンス

## 5. サービス層

### 5.1 新規: `app/services/evaluation_service.py`
- `get_evaluation_prompt()` - プロンプト取得
- `get_all_evaluation_prompts()` - 全プロンプト取得
- `create_or_update_evaluation_prompt()` - プロンプト保存
- `delete_evaluation_prompt()` - プロンプト削除
- `build_evaluation_prompt()` - フルプロンプト構築
- `execute_evaluation()` - 評価実行

## 6. API層

### 6.1 新規: `app/api/evaluation.py`
```
POST /evaluation/evaluate          - 出力評価実行
GET  /evaluation/prompts           - 全評価プロンプト取得
GET  /evaluation/prompts/{doc_type} - 評価プロンプト取得
POST /evaluation/prompts           - 評価プロンプト保存
DELETE /evaluation/prompts/{doc_type} - 評価プロンプト削除
```

### 6.2 修正: `app/api/router.py`
- `evaluation`ルーターを追加

## 7. ページ層 (main.py)

### 7.1 修正: `app/main.py`
```python
GET /evaluation-prompts                    - 評価プロンプト管理ページ
GET /evaluation-prompts/edit/{doc_type}    - 評価プロンプト編集ページ
```

## 8. テンプレート層

### 8.1 修正: `app/templates/prompts.html`
「新規プロンプト作成」ボタンの右に「評価プロンプト」ボタン追加

### 8.2 新規: `app/templates/evaluation_prompts.html`
- 文書タイプごとの評価プロンプト一覧
- 各行に「編集」ボタン
- 「プロンプト管理に戻る」ボタン

### 8.3 新規: `app/templates/evaluation_prompts_edit.html`
- 評価プロンプト編集フォーム
- 保存ボタン、キャンセルボタン

### 8.4 修正: `app/templates/index.html`
**出力画面:**
- 「出力評価」ボタン追加（コピーとクリアして戻るの間）
- 評価中のローディング表示

**新規: 評価結果画面 (`currentScreen === 'evaluation'`):**
- コピーボタン
- 出力結果に戻るボタン
- 評価結果表示（出力画面と同じレイアウト）

### 8.5 修正: `app/static/js/app.js`
```javascript
// State追加
evaluationResult: { result: '', processingTime: null },
isEvaluating: false,
evaluationElapsedTime: 0,

// 関数追加
async evaluateOutput() { ... }
backToOutput() { ... }
```

## 9. 画面フロー

```
[入力画面]
    ↓ 作成ボタン
[出力結果画面]
    - コピーボタン
    - 出力評価ボタン → [出力評価画面]
    - クリアして戻るボタン → [入力画面]

[出力評価画面]
    - コピーボタン
    - 出力結果に戻るボタン → [出力結果画面]

[プロンプト管理画面]
    - 新規プロンプト作成ボタン → 新規作成画面
    - 評価プロンプトボタン → [評価プロンプト管理画面]

[評価プロンプト管理画面]
    - プロンプト管理に戻るボタン → プロンプト管理画面
    - 編集ボタン → [評価プロンプト編集画面]
```

## 10. ファイル変更一覧

| 操作 | ファイル |
|------|----------|
| 新規 | `app/models/evaluation_prompt.py` |
| 新規 | `alembic/versions/xxx_create_evaluation_prompts.py` |
| 新規 | `app/schemas/evaluation.py` |
| 新規 | `app/services/evaluation_service.py` |
| 新規 | `app/api/evaluation.py` |
| 新規 | `app/templates/evaluation_prompts.html` |
| 新規 | `app/templates/evaluation_prompts_edit.html` |
| 修正 | `app/models/__init__.py` |
| 修正 | `app/core/config.py` |
| 修正 | `app/core/constants.py` |
| 修正 | `app/external/gemini_evaluation.py` |
| 修正 | `app/api/router.py` |
| 修正 | `app/main.py` |
| 修正 | `app/templates/prompts.html` |
| 修正 | `app/templates/index.html` |
| 修正 | `app/static/js/app.js` |

## 11. 実装順序

1. **データベース層**: モデル → マイグレーション
2. **設定層**: config.py → constants.py
3. **External API**: gemini_evaluation.py修正
4. **スキーマ層**: evaluation.py
5. **サービス層**: evaluation_service.py
6. **API層**: evaluation.py → router.py
7. **ページ層**: main.py
8. **テンプレート層**:
   - prompts.html（ボタン追加）
   - evaluation_prompts.html（新規）
   - evaluation_prompts_edit.html（新規）
   - index.html（評価機能追加）
   - app.js（評価機能追加）
