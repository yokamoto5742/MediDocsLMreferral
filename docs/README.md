# 診療情報提供書作成アプリ

このアプリケーションは、生成AIを活用して診療情報提供書を効率的に作成するためのWebアプリケーションです。

## 機能

### コア機能
- **複数のAIプロバイダーサポート**: Claude（Anthropic）とGemini（Google Vertex AI）の両方に統合
- **自動モデル切り替え**: 入力が指定文字数を超えると、自動的にClaudeからGeminiに切り替え
- **構造化文書生成**: 標準化されたセクションで医療文書を生成

### 文書管理
- **複数の文書タイプ**:
  - 他院への紹介
  - 紹介元への逆紹介
  - 返書
  - 最終返書
- **診療科別カスタマイズ**: 診療科ベースの設定に対応
- **医師別プロンプト**: 階層的プロンプトシステム（診療科 → 医師 → 文書タイプ）

### プロンプト管理
- **カスタムプロンプトテンプレート**: さまざまなシナリオ用のカスタムプロンプトを作成・管理
- **階層的継承**: 診療科と医師ごとのプロンプトカスタマイズ
- **Webベース UI**: プロンプトの作成と編集のための使いやすいインターフェース

### 分析とモニタリング
- **使用統計**: API使用状況、トークン数、作成時間を追跡
- **パフォーマンスメトリクス**: レスポンス時間とモデルパフォーマンスを監視

## アーキテクチャ概要

### デザインパターン

**Factory Pattern**: `app/external/api_factory.py` がAIプロバイダーのインスタンス化を管理
```python
# モデル選択に基づいて適切なAPIクライアントを動的に作成
api_client = get_api_client(model_name, api_key)
```

**Service Layer**: `app/services/` にはAPIルートから分離されたビジネスロジックが含まれる
- `summary_service.py`: 文書生成ロジック
- `prompt_service.py`: プロンプト管理
- `evaluation_service.py`: 出力評価ロジック
- `statistics_service.py`: 使用状況分析

**Repository Pattern**: `app/models/` にはデータベースモデルとデータアクセスが含まれる
- `prompt.py`: プロンプトテンプレート
- `evaluation_prompt.py`: 評価プロンプトテンプレート
- `usage.py`: API使用統計
- `setting.py`: アプリケーション設定

**MVC アーキテクチャ**:
- **Models**: `app/models/` 内のSQLAlchemy ORMモデル
- **Views**: `app/templates/` 内のJinja2テンプレート
- **Controllers**: `app/api/` 内のFastAPIルーター

### データフロー

1. **ユーザー入力**: ユーザーがWebインターフェースからカルテデータを入力し、文書タイプを選択
2. **リクエスト処理**: FastAPIエンドポイントが入力を受信・検証
3. **サービスレイヤー**: `SummaryService` が文書生成を調整
4. **AI統合**: Factoryパターンが適切なAPIクライアントをインスタンス化
5. **モデル選択**: 入力が指定文字数を超えた場合、自動的にClaudeからGeminiに切り替え
6. **文書生成**: AIが構造化された医療文書を生成
7. **後処理**: テキストプロセッサーが出力をセクションに解析
8. **データベースログ**: 使用統計とメタデータをPostgreSQLに保存
9. **レスポンス**: 構造化された文書をユーザーインターフェースに返却

### 主要コンポーネント

app/
├── api/            # FastAPI ルートハンドラー
│   ├── router.py   # メイン API ルーター
│   ├── summary.py  # 文書生成エンドポイント
│   ├── prompts.py  # プロンプト管理エンドポイント
│   ├── evaluation.py  # 出力評価エンドポイント
│   ├── statistics.py  # 出力統計エンドポイント
│   └── settings.py    # 設定エンドポイント
├── core/           # コア設定
│   ├── config.py   # 環境設定
│   ├── constants.py  # アプリケーション定数
│   └── database.py   # データベース接続
├── external/       # 外部 API 連携
│   ├── api_factory.py  # API クライアントファクトリ
│   ├── base_api.py     # ベース API クライアント
│   ├── claude_api.py   # Claude/Amazon Bedrock 連携
│   ├── gemini_api.py   # Gemini/Vertex AI 連携
│   └── gemini_evaluation.py  # 出力評価 API
├── models/         # データベースモデル
│   ├── prompt.py   # プロンプトテンプレート
│   ├── evaluation_prompt.py  # 評価プロンプトテンプレート
│   ├── usage.py    # 利用統計
│   └── setting.py  # アプリケーション設定
├── schemas/        # Pydantic スキーマ
│   ├── summary.py  # リクエスト/レスポンススキーマ
│   ├── prompt.py   # プロンプトスキーマ
│   ├── evaluation.py  # 評価スキーマ
│   └── statistics.py  # 統計スキーマ
├── services/       # ビジネスロジック
│   ├── summary_service.py  # 文書生成ロジック
│   ├── prompt_service.py   # プロンプト管理ロジック
│   ├── evaluation_service.py  # 出力評価ロジック
│   └── statistics_service.py  # 出力統計ロジック
├── utils/          # ユーティリティ関数
│   ├── text_processor.py  # テキスト解析
│   ├── exceptions.py      # カスタム例外
│   └── error_handlers.py  # エラーハンドリング
└── main.py         # FastAPI アプリケーション本体

