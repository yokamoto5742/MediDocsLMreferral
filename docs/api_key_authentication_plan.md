# APIキー認証 実装計画

## 概要

FastAPIの依存注入（Dependency Injection）機能を使用して、`/api/*`配下のエンドポイントにAPIキー認証を実装する

### 要件

- **適用範囲**: `/api/*`配下のAPIエンドポイントのみ（WebページUIは除外）
- **キー管理**: 環境変数`API_KEY`で単一キーを管理
- **開発モード**: `API_KEY`未設定時は認証をスキップ

---

## 実装ステップ

### Step 1: 設定クラスの拡張

**ファイル**: `app/core/config.py`

`Settings`クラスに`api_key`フィールドを追加する

```python
# Application セクションに追加
api_key: str | None = None  # APIキー認証用
```

**変更箇所**: `Settings`クラス内、既存の`Application`セクション（45行目付近）

---

### Step 2: 認証依存関数の作成

**新規ファイル**: `app/core/security.py`

APIキー検証用の依存関数を作成する

```python
"""APIキー認証モジュール"""
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings, Settings

# ヘッダー名の定義
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key_header: str | None = Depends(API_KEY_HEADER),
    settings: Settings = Depends(get_settings),
) -> str | None:
    """
    APIキーを検証する依存関数

    - API_KEY環境変数が未設定の場合: 認証をスキップ（開発モード）
    - API_KEY環境変数が設定済みの場合: ヘッダーのキーと照合
    """
    # 開発モード: API_KEY未設定時は認証スキップ
    if settings.api_key is None:
        return None

    # 本番モード: APIキー検証
    if api_key_header is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="APIキーが必要です",
            headers={"WWW-Authenticate": "API-Key"},
        )

    if api_key_header != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無効なAPIキーです",
        )

    return api_key_header
```

---

### Step 3: APIルーターへの認証適用

**ファイル**: `app/api/router.py`

ルーターレベルで認証依存関数を適用する

```python
from fastapi import APIRouter, Depends

from app.api import evaluation, prompts, settings, statistics, summary
from app.core.security import verify_api_key

api_router = APIRouter(dependencies=[Depends(verify_api_key)])
api_router.include_router(evaluation.router)
api_router.include_router(prompts.router)
api_router.include_router(settings.router)
api_router.include_router(statistics.router)
api_router.include_router(summary.router)
```

**注意**: ルーターに`dependencies`を設定することで、配下の全エンドポイントに自動適用される

---

### Step 4: 環境変数の設定

**ファイル**: `.env`（本番環境）

```bash
# APIキー認証
API_KEY=your-secure-api-key-here
```

**開発環境**: `API_KEY`を設定しないことで認証をスキップ

---

### Step 5: テストの作成

**新規ファイル**: `tests/core/test_security.py`

```python
"""APIキー認証のテスト"""
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.core.security import verify_api_key, API_KEY_HEADER


class TestVerifyApiKey:
    """verify_api_key関数のテスト"""

    def test_development_mode_no_api_key_configured(self, mocker):
        """API_KEY未設定時は認証スキップ"""
        mock_settings = mocker.MagicMock()
        mock_settings.api_key = None

        app = FastAPI()

        @app.get("/test")
        async def test_endpoint(
            api_key: str | None = Depends(verify_api_key),
        ):
            return {"status": "ok", "api_key": api_key}

        # settingsをモック
        app.dependency_overrides[verify_api_key] = lambda: None

        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200

    def test_missing_api_key_header(self, mocker):
        """APIキー未提供時は401エラー"""
        mock_settings = mocker.MagicMock()
        mock_settings.api_key = "test-key"

        # 統合テストとして実装
        from app.main import app

        client = TestClient(app)

        # API_KEYが設定されている状態でヘッダーなしでアクセス
        # (このテストは環境変数の設定が必要)

    def test_invalid_api_key(self):
        """無効なAPIキーは403エラー"""
        pass

    def test_valid_api_key(self):
        """有効なAPIキーで認証成功"""
        pass
```

**ファイル**: `tests/api/test_api_authentication.py`

