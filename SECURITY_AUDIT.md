# セキュリティ監査レポート

**監査日**: 2026-02-12
**対象**: MediDocsLMreferral アプリケーション
**監査基準**: NIST, HIPAA, 医療情報システムの安全管理に関するガイドライン（厚労省）

---

## 1. 総合評価スコア
**[ 6.5 / 10 ]**

用途と運用環境を考慮すると、基本的なセキュリティ対策は実装されているが、医療情報システムとしていくつかの重要な改善点がある。

---

## 2. セキュリティ分析

### 強み（Strengths）
- **CSRF保護が適切に実装**: HMAC-SHA256署名 + タイムスタンプ方式で、`hmac.compare_digest`によるタイミング攻撃対策済み（`app/core/security.py:61`）
- **入出力データの非保存**: PostgreSQLにはプロンプトと統計情報のみ保存。患者の医療テキスト自体はDBに永続化されない設計
- **前処理による匿名化**: カルテ変換アプリで患者基本情報を除去してからAIに送信
- **ネットワーク分離**: Ericom Shield仮想ブラウザによる院内環境とインターネットの分離
- **Cloudflare IP制限**: 仮想ブラウザの固定IPによるアクセス制御 + Origin CA証明書
- **API Gatewayレート制限**: Cloudflare AI Gatewayで1時間200リクエスト制限
- **AWS Bedrock日本リージョン**: BAA締結済みでHIPAA対応、データが国内に留まる
- **Swagger UIの無効化**: 本番環境で`docs_url=None`に設定（`app/main.py:32`）
- **保護されたルーターの分離**: 生成・評価エンドポイントはCSRF必須の`protected_api_router`で保護（`app/api/router.py:15`）

### 懸念点・リスク（Weaknesses）

#### Critical（高リスク）
1. **ユーザー認証なし**: アプリケーション全体にログイン認証が存在しない。CSRFトークンはページ表示時に自動生成されるため、URLを知っている者は誰でもアクセス可能。IP制限が唯一の防壁
2. **admin_routerに認証なし**: プロンプト管理（CRUD）、設定変更、統計情報閲覧のエンドポイントがCSRF保護すらなく公開（`app/api/router.py:7-12`）
3. **CSRF秘密鍵のフォールバック**: `csrf_secret_key`未設定時にランダム生成されるが、サーバー再起動で全トークンが無効化される（`app/core/security.py:18-19`）。ワーカー複数台の場合、各プロセスで異なる鍵になりトークン検証が破綻する

