## セキュリティ分析

#### Critical（高リスク）
2. **admin_routerに認証なし**: プロンプト管理（CRUD）、設定変更、統計情報閲覧のエンドポイントがCSRF保護すらなく公開（`app/api/router.py:7-12`）
3. **CSRF秘密鍵のフォールバック**: `csrf_secret_key`未設定時にランダム生成されるが、サーバー再起動で全トークンが無効化される（`app/core/security.py:18-19`）。ワーカー複数台の場合、各プロセスで異なる鍵になりトークン検証が破綻する

#### High（中高リスク）
4. **CORSミドルウェア未設定**: CORSポリシーが明示的に設定されていない。FastAPIのデフォルトはCORS許可なしだが、明示設定がベストプラクティス
5. **セキュリティヘッダー未設定**: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy`等のレスポンスヘッダーが未実装

#### Medium（中リスク）
10. **入力サニタイゼーション不足**: XSS対策の明示的なサニタイゼーション処理が見当たらない。Jinja2のautoescapeに依存


## 4. スコア向上のための推奨事項（優先度順）

### 管理エンドポイント（`admin_router`）にCSRF保護を追加

**最低限の対応例**:
```python
# app/api/router.py
# admin_routerにもCSRF保護を追加
admin_router = APIRouter(dependencies=[Depends(require_csrf_token)])
```

### 2. セキュリティヘッダーの追加
**優先度: 高**

FastAPIミドルウェアでレスポンスヘッダーを追加:

```python
# app/main.py
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### 3. 監査ログの実装
**優先度: 高**

医療情報システムの安全管理ガイドライン（厚労省）では操作記録が求められる。最低限、文書生成・評価実行・プロンプト変更の操作ログを記録する仕組みを追加。生成AIに投入するカルテテキストを含んだプロンプトと、生成AIの出力結果の中身はログに個人情報を含む可能性があるためログに出力しない。

**実装例**:
```python
# app/services/summary_service.py
import logging
audit_logger = logging.getLogger("audit")

async def generate_summary(...):
    audit_logger.info({
        "event": "document_generation",
        "user_ip": request.client.host,
        "document_type": document_type,
        "model": selected_model,
        "timestamp": datetime.utcnow().isoformat()
    })
```

Papertrailへの構造化ログ出力で対応可能。

### 5. 入力バリデーション・サニタイゼーション強化
**優先度: 中**

AI APIに送信する前のテキスト入力に対する明示的なサニタイゼーション処理を追加。プロンプトインジェクション対策として、入力テキストのパターン検査を検討する。

**実装例**:
```python
# app/utils/input_validator.py
import re

def sanitize_medical_text(text: str) -> str:
    """医療テキストのサニタイゼーション"""
    # HTMLタグの除去
    text = re.sub(r'<[^>]+>', '', text)
    # スクリプトタグの完全除去
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 異常な制御文字の除去
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    return text
```

## 6. 今後の改善ロードマップ（推奨）

### Phase 1: 緊急対応
1. `admin_router`にCSRF保護を追加
2. `csrf_secret_key`を環境変数で必須設定化
3. セキュリティヘッダーミドルウェアの追加

### Phase 2: 重要対応
4. 監査ログの実装（構造化ログ出力）
5. 入力サニタイゼーション処理の追加

### Phase 3: 中長期対応 ✅完了
6. ✅ CORS設定の明示化
   - FastAPIのCORSMiddlewareを明示的に追加
   - 環境変数でCORS設定を管理（CORS_ORIGINS, CORS_ALLOW_CREDENTIALS等）
   - デフォルトは同一オリジンのみ許可
7. ✅ プロンプトインジェクション対策の実装
   - プロンプトインジェクション攻撃パターンの検出機能を追加
   - システムプロンプト上書き指示、ロールプレイング攻撃、異常な繰り返しパターンの検出
   - 文書生成と評価の両方で入力検証を実施