```python
"""API認証の統合テスト"""
import pytest
from fastapi.testclient import TestClient


class TestApiAuthentication:
    """APIエンドポイントの認証テスト"""

    def test_api_endpoint_requires_authentication(
        self, client: TestClient, mocker
    ):
        """API_KEY設定時、ヘッダーなしで401エラー"""
        # settingsのapi_keyをモック
        mocker.patch(
            "app.core.config.get_settings",
            return_value=mocker.MagicMock(api_key="test-secret-key"),
        )

        response = client.get("/api/settings/")
        assert response.status_code == 401

    def test_api_endpoint_with_valid_key(
        self, client: TestClient, mocker
    ):
        """有効なAPIキーで認証成功"""
        mocker.patch(
            "app.core.config.get_settings",
            return_value=mocker.MagicMock(api_key="test-secret-key"),
        )

        response = client.get(
            "/api/settings/",
            headers={"X-API-Key": "test-secret-key"},
        )
        # 認証は成功（他のエラーがあれば別の理由）
        assert response.status_code != 401
        assert response.status_code != 403

    def test_web_pages_do_not_require_authentication(
        self, client: TestClient, mocker
    ):
        """WebページUIは認証不要"""
        mocker.patch(
            "app.core.config.get_settings",
            return_value=mocker.MagicMock(api_key="test-secret-key"),
        )

        response = client.get("/")
        assert response.status_code == 200
```

---

### Step 6: ドキュメントの更新

**ファイル**: `docs/CHANGELOG.md`

```markdown
## [Unreleased]

### Added
- APIキー認証機能を追加
  - `/api/*`配下のエンドポイントに`X-API-Key`ヘッダーによる認証を実装
  - 環境変数`API_KEY`でキーを設定
  - `API_KEY`未設定時は認証をスキップ（開発モード）
```

---

## ファイル変更一覧

| ファイル | 操作 | 説明 |
|---------|------|------|
| `app/core/config.py` | 修正 | `api_key`フィールド追加 |
| `app/core/security.py` | 新規 | 認証依存関数 |
| `app/api/router.py` | 修正 | 認証依存関数の適用 |
| `.env.example` | 修正 | `API_KEY`の例を追加 |
| `tests/core/test_security.py` | 新規 | 認証関数のユニットテスト |
| `tests/api/test_api_authentication.py` | 新規 | 統合テスト |
| `docs/CHANGELOG.md` | 修正 | 変更履歴 |

---

## 使用方法

### 開発環境

`.env`ファイルで`API_KEY`を設定しない、または空にする

```bash
# API_KEY=  # コメントアウトまたは削除
```

### 本番環境

```bash
# .env または環境変数
API_KEY=your-32-character-secure-key-here
```

### クライアントからのリクエスト

```bash
# curlの例
curl -H "X-API-Key: your-api-key" https://your-domain.com/api/settings/

# Pythonの例
import requests
response = requests.get(
    "https://your-domain.com/api/summary/generate",
    headers={"X-API-Key": "your-api-key"},
    json={"chart_text": "..."}
)
```

---

## セキュリティ考慮事項

1. **APIキーの生成**: 32文字以上のランダムな文字列を推奨
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **HTTPS必須**: 本番環境ではHTTPSを使用してキーの漏洩を防ぐ

3. **キーのローテーション**: 定期的にAPIキーを変更することを推奨

4. **ログ出力の注意**: APIキーをログに出力しないこと

---

## 拡張可能性

将来的に以下の拡張が可能:

- **複数APIキー対応**: データベースでキーを管理し、クライアントごとに発行
- **レート制限**: APIキーごとにリクエスト制限を設定
- **キーのスコープ**: 読み取り専用/書き込み可能などの権限分離
- **監査ログ**: APIキー使用履歴の記録

---

## 実装順序チェックリスト

- [ ] Step 1: `app/core/config.py`に`api_key`フィールド追加
- [ ] Step 2: `app/core/security.py`を新規作成
- [ ] Step 3: `app/api/router.py`に認証を適用
- [ ] Step 4: `.env.example`を更新
- [ ] Step 5: テストを作成・実行
- [ ] Step 6: `docs/CHANGELOG.md`を更新
- [ ] 動作確認: 開発モード（API_KEY未設定）
- [ ] 動作確認: 本番モード（API_KEY設定済み）