#### High（中高リスク）
4. **CORSミドルウェア未設定**: CORSポリシーが明示的に設定されていない。FastAPIのデフォルトはCORS許可なしだが、明示設定がベストプラクティス
5. **セキュリティヘッダー未設定**: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy`等のレスポンスヘッダーが未実装
6. **アプリケーションレベルのレート制限なし**: Cloudflare AI Gatewayの制限はAI APIコールのみ。アプリのエンドポイント自体にレート制限がない
7. **監査ログ不在**: 誰がいつどの文書を生成したかの操作ログがない。医療情報システムのガイドラインでは操作記録が必須

#### Medium（中リスク）
8. **Vertex AI グローバルエンドポイント**: `google_location = "global"`がデフォルト（`app/core/config.py:38`）。データ処理の地理的所在が不明確で、日本の医療情報ガイドラインとの整合性に疑問
9. **Heroku Basicプラン**: Private Spacesではないため、共有インフラ上で動作。SOC2/HIPAA対応にはEnterprise/Shieldプランが必要
10. **入力サニタイゼーション不足**: XSS対策の明示的なサニタイゼーション処理が見当たらない。Jinja2のautoescapeに依存

---

## 3. カテゴリ別評価

| カテゴリ | スコア (1-10) | 理由 |
| :--- | :--- | :--- |
| **データ機密性 (Data Privacy)** | 7 | 入出力非保存・前処理匿名化は優秀。ただし匿名化の完全性担保やデータ残留リスク（メモリ/ログ）の考慮が不足 |
| **ネットワーク (Network Security)** | 7 | Cloudflare IP制限 + Origin CA + 仮想ブラウザ分離は堅実。セキュリティヘッダー・CORS明示設定・アプリレベルレート制限が未実装 |
| **認証・認可 (AuthN/AuthZ)** | 3 | ユーザー認証なし。CSRFトークンのみで、管理エンドポイントも無防備。医療システムとしては大きな欠陥 |
| **コンプライアンス (Compliance)** | 6 | AWS Bedrock BAA締結、入出力非保存は評価できる。監査ログ不在・Vertex AIのリージョン問題・Heroku共有インフラが減点要因 |
| **AIガバナンス (AI Governance)** | 7 | AI Gatewayレート制限、ログ非保存方針、自動モデル切替は良好。プロンプトインジェクション対策の明示的実装がない |

---

## 4. スコア向上のための推奨事項（優先度順）

### 1. ユーザー認証の導入（+1.5点見込み）
**優先度: 最高**

院内シングルサインオン（SAML/OIDC）またはBasic認証+IP制限の二重防御を実装。少なくとも管理エンドポイント（`admin_router`）にCSRF保護を追加し、できれば認証ミドルウェアを導入する。

**最低限の対応例**:
```python
# app/api/router.py
# admin_routerにもCSRF保護を追加
admin_router = APIRouter(dependencies=[Depends(require_csrf_token)])
```

**推奨実装**:
- FastAPI-Usersによるセッション管理
- またはHTTP Basic認証 + IP制限の二重防御
- または院内SSO（SAML 2.0 / OIDC）連携

### 2. セキュリティヘッダーの追加（+0.5点見込み）
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

### 3. 監査ログの実装（+0.5点見込み）
**優先度: 高**

医療情報システムの安全管理ガイドライン（厚労省）では操作記録が求められる。最低限、文書生成・評価実行・プロンプト変更の操作ログを記録する仕組みを追加。

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

### 4. Vertex AI リージョン指定（+0.3点見込み）
**優先度: 中**

`google_location`のデフォルトを`"global"`から`"asia-northeast1"`に変更し、データ処理が日本国内で完結するよう保証する。

```python
# app/core/config.py
google_location: str = "asia-northeast1"  # 日本リージョンに固定
```

### 5. 入力バリデーション・サニタイゼーション強化（+0.2点見込み）
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

---

## 5. 補足: 運用環境を考慮した総合見解

このアプリケーションは**Ericom Shield + Cloudflare IP制限**という外部防御に大きく依存しており、その前提が成立する限りにおいてはリスクが緩和されています。しかし「多層防御（Defense in Depth）」の観点からは、アプリケーション層の認証・認可が欠如していることが最大のリスクです。

仮想ブラウザやCloudflareの設定変更・障害時に、アプリケーション自体が無防備になる点は医療システムとして看過できません。

### アーキテクチャ面での評価
- **データプライバシー（前処理）**: 電子カルテ側での匿名化は評価できるが、アプリケーション側でその完全性を検証する仕組みがない
- **ネットワーク・エンドポイント保護**: IP制限 + Origin CA + 仮想ブラウザ分離は良好だが、アプリ自体のセキュリティヘッダー・CORS設定が未整備
- **AIガバナンス**: レート制限、ログ非保存方針は適切。プロンプトインジェクション対策の明示的実装があればさらに良い
- **インフラストラクチャ**: Heroku Basicプランは共有インフラのため、医療情報システムとしてはPrivate Spaces移行を検討すべき

### コンプライアンスチェックリスト

| 項目 | 対応状況 | 備考 |
| :--- | :--- | :--- |
| データの暗号化（通信） | ✅ | Cloudflare Origin CA証明書 |
| データの暗号化（保存） | ⚠️ | DBには医療データ非保存だが、明示的な暗号化設定なし |
| アクセス制御 | ❌ | ユーザー認証なし、IP制限のみ |
| 操作ログ（監査証跡） | ❌ | 未実装 |
| データ保管場所の明確化 | ⚠️ | AWS Bedrock(日本)は◎、Vertex AI(global)は△ |
| BAA締結 | ✅ | AWS Bedrockは締結済み |
| データ保持期間の管理 | ✅ | 入出力データは非保存 |

---

## 6. 今後の改善ロードマップ（推奨）

### Phase 1: 緊急対応（1-2週間）
1. `admin_router`にCSRF保護を追加
2. `csrf_secret_key`を環境変数で必須設定化
3. セキュリティヘッダーミドルウェアの追加

### Phase 2: 重要対応（1ヶ月）
4. 監査ログの実装（構造化ログ出力）
5. Vertex AI リージョンを`asia-northeast1`に変更
6. 入力サニタイゼーション処理の追加

### Phase 3: 中長期対応（3-6ヶ月）
7. ユーザー認証機能の導入（SSO連携またはBasic認証）
8. アプリケーションレベルのレート制限実装
9. Heroku Private Spacesへの移行検討
10. CORS設定の明示化
11. プロンプトインジェクション対策の実装

---

## 7. 参考資料
- [医療情報システムの安全管理に関するガイドライン 第6.0版（厚生労働省）](https://www.mhlw.go.jp/stf/shingi/0000516275_00006.html)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)

---

**監査担当者**: Claude Sonnet 4.5 (Security Audit Role)
**報告書バージョン**: 1.0
