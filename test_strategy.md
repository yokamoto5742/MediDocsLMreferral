# MediDocsLM Referral - テスト戦略書

## 1. コード構造の分析結果

### 1.1 アーキテクチャ概要

```
app/
├── api/           # APIルーター層（FastAPIエンドポイント）
├── core/          # コア設定（config, constants, database）
├── external/      # 外部API連携（Claude, Gemini）
├── models/        # SQLAlchemyモデル
├── schemas/       # Pydanticスキーマ
├── services/      # ビジネスロジック層
└── utils/         # ユーティリティ（例外、テキスト処理）
```

### 1.2 モジュール依存関係

```
API層 → Services層 → External層/Models層
         ↓
      Utils層（text_processor, exceptions）
         ↓
      Core層（config, constants, database）
```

### 1.3 複雑度評価

| モジュール | 複雑度 | 理由 |
|-----------|--------|------|
| `services/summary_service.py` | **高** | 複数の外部依存、条件分岐、エラーハンドリング |
| `external/api_factory.py` | **中** | ファクトリパターン、プロバイダー切替 |
| `external/claude_api.py` | **中** | AWS認証、外部API呼び出し |
| `external/gemini_api.py` | **中** | Google認証、Vertex AI連携 |
| `services/prompt_service.py` | **低** | 単純なCRUD操作 |
| `services/statistics_service.py` | **低** | SQLAlchemyクエリのみ |
| `utils/text_processor.py` | **低** | 純粋関数、状態なし |

---

## 2. 優先度別テスト対象一覧

### 2.1 【最優先（P0）- 必須テスト】

#### `app/services/summary_service.py`

| 関数 | テスト種別 | 優先度理由 |
|------|-----------|-----------|
| `execute_summary_generation()` | 正常系・異常系・統合 | **ビジネスロジックの核**。文書生成のオーケストレーション全体を担う |
| `validate_input()` | 正常系・異常系・境界値 | **データ整合性**。入力検証はセキュリティとUXに直結 |
| `determine_model()` | 正常系・異常系・境界値 | **重要なビジネスルール**。モデル自動切替ロジック |
| `get_provider_and_model()` | 正常系・異常系 | **外部連携**。プロバイダー選択の正確性が必須 |
| `save_usage()` | 正常系・異常系 | **データ整合性**。統計データの永続化 |

**テストケース設計**:

```
validate_input()
├── 正常系
│   ├── 適切な長さの入力で (True, None) を返す
│   └── 境界値 min_input_tokens ちょうどで成功
├── 異常系
│   ├── 空文字列で (False, "カルテ情報を入力してください")
│   ├── 空白のみで (False, "カルテ情報を入力してください")
│   ├── min_input_tokens 未満で (False, "入力文字数が少なすぎます")
│   └── max_input_tokens 超過で (False, "入力文字数が...を超えています")
└── 境界値
    ├── min_input_tokens - 1 で失敗
    ├── min_input_tokens で成功
    ├── max_input_tokens で成功
    └── max_input_tokens + 1 で失敗

determine_model()
├── 正常系
│   ├── Claude指定 + 閾値以下 → Claude維持
│   ├── Gemini_Pro指定 → Gemini_Pro維持
│   └── プロンプトからモデル取得成功
├── 異常系
│   ├── 入力長超過 + Gemini未設定 → ValueError
│   └── プロンプト取得失敗時も処理継続
└── 境界値
    ├── max_token_threshold ちょうど → 切替なし
    └── max_token_threshold + 1 → Gemini切替

execute_summary_generation()
├── 正常系
│   ├── 完全な入力で SummaryResult(success=True) を返す
│   ├── モデル切替発生時に model_switched=True
│   └── 統計保存が正常に実行される
├── 異常系
│   ├── 入力検証失敗で error_message 設定
│   ├── モデル決定失敗で error_message 設定
│   ├── API呼び出し失敗で error_message 設定
│   └── 統計保存失敗でも処理は成功
└── 統合
    └── Claude → Gemini 自動切替の E2E フロー
```

#### `app/external/api_factory.py`

| 関数/クラス | テスト種別 | 優先度理由 |
|------------|-----------|-----------|
| `APIFactory.create_client()` | 正常系・異常系 | **ファクトリパターン**。適切なクライアント生成が必須 |
| `APIFactory.generate_summary_with_provider()` | 正常系・異常系 | **外部連携のエントリポイント** |
| `generate_summary()` | 正常系 | ファクトリへの委譲確認 |

**テストケース設計**:

```
APIFactory.create_client()
├── 正常系
│   ├── "claude" → ClaudeAPIClient インスタンス
│   ├── "gemini" → GeminiAPIClient インスタンス
│   ├── APIProvider.CLAUDE → ClaudeAPIClient
│   └── APIProvider.GEMINI → GeminiAPIClient
└── 異常系
    ├── 未対応プロバイダー文字列 → APIError
    └── 不正な型 → APIError
```

