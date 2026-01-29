# フロントエンド移行ガイド

HTMLリファクタリングプロジェクトの実装が完了しました。現在は**フェーズ1-3（CDN版）**が動作しており、いつでも**フェーズ4（Vite版）**に切り替え可能です。

## 現在の状態

### ✅ 実装完了
- **フェーズ1**: Jinja2コンポーネント分割
- **フェーズ2**: マクロとCSSユーティリティクラス
- **フェーズ3**: Alpine.jsロジック移動
- **フェーズ4**: Vite + TypeScript + Tailwind環境構築

### 🔧 現在有効
- **CDN版**（フェーズ1-3）が本番稼働中
- `app/templates/base.html`でCDN版を読み込み

---

## Vite版への切り替え手順

### 前提条件

- Node.js v18以上
- npm（またはpnpm/yarn）
- 依存関係インストール済み（`frontend/node_modules/`存在）
- ビルド成果物生成済み（`app/static/dist/`存在）

### 手順1: ビルド成果物の確認

```bash
ls app/static/dist/
# 出力例:
# css/  js/
```

もしビルド成果物がない場合:

```bash
cd frontend
npm run build
```

### 手順2: base.htmlの切り替え

`app/templates/base.html`を編集:

#### CSS部分

**変更前（CDN版）:**
```html
<!-- フェーズ4: Vite版（本番用） - npm run buildでビルド後に有効化 -->
<!-- <link rel="stylesheet" href="/static/dist/css/main.css"> -->

<!-- フェーズ1-3: CDN版（現在有効） -->
<script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {
        darkMode: 'class'
    }
</script>
<link rel="stylesheet" href="/static/css/style.css">
<script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

**変更後（Vite版）:**
```html
<!-- フェーズ4: Vite版（本番用） -->
<link rel="stylesheet" href="/static/dist/css/main.css">

<!-- フェーズ1-3: CDN版 -->
<!-- <script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {
        darkMode: 'class'
    }
</script>
<link rel="stylesheet" href="/static/css/style.css">
<script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script> -->
```

#### JavaScript部分

**変更前（CDN版）:**
```html
<!-- フェーズ4: Vite版（本番用） - npm run buildでビルド後に有効化 -->
<!-- <script type="module" src="/static/dist/js/main.js"></script> -->

<!-- フェーズ1-3: 既存app.js（現在有効） -->
<script src="/static/js/app.js"></script>
```

**変更後（Vite版）:**
```html
<!-- フェーズ4: Vite版（本番用） -->
<script type="module" src="/static/dist/js/main.js"></script>

<!-- フェーズ1-3: 既存app.js -->
<!-- <script src="/static/js/app.js"></script> -->
```

### 手順3: アプリケーション再起動

```bash
uvicorn app.main:app --reload
```

### 手順4: 動作確認

ブラウザで http://localhost:8000 にアクセスして以下を確認:

- [ ] 入力画面が正しく表示される
- [ ] スタイルが適用されている（ボタン、フォーム等）
- [ ] カルテ情報を入力して「作成」ボタンをクリック
- [ ] 出力画面に遷移する
- [ ] タブ切り替えが動作する
- [ ] 「コピー」ボタンが動作する
- [ ] 「出力評価」ボタンが動作する
- [ ] 評価画面に遷移する
- [ ] ダークモードが動作する

---

## CDN版への戻し方

問題が発生した場合、すぐにCDN版に戻せます。

### base.htmlの再編集

上記の変更を逆にして、CDN版のコメントを外し、Vite版をコメントアウトします。

### アプリケーション再起動

```bash
uvicorn app.main:app --reload
```

---

## 開発フロー

### CDN版での開発（現在）

```bash
# FastAPIのみ起動
uvicorn app.main:app --reload
```

- テンプレート編集: `app/templates/`
- CSS編集: `app/static/css/style.css`
- JavaScript編集: `app/static/js/app.js`

### Vite版での開発（推奨）

```bash
# ターミナル1: FastAPI
uvicorn app.main:app --reload

# ターミナル2: Vite開発サーバー（HMR対応）
cd frontend
npm run dev
```

- TypeScript編集: `frontend/src/app.ts`
- スタイル編集: `frontend/src/styles/main.css`
- 型定義編集: `frontend/src/types.ts`
- テンプレート編集: `app/templates/`（Jinja2）

変更が即座にブラウザに反映されます（HMR）。

---

## トラブルシューティング

### スタイルが適用されない

**原因**: ビルド成果物が古い

**解決**:
```bash
cd frontend
npm run build
```

### JavaScriptエラー

**原因**: 型定義とランタイムの不一致

**解決**:
```bash
cd frontend
npm run typecheck
# エラーを修正後
npm run build
```

### Alpine.jsが動作しない

**原因**: CDN版とVite版の両方が読み込まれている

**解決**: `base.html`で片方のみ有効化されているか確認

---

## パフォーマンス比較

| 項目 | CDN版 | Vite版 |
|------|-------|--------|
| 初回ロード | Tailwind CDN + Alpine CDN | 最適化済みバンドル |
| ファイルサイズ | 未計測 | CSS 23KB, JS 50KB (gzip) |
| 開発体験 | 手動リロード | HMR対応 |
| 型安全性 | なし | TypeScript完全対応 |
| ビルド最適化 | なし | Tree-shaking, minify |

---

## メンテナンス

### 依存関係の更新

```bash
cd frontend
npm update
npm audit fix
```

### Tailwind設定変更

`frontend/tailwind.config.js`を編集後:

```bash
npm run build
```

### TypeScript設定変更

`frontend/tsconfig.json`を編集後:

```bash
npm run typecheck
npm run build
```

---

## 推奨事項

1. **段階的移行**: まずCDN版で十分にテストしてから、Vite版に切り替える
2. **本番環境**: Vite版を推奨（最適化済み、型安全）
3. **開発環境**: Vite開発サーバーを推奨（HMR対応）
4. **CI/CD**: ビルドステップに`npm run build`を追加
