# Streamlit → FastAPI + HTMX 移行計画

## 概要

現在のStreamlitベースのアプリケーションを、FastAPI + HTMX + Alpine.jsのシングルアプリケーションに移行する計画です。

**現状分析**: `app/`ディレクトリに既にFastAPI + HTMX + Alpine.jsの基盤実装が存在しています。本計画は残りの作業を完了させ、旧コードを整理することを目的とします。

---

## Phase 1: 現状確認と検証

### Step 1.1: 既存FastAPI実装の動作確認

```bash
# FastAPIサーバー起動
uvicorn app.main:app --reload --port 8000
```

確認項目:
- [ ] メインページ (`/`) の表示
- [ ] プロンプト管理ページ (`/prompts`) の表示
- [ ] 統計ページ (`/statistics`) の表示
- [ ] API ドキュメント (`/api/docs`) の表示

### Step 1.2: API エンドポイントのテスト

| エンドポイント | メソッド | 確認項目 |
|--------------|---------|---------|
| `/api/summary/generate` | POST | 要約生成 |
| `/api/summary/models` | GET | 利用可能モデル取得 |
| `/api/prompts/` | GET | プロンプト一覧取得 |
| `/api/prompts/` | POST | プロンプト作成 |
| `/api/prompts/{id}` | DELETE | プロンプト削除 |
| `/api/statistics/summary` | GET | 統計サマリー取得 |
| `/api/statistics/records` | GET | 使用履歴取得 |
| `/api/settings/departments` | GET | 診療科一覧 |
| `/api/settings/doctors/{dept}` | GET | 医師一覧 |
| `/api/settings/document-types` | GET | 文書タイプ一覧 |

### Step 1.3: データベース接続確認

```bash
# テスト実行
python -m pytest tests/ -v --tb=short
```

---

## Phase 2: 機能完成と改善

### Step 2.1: HTMXによるリアルタイム更新の強化

**対象ファイル**: `app/templates/index.html`

現状はAlpine.jsでfetchを使用しているが、以下をHTMXに置き換えることを検討:

```html
<!-- 現在の実装 (Alpine.js) -->
<button @click="generateSummary()">作成</button>

<!-- HTMXへの移行案 -->
<button hx-post="/api/summary/generate"
        hx-target="#result"
        hx-indicator="#loading">
    作成
</button>
```

**判断ポイント**:
- Option A: 現状のAlpine.js実装を維持（動作していれば変更不要）
- Option B: HTMXに完全移行（サーバーサイドレンダリングを活用）

### Step 2.2: エラーハンドリングの統一

**対象ファイル**: `app/utils/error_handlers.py`

```python
# FastAPI例外ハンドラーの追加
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"success": False, "error_message": str(exc)}
    )
```

### Step 2.3: サイドバーの医師リスト動的更新

**対象ファイル**: `app/templates/components/sidebar.html`

HTMXを使用した動的更新:

```html
<select hx-get="/api/settings/doctors/{department}"
        hx-trigger="change from:#department-select"
        hx-target="this"
        hx-swap="innerHTML">
</select>
```

---

## Phase 3: テストの拡充

### Step 3.1: 既存テストの確認と修正

```bash
# 現在のテスト構造
tests/
├── api/
│   ├── test_prompts.py
│   └── test_statistics.py
├── services/
│   ├── test_prompt_service.py
│   └── test_statistics_service.py
└── app/
    └── conftest.py
```

### Step 3.2: 追加テストの作成

| テストファイル | 対象 | 優先度 |
|--------------|------|-------|
| `tests/api/test_summary.py` | 要約生成API | 高 |
| `tests/api/test_settings.py` | 設定API | 中 |
| `tests/services/test_summary_service.py` | 要約サービス | 高 |
| `tests/external/test_api_factory.py` | API Factory | 中 |

### Step 3.3: E2Eテストの追加（オプション）

```bash
pip install playwright pytest-playwright
```

```python
# tests/e2e/test_main_flow.py
async def test_summary_generation(page):
    await page.goto("http://localhost:8000")
    await page.fill('[x-model="form.medicalText"]', "テスト入力")
    await page.click('button[type="submit"]')
    await page.wait_for_selector('[x-show="result.outputSummary"]')
```

---

## Phase 4: 旧Streamlitコードの削除

### Step 4.1: 削除対象ファイルの特定

```
削除対象:
├── views/
│   ├── __init__.py
│   ├── main_page.py
│   ├── prompt_management_page.py
│   └── statistics_page.py
├── ui_components/
│   ├── __init__.py
│   └── navigation.py
```

### Step 4.2: 依存関係の確認

```bash
# 旧コードへの参照がないことを確認
grep -r "from views" app/
grep -r "from ui_components" app/
grep -r "import streamlit" app/
```

### Step 4.3: 削除の実行