## セットアップとインストール

### 前提条件

- Python 3.13以上
- PostgreSQL 16以上
- 少なくとも1つのAI APIアカウント:
  - AWS BedrockアクセスのClaude API 
  - Vertex AIが有効化されたGoogle Cloud Platformアカウント

### インストール手順

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd MediDocsLMreferral
```

1. **仮想環境の作成**
```bash
python -m venv .venv
source .venv\Scripts\activate
```

1. **依存関係のインストール**
```bash
pip install -r requirements.txt
```

1. **PostgreSQLデータベースのセットアップ**
```bash
# データベースの作成
createdb medidocs

# データベーステーブルは初回実行時に自動作成されます
```

1. **データベースマイグレーションの実行**
```bash
# テーブルは起動時にSQLAlchemyを介して自動作成されます
```

## 環境変数の設定

プロジェクトルートに以下の変数を含む `.env` ファイルを作成してください:

### データベース設定
```env
# PostgreSQL データベース
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=medidocs
POSTGRES_SSL=false

# コネクションプール設定
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Heroku データベース URL（オプション、個別設定を上書き）
DATABASE_URL=postgresql://user:password@host:port/database
```

### Claude API 設定

**AWS Bedrock**
```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-northeast-1
ANTHROPIC_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Google Vertex AI 設定
```env
# Google Cloud 認証情報（JSON形式）
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project",...}

# Vertex AI 設定
GOOGLE_PROJECT_ID=your-gcp-project-id
GOOGLE_LOCATION=asia-northeast1
GEMINI_MODEL=gemini-2.0-flash
GEMINI_THINKING_LEVEL=HIGH
```

### アプリケーション設定
```env
# トークン制限
MAX_INPUT_TOKENS=200000
MIN_INPUT_TOKENS=100
MAX_TOKEN_THRESHOLD=100000

# 機能
PROMPT_MANAGEMENT=true
APP_TYPE=default
SELECTED_AI_MODEL=Claude
```

## 使用方法

### アプリケーションの起動

**開発モード:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**本番モード:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Webインターフェースの使用

1. **メインページへのアクセス**: `http://localhost:8000` にアクセス
2. **患者情報の入力**:
   - 診療科と医師を選択
   - 文書タイプを選択
   - テキストエリアにカルテデータを入力
   - 追加情報を入力
3. **AIモデルの選択**: ClaudeまたはGeminiを選択（または自動切り替え）
4. **文書の生成**: 生成ボタンをクリック
5. **出力結果の確認**: 生成された文書が構造化されたセクションで表示される
6. **出力結果のコピー**: コピーボタンで出力結果のテキストをコピー

### プロンプトの管理

1. **Prompts** ページにアクセス
2. **新規プロンプトの作成**:
   - 診療科、医師、文書タイプを選択
   - カスタムプロンプトテンプレートを入力
   - プロンプトを保存
3. **既存プロンプトの編集**: プロンプトの横にある編集アイコンをクリック
4. **プロンプトの削除**: 削除アイコンをクリック

### 統計の表示

1. **Statistics** ページにアクセス
2. 統計用の日付範囲を選択
3. メトリクスの表示:
   - 合計API呼び出し数
   - モデル別トークン使用量
   - 平均作成時間

### APIの使用

**API経由での文書生成:**
```bash
curl -X POST "http://localhost:8000/api/summary/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "chart_data": "患者情報とカルテデータ",
    "additional_info": "追加情報",
    "department": "眼科",
    "doctor": "橋本義弘",
    "document_type": "他院への紹介",
    "model_name": "Claude"
  }'
```

**使用統計の取得:**
```bash
curl -X GET "http://localhost:8000/api/statistics?start_date=2026-01-01&end_date=2026-01-21"
```

## テスト

### テストの実行

**すべてのテストを実行:**
```bash
python -m pytest tests/ -v --tb=short
```

**カバレッジ付きで実行:**
```bash
python -m pytest tests/ -v --tb=short --cov=app --cov-report=html
```

**特定のテストファイルを実行:**
```bash
python -m pytest tests/services/test_summary_service.py -v
```

**特定のテストを実行:**
```bash
python -m pytest tests/services/test_summary_service.py::test_generate_summary -v
```

### テスト構造