#### `app/external/base_api.py`

| メソッド | テスト種別 | 優先度理由 |
|---------|-----------|-----------|
| `create_summary_prompt()` | 正常系・異常系 | **プロンプト生成**。AI出力品質に直結 |
| `generate_summary()` | 正常系・異常系 | **外部API呼び出しの共通処理** |
| `get_model_name()` | 正常系 | モデル名取得ロジック |

**テストケース設計**:

```
create_summary_prompt()
├── 正常系
│   ├── 必須項目のみでプロンプト生成
│   ├── 全オプション指定でプロンプト生成
│   ├── カスタムプロンプト使用
│   └── デフォルトプロンプトへのフォールバック
└── 異常系
    └── プロンプト取得失敗時のデフォルト使用

generate_summary()
├── 正常系
│   ├── 初期化 → プロンプト生成 → コンテンツ生成の流れ
│   └── model_name 未指定時のデフォルト使用
└── 異常系
    ├── 初期化失敗で APIError
    └── コンテンツ生成失敗で APIError
```

#### `app/external/claude_api.py`

| メソッド | テスト種別 | 優先度理由 |
|---------|-----------|-----------|
| `initialize()` | 正常系・異常系 | **AWS認証**。セキュリティクリティカル |
| `_generate_content()` | 正常系・異常系 | **外部API呼び出し** |

**テストケース設計**:

```
initialize()
├── 正常系
│   └── 全認証情報設定済みで True を返す
└── 異常系
    ├── AWS_ACCESS_KEY_ID 未設定 → APIError
    ├── AWS_SECRET_ACCESS_KEY 未設定 → APIError
    ├── AWS_REGION 未設定 → APIError
    └── ANTHROPIC_MODEL 未設定 → APIError

_generate_content()
├── 正常系
│   └── 正常レスポンスで (text, input_tokens, output_tokens) を返す
└── 異常系
    ├── API呼び出し失敗 → APIError
    └── 空レスポンス → MESSAGES["EMPTY_RESPONSE"]
```

#### `app/external/gemini_api.py`

| メソッド | テスト種別 | 優先度理由 |
|---------|-----------|-----------|
| `initialize()` | 正常系・異常系 | **Google認証**。複数認証パターン |
| `_generate_content()` | 正常系・異常系 | **Vertex AI呼び出し** |

**テストケース設計**:

```
initialize()
├── 正常系
│   ├── GOOGLE_CREDENTIALS_JSON 使用で初期化成功
│   └── デフォルト認証で初期化成功
└── 異常系
    ├── GOOGLE_PROJECT_ID 未設定 → APIError
    ├── 不正なJSON形式 → APIError
    └── 認証情報フィールド不足 → APIError

_generate_content()
├── 正常系
│   ├── ThinkingLevel.LOW 設定
│   └── ThinkingLevel.HIGH 設定
└── 異常系
    └── Vertex AI API エラー → APIError
```

---

### 2.2 【高優先度（P1）- 推奨テスト】

#### `app/utils/text_processor.py`

| 関数 | テスト種別 | 優先度理由 |
|------|-----------|-----------|
| `format_output_summary()` | 正常系・境界値 | **出力品質**。UIに表示されるテキスト整形 |
| `parse_output_summary()` | 正常系・異常系・境界値 | **複雑なパース処理**。セクション抽出の正確性 |

**テストケース設計**:

```
format_output_summary()
├── 正常系
│   ├── '*' 削除
│   ├── '＊' 削除
│   ├── '#' 削除
│   ├── ' '（半角スペース）削除
│   └── 複合パターン
└── 境界値
    ├── 空文字列
    └── 特殊文字のみ

parse_output_summary()
├── 正常系
│   ├── コロンあり形式（主病名: 高血圧症）
│   ├── 全角コロン形式（主病名：高血圧症）
│   ├── コロンなし形式（主病名 高血圧症）
│   ├── エイリアス変換（治療内容 → 治療経過）
│   ├── 複数行のセクション内容
│   └── 全セクション抽出
├── 異常系
│   ├── セクション名なしの行
│   └── 未知のセクション名
└── 境界値
    ├── 空文字列
    ├── 改行のみ
    └── セクション名のみ（内容なし）
```

#### `app/services/prompt_service.py`

| 関数 | テスト種別 | 優先度理由 |
|------|-----------|-----------|
| `get_all_prompts()` | 正常系 | **データ取得**。一覧表示 |
| `get_prompt()` | 正常系・異常系 | **階層検索**。department/doctor/document_type |
| `get_prompt_by_id()` | 正常系・異常系 | **ID検索** |
| `create_or_update_prompt()` | 正常系 | **Upsertロジック** |
| `delete_prompt()` | 正常系・異常系 | **削除処理** |

