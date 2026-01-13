# FastAPI移行ガイド

## 概要

このプロジェクトは、StreamlitアプリからFastAPIアプリへの段階的な移行を行っています。現在、両方のアプリが同じデータベースを共有しており、独立して動作します。

## アーキテクチャ

### 既存Streamlitアプリ
- **ディレクトリ**: `views/`, `ui_components/`, `utils/`, `services/`
- **起動**: `streamlit run app.py`
- **ポート**: 8501
- **データベース接続**: `database/db.py` (DatabaseManager)
- **プロンプト管理**: `utils/prompt_manager.py`

### 新しいFastAPIアプリ
- **ディレクトリ**: `app/`
- **起動**: `uvicorn app.main:app --reload`
- **ポート**: 8000
- **データベース接続**: `app/core/database.py` (SQLAlchemy)
- **プロンプト管理**: `app/services/prompt_service.py`

## データベーススキーマ互換性

両アプリは同じPostgreSQLデータベースを使用しており、以下のテーブルを共有します：

### `prompts` テーブル
```sql
CREATE TABLE prompts (
    id SERIAL PRIMARY KEY,
    department VARCHAR(100) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    doctor VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    selected_model VARCHAR(50),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_prompt UNIQUE (department, document_type, doctor)
)
```

### `summary_usage` テーブル
```sql
CREATE TABLE summary_usage (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    app_type VARCHAR(50),
    document_types VARCHAR(100),
    model_detail VARCHAR(100),
    department VARCHAR(100),
    doctor VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    processing_time INTEGER
)
```

## 機能比較

| 機能 | Streamlit | FastAPI | 状態 |
|------|-----------|---------|------|
| 文書生成 | ✓ | ✓ (API) | 両方利用可能 |
| プロンプト管理 | ✓ | ✓ | 両方利用可能 |
| 統計情報 | - | ✓ | FastAPIのみ |
| API アクセス | - | ✓ | FastAPIのみ |

## プロンプト管理の実装比較

### Streamlit実装 (`utils/prompt_manager.py`)
- 生SQLクエリを使用
- `DatabaseManager`クラス経由でデータベースアクセス
- 関数ベースのAPI: `get_prompt()`, `create_or_update_prompt()`, `delete_prompt()`

### FastAPI実装 (`app/services/prompt_service.py`)
- SQLAlchemy ORMを使用
- セッション管理による安全なトランザクション処理
- 関数ベースのAPI: `get_prompt()`, `create_or_update_prompt()`, `delete_prompt()`

### 共通点
- 同じデータベーステーブルを使用
- 同じビジネスロジック
- 互換性のあるデータ構造

## 移行戦略

### フェーズ1: 並行運用（現在）
- StreamlitアプリとFastAPIアプリが独立して動作
- 同じデータベースを共有
- ユーザーは両方のアプリにアクセス可能

### フェーズ2: 段階的移行
1. FastAPIのフロントエンドを完成させる
2. ユーザーにFastAPIアプリの使用を促す
3. Streamlitアプリの使用を段階的に減らす

### フェーズ3: 完全移行
1. Streamlitアプリの廃止
2. `utils/`, `views/`, `ui_components/`の削除
3. FastAPIアプリのみの運用

## テスト

### FastAPIアプリのテスト
```bash
# 全テスト実行
python -m pytest tests/app/ -v

# 特定のテストのみ
python -m pytest tests/app/api/test_prompts.py -v
python -m pytest tests/app/api/test_statistics.py -v
python -m pytest tests/app/services/test_prompt_service.py -v
```

### Streamlitアプリのテスト
```bash
# 全テスト実行
python -m pytest tests/ -v --ignore=tests/app/

# 特定のテストのみ
python -m pytest tests/test_prompt_manager.py -v
python -m pytest tests/test_summary_service.py -v
```

## 開発ガイドライン

### FastAPIアプリの開発
1. **モデル定義**: `app/models/` に SQLAlchemy モデルを追加
2. **スキーマ定義**: `app/schemas/` に Pydantic スキーマを追加
3. **サービス実装**: `app/services/` にビジネスロジックを実装
4. **API実装**: `app/api/` にエンドポイントを追加
5. **テスト作成**: `tests/app/` に対応するテストを作成

### Streamlitアプリの開発（非推奨）
- 新機能の追加は推奨されません
- バグ修正のみ実施してください

## トラブルシューティング

### データベース接続エラー
```bash
# 環境変数を確認
cat .env | grep DATABASE_URL

# データベースが起動しているか確認
psql -h localhost -U postgres -d medidocs
```

### ポート競合
- Streamlit: 8501
- FastAPI: 8000
- 別のポートで起動する場合:
  ```bash
  streamlit run app.py --server.port 8502
  uvicorn app.main:app --port 8001
  ```

## API エンドポイント

### プロンプト管理
- `GET /api/prompts/` - プロンプト一覧取得
- `POST /api/prompts/` - プロンプト作成/更新
- `DELETE /api/prompts/{prompt_id}` - プロンプト削除

### 統計情報
- `GET /api/statistics/summary` - 統計サマリー取得
- `GET /api/statistics/records` - 使用履歴取得

### ドキュメント
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## まとめ

現在、StreamlitアプリとFastAPIアプリは共存しており、ユーザーは両方を使用できます。データベースは共有されているため、どちらのアプリで作成したプロンプトも他方のアプリで使用できます。

段階的な移行により、ユーザーへの影響を最小限に抑えながら、モダンなアーキテクチャへの移行を実現しています。