```bash
# バックアップを取ってから削除
git add -A
git commit -m "Backup before removing Streamlit code"

# 削除
rm -rf views/
rm -rf ui_components/
```

### Step 4.4: requirements.txtの整理

**削除候補パッケージ** (Streamlit関連):
- streamlit（未インストールの場合は不要）
- altair（使用していない場合）
- pydeck（使用していない場合）
- pillow（使用していない場合）

```bash
# 使用パッケージの確認
pip check
pipdeptree
```

---

## Phase 5: デプロイ設定の更新

### Step 5.1: Procfileの更新

```procfile
# 現在 (Streamlit用の場合)
web: streamlit run app.py

# 更新後 (FastAPI用)
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 5.2: 環境変数の確認

必須環境変数:
```env
# データベース
DATABASE_URL=postgresql://...

# AI API (少なくとも1つ必要)
CLAUDE_API_KEY=...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# または
GOOGLE_CREDENTIALS_JSON=...
GOOGLE_PROJECT_ID=...
GOOGLE_LOCATION=asia-northeast1
GEMINI_MODEL=gemini-1.5-pro
```

### Step 5.3: Docker対応（オプション）

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: medidocs
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## Phase 6: ドキュメントの更新

### Step 6.1: CLAUDE.mdの更新

```markdown
## Development Commands

### Running the Application
# 変更前
streamlit run app.py

# 変更後
uvicorn app.main:app --reload --port 8000
```

### Step 6.2: README.mdの更新（docs/配下）

更新項目:
- [ ] インストール手順
- [ ] 起動コマンド
- [ ] API仕様
- [ ] 環境変数一覧

---

## 実行チェックリスト

### Phase 1: 現状確認
- [ ] Step 1.1: FastAPI起動確認
- [ ] Step 1.2: 全APIエンドポイントテスト
- [ ] Step 1.3: pytest実行

### Phase 2: 機能完成
- [ ] Step 2.1: HTMX改善判断
- [ ] Step 2.2: エラーハンドリング統一
- [ ] Step 2.3: サイドバー動的更新

### Phase 3: テスト拡充
- [ ] Step 3.1: 既存テスト確認
- [ ] Step 3.2: 追加テスト作成
- [ ] Step 3.3: E2Eテスト（オプション）

### Phase 4: 旧コード削除
- [ ] Step 4.1: 削除対象特定
- [ ] Step 4.2: 依存関係確認
- [ ] Step 4.3: 削除実行
- [ ] Step 4.4: requirements.txt整理

### Phase 5: デプロイ設定
- [ ] Step 5.1: Procfile更新
- [ ] Step 5.2: 環境変数確認
- [ ] Step 5.3: Docker対応（オプション）

### Phase 6: ドキュメント
- [ ] Step 6.1: CLAUDE.md更新
- [ ] Step 6.2: README.md更新

---

## 補足: ファイル構造（移行後）

```
MediDocsLMreferral/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── prompts.py
│   │   ├── settings.py
│   │   ├── statistics.py
│   │   └── summary.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── constants.py
│   │   └── database.py
│   ├── external/
│   │   ├── __init__.py
│   │   ├── api_factory.py
│   │   ├── base_api.py
│   │   ├── claude_api.py
│   │   └── gemini_api.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── prompt.py
│   │   ├── setting.py
│   │   └── usage.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── prompt.py
│   │   ├── statistics.py
│   │   └── summary.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── prompt_service.py
│   │   ├── statistics_service.py
│   │   └── summary_service.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   ├── templates/
│   │   ├── components/
│   │   │   └── sidebar.html
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── prompts.html
│   │   └── statistics.html
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── error_handlers.py
│   │   ├── exceptions.py
│   │   └── text_processor.py
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── api/
│   ├── services/
│   └── conftest.py
├── docs/
│   └── README.md
├── .env
├── .gitignore
├── CLAUDE.md
├── Procfile
├── requirements.txt
└── setup.sh
```

---

## リスクと対策

| リスク | 影響度 | 対策 |
|-------|-------|------|
| API互換性の問題 | 高 | Phase 1で徹底的にテスト |
| データベースマイグレーション | 中 | Alembicで管理 |
| 本番環境での動作差異 | 高 | ステージング環境でテスト |
| 旧コード削除による不具合 | 低 | Gitで履歴管理、段階的削除 |

---

## 所要時間目安

| Phase | 作業内容 | 目安 |
|-------|---------|-----|
| Phase 1 | 現状確認と検証 | 0.5日 |
| Phase 2 | 機能完成と改善 | 1-2日 |
| Phase 3 | テストの拡充 | 1日 |
| Phase 4 | 旧コード削除 | 0.5日 |
| Phase 5 | デプロイ設定更新 | 0.5日 |
| Phase 6 | ドキュメント更新 | 0.5日 |
| **合計** | | **4-5日** |

※ 既存のFastAPI実装の完成度により変動