**テストケース設計**:

```
get_prompt()
├── 正常系
│   ├── 完全一致で Prompt を返す
│   └── 該当なしで None を返す
└── 異常系
    └── DBセッションエラー時の挙動

create_or_update_prompt()
├── 正常系
│   ├── 新規作成
│   ├── 既存更新（content変更）
│   └── selected_model 更新
```

#### `app/services/statistics_service.py`

| 関数 | テスト種別 | 優先度理由 |
|------|-----------|-----------|
| `get_usage_summary()` | 正常系・境界値 | **集計処理**。統計表示 |
| `get_aggregated_records()` | 正常系・境界値 | **グループ集計** |
| `get_usage_records()` | 正常系・境界値 | **ページネーション** |

**テストケース設計**:

```
get_usage_summary()
├── 正常系
│   ├── フィルターなしで全件集計
│   ├── start_date フィルター
│   ├── end_date フィルター
│   ├── model フィルター
│   └── 複合フィルター
└── 境界値
    ├── データなしで 0 を返す
    └── 日付境界の確認

get_aggregated_records()
├── 正常系
│   ├── document_type, department, doctor でグループ化
│   ├── "default" → "全科共通"/"医師共通" 変換
│   └── NULL値の "-" 変換
```

#### `app/api/summary.py`

| 関数 | テスト種別 | 優先度理由 |
|------|-----------|-----------|
| `generate_summary()` | 統合テスト | **APIエンドポイント** |
| `get_available_models()` | 正常系 | **モデル一覧取得** |

**テストケース設計**:

```
POST /api/summary/generate
├── 正常系
│   ├── 有効なリクエストで SummaryResponse を返す
│   └── model_switched フラグの確認
└── 異常系
    ├── medical_text 空で 422 Validation Error
    └── サービス層エラーで error_message 設定

GET /api/summary/models
├── 正常系
│   ├── Claude設定時に "Claude" を含む
│   ├── Gemini設定時に "Gemini_Pro" を含む
│   └── 両方設定時に両方を返す
└── 境界値
    └── どちらも未設定で空配列
```

#### `app/core/config.py`

| クラス/関数 | テスト種別 | 優先度理由 |
|------------|-----------|-----------|
| `Settings` | 正常系 | **設定初期化** |
| `Settings.get_database_url()` | 正常系・境界値 | **DB接続URL構築** |
| `get_settings()` | 正常系 | **キャッシュ動作** |

**テストケース設計**:

```
Settings.get_database_url()
├── 正常系
│   ├── 個別設定から URL 構築
│   ├── DATABASE_URL（Heroku形式）使用
│   ├── postgres:// → postgresql:// 変換
│   └── SSL有効時の ?sslmode=require 追加
└── 境界値
    └── SSL無効時のパラメータなし
```

---

### 2.3 【中優先度（P2）- 可能であれば実施】

#### `app/utils/exceptions.py`

| クラス | テスト種別 | 優先度理由 |
|--------|-----------|-----------|
| `AppError` | 正常系 | 基底例外クラス |
| `APIError` | 正常系 | API例外の継承確認 |
| `DatabaseError` | 正常系 | DB例外の継承確認 |

**テストケース設計**:

```
例外クラス
├── 正常系
│   ├── AppError が Exception を継承
│   ├── APIError が AppError を継承
│   ├── DatabaseError が AppError を継承
│   └── メッセージの設定と取得
```

#### `app/schemas/summary.py`

| クラス | テスト種別 | 優先度理由 |
|--------|-----------|-----------|
| `SummaryRequest` | 正常系・異常系 | Pydanticバリデーション |
| `SummaryResponse` | 正常系 | レスポンス構造確認 |

**テストケース設計**:

```
SummaryRequest
├── 正常系
│   ├── 必須項目のみで有効
│   └── 全項目設定で有効
└── 異常系
    ├── medical_text 空で ValidationError
    └── 必須項目欠落で ValidationError
```

#### `app/models/prompt.py`, `app/models/usage.py`

| クラス | テスト種別 | 優先度理由 |
|--------|-----------|-----------|
| `Prompt` | 正常系 | ORMマッピング確認 |
| `SummaryUsage` | 正常系 | ORMマッピング確認 |

**テストケース設計**:

```
Prompt モデル
├── 正常系
│   ├── インスタンス生成
│   ├── カラムマッピング確認
│   └── デフォルト値確認（is_default=False）

SummaryUsage モデル
├── 正常系
│   ├── インスタンス生成
│   └── カラム名マッピング（document_types, model_detail）
```

#### `app/core/database.py`