```
tests/
├── conftest.py              # 共有フィクスチャ
├── api/                     # APIエンドポイントテスト
│   ├── test_prompts.py
│   ├── test_summary.py
│   ├── test_evaluation.py
│   ├── test_statistics.py
│   └── test_settings.py
├── core/                    # コア機能テスト
│   └── test_config.py
├── external/                # 外部APIテスト
│   ├── test_api_factory.py
│   ├── test_base_api.py
│   ├── test_claude_api.py
│   ├── test_gemini_api.py
│   └── test_gemini_evaluation.py
├── services/                # ビジネスロジックテスト
│   ├── test_prompt_service.py
│   ├── test_summary_service.py
│   ├── test_evaluation_service.py
│   └── test_statistics_service.py
└── test_utils/              # ユーティリティテスト
    └── test_text_processor.py
```

### テストカバレッジ

本プロジェクトは120以上のテストで包括的なテストカバレッジを維持:
- APIエンドポイント
- サービスレイヤーロジック
- 外部API統合
- データベース操作
- テキスト処理ユーティリティ
- エラー処理

## 使用技術

### バックエンドフレームワーク
- **FastAPI**: API構築のためのモダンで高速なWebフレームワーク
- **Uvicorn**: FastAPI用ASGIサーバー
- **Pydantic**: Pythonの型アノテーションを使用したデータ検証
- **SQLAlchemy**: SQLツールキットとORM

### データベース
- **PostgreSQL**: プロンプト、設定、使用データを保存する主要データベース
- **psycopg2-binary**: Python用PostgreSQLアダプター

### AI/ML統合
- **Google Generative AI**: Gemini API統合
- **Google Cloud AI Platform**: Vertex AI統合
- **boto3**: Amazon Bedrock統合用AWS SDK

### フロントエンド
- **Jinja2**: HTMLレンダリング用テンプレートエンジン
- **HTML/CSS/JavaScript**: フロントエンド技術

### テスト
- **pytest**: テストフレームワーク
- **pytest-cov**: カバレッジレポート
- **pytest-mock**: テスト用モックライブラリ

### 開発ツール
- **python-dotenv**: 環境変数管理
- **pyright**: Python用静的型チェッカー
- **uv**: 高速Pythonパッケージインストーラー

### 追加ライブラリ
- **httpx**: API呼び出し用HTTPクライアント
- **tenacity**: APIレジリエンス用リトライライブラリ
- **pydantic-settings**: 設定管理
- **python-multipart**: マルチパートフォームデータ解析

## 主要なビジネスロジック

### 自動モデル切り替え

アプリケーションは入力の長さに基づいてAIモデルを自動的に切り替えます:

```python
# 入力が40,000文字を超え、Claudeが選択されている場合
if input_length > 40000 and selected_model == "Claude":
    # 長い入力をより適切に処理するためにGeminiに切り替え
    switch_to_model("Gemini_Pro")
```

### 階層的プロンプトシステム

プロンプトは特異性の順序で解決されます:
1. 医師 + 文書タイプ固有のプロンプト
2. 診療科 + 文書タイプ固有のプロンプト
3. 文書タイプのデフォルトプロンプト

これにより、フォールバックデフォルトを維持しながら柔軟なカスタマイズが可能です。

### 使用状況の追跡

すべてのAPI呼び出しは以下の情報とともにログに記録されます:
- 使用されたモデル
- トークン数（入力/出力）
- 作成時間
- タイムスタンプ
- 診療科/医師/文書タイプのコンテキスト

## コントリビューション

### コードスタイル
- PEP 8ガイドラインに従う
- すべての関数に型ヒントを使用
- インポート順序: 標準ライブラリ → サードパーティ → ローカルモジュール
- インポートをアルファベット順に保つ

### コミットメッセージ
- 説明的なコミットメッセージを使用
- 可能な限り従来のコミット形式に従う
- 該当する場合は日本語と英語の説明を両方含める

## ライセンス

このプロジェクトは[Apache License 2.0](LICENSE)のもとで公開されています。

## サポート

問題、質問、コントリビューションについては、プロジェクトリポジトリを参照してください。

## 変更履歴
バージョン履歴と更新については、[CHANGELOG.md](CHANGELOG.md)を参照してください。

## セキュリティに関する注意事項

- 認証情報を含む `.env` ファイルをコミットしない
- APIキーを定期的にローテーション
- すべての機密設定に環境変数を使用
- セキュリティパッチのために依存関係を最新に保つ
- 本番医療現場で使用する前にAI生成コンテンツをレビュー

## 免責事項

このアプリケーションは、医療文書を作成するために生成AIを使用しています。すべてのAI生成コンテンツは、使用前に資格のある医療専門家によってレビューおよび検証される必要があります。このアプリケーションは文書作成を支援するツールであり、専門的な医学的判断に代わるものではありません。