| 関数 | テスト種別 | 優先度理由 |
|------|-----------|-----------|
| `get_db()` | 正常系 | セッション生成・クローズ |
| `get_db_session()` | 正常系・異常系 | コンテキストマネージャ |

---

### 2.4 【低優先度（P3）- テスト不要またはオプション】

以下は **テスト不要** または **オプション** として扱います。

---

## 3. テストが不要な部分の明示

| モジュール/要素 | 理由 |
|----------------|------|
| `app/core/constants.py` | **定数定義のみ**。副作用なし、ビジネスロジックなし |
| `app/models/base.py` | **SQLAlchemy Base定義のみ**。SQLAlchemyライブラリの動作確認は不要 |
| `app/api/router.py` | **ルーター集約のみ**。`include_router()` の呼び出しのみ |
| `app/schemas/prompt.py` | **単純なPydanticスキーマ**。Pydanticのバリデーションは信頼可能 |
| `app/schemas/statistics.py` | **単純なPydanticスキーマ** |
| `utils/config.py` (root) | **互換性ラッパー**。`app.core.config` への委譲のみ |
| `utils/prompt_manager.py` (root) | **互換性ラッパー**。`app.services.prompt_service` への委譲のみ |
| `app/static/`, `app/templates/` | **静的ファイル**。ユニットテスト対象外 |
| `app/main.py` のHTML表示関数 | **テンプレートレンダリング**。E2Eテストで確認 |

---

## 4. テストカバレッジ目標

| 優先度 | ライン | ブランチ | 対象モジュール例 |
|--------|--------|----------|------------------|
| **P0** | 100% | 100% | summary_service, api_factory, claude_api, gemini_api, base_api |
| **P1** | 90%+ | 85%+ | text_processor, prompt_service, statistics_service, api/summary |
| **P2** | 80%+ | 75%+ | exceptions, schemas, models, database |
| **P3** | - | - | constants, router, 互換性ラッパー |

---

## 5. モック戦略

### 5.1 外部依存のモック対象

| 依存 | モック方法 | 理由 |
|------|-----------|------|
| `AnthropicBedrock` | `unittest.mock.patch` | AWS APIコスト削減、テスト速度向上 |
| `genai.Client` | `unittest.mock.patch` | Google APIコスト削減 |
| `get_db_session()` | `pytest.fixture` | インメモリSQLiteでテスト |
| `get_settings()` | `unittest.mock.patch` | 環境変数依存の排除 |
| `utils.prompt_manager.get_prompt()` | `unittest.mock.patch` | DBアクセスの分離 |

### 5.2 モック例

```python
# summary_service のテスト例
@pytest.fixture
def mock_settings(mocker):
    settings = mocker.MagicMock()
    settings.min_input_tokens = 100
    settings.max_input_tokens = 200000
    settings.max_token_threshold = 100000
    settings.gemini_model = "gemini-pro"
    mocker.patch("app.services.summary_service.settings", settings)
    return settings

@pytest.fixture
def mock_generate_summary(mocker):
    return mocker.patch(
        "app.services.summary_service.generate_summary",
        return_value=("生成結果", 100, 50)
    )
```

---

## 6. テスト実行コマンド

```bash
# 全テスト実行
python -m pytest tests/ -v --tb=short

# カバレッジ付き
python -m pytest tests/ -v --cov=app --cov-report=html

# P0テストのみ（マーカー使用時）
python -m pytest tests/ -v -m "p0"

# 特定モジュール
python -m pytest tests/services/test_summary_service.py -v
```

---

## 7. 推奨テストファイル構成

```
tests/
├── conftest.py              # 共通fixture
├── api/
│   ├── test_summary.py      # P1
│   ├── test_prompts.py      # P1
│   └── test_statistics.py   # P1
├── services/
│   ├── test_summary_service.py    # P0
│   ├── test_prompt_service.py     # P1
│   └── test_statistics_service.py # P1
├── external/
│   ├── test_api_factory.py  # P0
│   ├── test_base_api.py     # P0
│   ├── test_claude_api.py   # P0
│   └── test_gemini_api.py   # P0
├── utils/
│   └── test_text_processor.py # P1
├── core/
│   └── test_config.py       # P1
└── schemas/
    └── test_summary_schema.py # P2
```

---

## 8. 注意事項

1. **環境変数の分離**: テスト用の `.env.test` または `conftest.py` でモック設定
2. **DBの分離**: インメモリSQLite（`sqlite:///:memory:`）を使用
3. **外部API呼び出しの禁止**: すべての外部API呼び出しはモック化必須
4. **タイムゾーン考慮**: `ZoneInfo("Asia/Tokyo")` を使用するテストは時刻固定
5. **非同期処理**: `save_usage()` の例外無視動作を確認

---

*作成日: 2026-01-21*
*対象プロジェクト: MediDocsLM Referral*
