# 変更履歴

診療情報提供書作成アプリのすべての重要な変更は、このファイルに記録されます。

このフォーマットは [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/spec/v2.0.0.html) に準拠しています。

## [Unreleased]

### 追加
- **APIキー認証機能**: `/api/*`配下のエンドポイントに`X-API-Key`ヘッダーによる認証を実装
  - `app/core/config.py`: `api_key`フィールドを追加
  - `app/core/security.py`: `verify_api_key`依存関数を実装
  - `app/api/router.py`: ルーターレベルで認証を適用
  - 環境変数`API_KEY`でキーを設定
  - `API_KEY`未設定時は認証をスキップ（開発モード）
  - `.env.example`: APIキー設定例を追加
  - `tests/core/test_security.py`: 認証関数のユニットテスト
  - `tests/api/test_api_authentication.py`: 統合テスト

## [1.5.2] - 2026-01-29

### リファクタリング
- **DRY原則の適用**: `app/services/summary_service.py`にエラーレスポンス生成ヘルパー関数`_error_response`を導入し、重複コードを削減
- **マジックストリング削除**: `app/core/constants.py`に`ModelType` Enumを追加し、"Claude"、"Gemini_Pro"などの文字列リテラルを統一
  - `app/services/summary_service.py`: `ModelType`と`APIProvider` Enumを使用
  - `app/schemas/summary.py`: デフォルト値を`ModelType.CLAUDE.value`に変更
  - `app/core/config.py`: `selected_ai_model`のデフォルト値を`ModelType.CLAUDE.value`に変更
  - `app/main.py`: `get_available_models`関数で`ModelType` Enumを使用
  - `app/api/summary.py`: `get_available_models`関数で`ModelType` Enumを使用
- **冗長コード削除**: `app/api/summary.py`の`generate_summary`エンドポイントで、`SummaryResponse`の冗長な再構築を削除
- **型ヒント追加**: `app/utils/text_processor.py`の`format_output_summary`と`parse_output_summary`関数に型ヒントを追加
- **ロジック集約**: モデル名取得ロジックを`app/services/prompt_service.py`の`get_selected_model`関数に集約
  - `app/services/summary_service.py`の`determine_model`関数で使用
  - `app/external/base_api.py`の`get_model_name`関数で使用
  - 重複していたデータベース呼び出しを統一

### 修正
- テストファイルの更新: リファクタリングに合わせてモックのパスとテストロジックを修正
  - `tests/api/test_settings.py`: `test_get_doctors_default_department`の期待値を修正
  - `tests/external/test_base_api.py`: `@patch`のパスを更新、`get_selected_model`を使用

## [1.5.1] - 2026-01-29

### 追加
- `package.json`: Alpine.jsをdependenciesに追加
- `package.json`: heroku-postbuildスクリプトに `--include=dev` オプションを追加
- `frontend/DEVELOPMENT.md`: フロントエンド開発ガイド（README.mdからリネーム）

### 変更
- `README.md`: プロジェクトルートに移動（docs/README.mdから）
- `app/templates/base.html`: Vite版を有効化、CDN版をコメントアウト
- `.claude/agents/readme-generator.md`: パス指定を修正（docs/README.md → README.md）
- `scripts/project_structure.txt`: プロジェクト構造と生成日時を更新

### 削除
- `docs/FRONTEND_MIGRATION.md`: フロントエンド移行ガイドを削除（情報統合済み）
- `app/static/js/app.js`: 未使用のJavaScriptファイルを削除（Vite版に統合済み）
- `app/static/css/style.css`: 未使用のCSSファイルを削除（Vite版に統合済み）

### リファクタリング
- フロントエンド関連ファイルをVite版に完全移行
- 開発関連ドキュメントを整理統合

## [1.5.0] - 2026-01-28

### 追加
- **フロントエンド環境構築**: Vite + TypeScript + Tailwind CSSのモダンなビルド環境を導入
  - `frontend/`: フロントエンド専用ディレクトリ作成
  - `frontend/src/types.ts`: バックエンドスキーマと対応する型定義
  - `frontend/src/app.ts`: 型安全なAlpine.jsアプリケーション
  - `frontend/src/main.ts`: エントリーポイント
  - `frontend/src/styles/main.css`: Tailwind CSS + カスタムスタイル（@apply使用）
  - `frontend/src/alpinejs.d.ts`: Alpine.js型定義
  - `frontend/vite.config.ts`: Vite設定（プロキシ、ビルド設定）
  - `frontend/tailwind.config.js`: Tailwind設定
  - `frontend/postcss.config.js`: PostCSS設定
  - `frontend/tsconfig.json`: TypeScript設定
  - `frontend/package.json`: フロントエンド依存関係管理
  - `frontend/README.md`: フロントエンドセットアップガイド
- **Jinja2コンポーネント**: 画面ごとの分割
  - `app/templates/components/input_screen.html`: 入力画面
  - `app/templates/components/output_screen.html`: 出力画面
  - `app/templates/components/evaluation_screen.html`: 評価画面
- **Jinja2マクロ**: 共通UIコンポーネント
  - `app/templates/macros.html`: テキストエリア、ボタン、アラートのマクロ
- **ヘルパー関数**: Alpine.jsロジック整理
  - `app/static/js/app.js`: `getCurrentTabContent()`, `copyCurrentTab()`, `isActiveTab()`, `getTabClass()`追加
- **ドキュメント**:
  - `html_refactoring_plan.md`: HTMLリファクタリング計画書
  - `FRONTEND_MIGRATION.md`: フロントエンド移行ガイド

### 変更
- `app/templates/index.html`: 187行→9行に削減（includeのみ）
- `app/static/css/style.css`: 共通CSSクラス追加（`.form-textarea`, `.btn-primary`等）
- `app/templates/base.html`: Vite版とCDN版の切り替えコメント追加
- `.gitignore`: フロントエンドビルド成果物を除外（`app/static/dist/`, `node_modules/`）

### リファクタリング
- **HTML整理**: Tailwind CSSクラスの重複を削減（10箇所以上→0）
- **ロジック分離**: HTML内の三項演算子をJavaScript関数に移動
- **型安全性**: TypeScriptによる型チェック導入

### 技術スタック更新
- TypeScript 5.3.0
- Vite 5.0.0
- Tailwind CSS 3.4.0
- Alpine.js 3.13.0（型定義追加）

### 備考
- CDN版（フェーズ1-3）が現在稼働中
- Vite版（フェーズ4）はビルド済み、いつでも切り替え可能
- HMR対応の開発環境が利用可能

## [1.4.0] - 2026-01-27

### 追加
- `app/models/prompt.py`: 型ヒントを追加
- `app/models/evaluation_prompt.py`: 型ヒントを追加
- `app/services/evaluation_service.py`: prompt_data.contentに型キャストを追加

### 変更
- `app/services/summary_service.py`: SummaryResultをSummaryResponseに置き換え
- `app/services/evaluation_service.py`: プロンプト構築の退院時処方を現在の処方に変更
- `docs/README.md`: APIクライアントアーキテクチャ、開発コマンド、型チェック（Pyright）、コントリビューションガイドを更新

### 修正
- `app/static/js/app.js`: コメントの表記ゆれを修正
- `tests/api/test_base_api.py`: 空文字列のテストケースを修正
- `tests/services/test_evaluation_service.py`: 退院時処方の表記を修正

### リファクタリング
- `tests/`: 不要な引数を削除し、テストを簡潔にする
- `app/utils/text_processor.py`, `app/utils/error_handlers.py`: 不要なコメントを削除

## [1.1.0] - 2026-01-23

### 修正
- すべての失敗していたユニットテストを修正（120のテスト全てがパス）
- `app/utils/text_processor.py`: テキスト処理機能を強化
  - `format_output_summary`: `#`記号と半角スペースの削除機能を追加
  - `section_aliases`: マッピング構造を簡素化（複雑な括弧を削除）
  - `parse_output_summary`: コロン/非コロンパターンを適切に処理するための完全な書き直し
- `app/utils/env_loader.py`: 出力メッセージをテスト期待値に合わせて修正
- `tests/test_prompt_manager.py`: 文書タイプ参照を定数に合わせて更新
- `tests/test_summary_service.py`: キューベースのエラー処理に対応した例外処理テストを修正

## [1.0.0] - 2026-01-21

### 追加
- 診療情報提供書作成アプリの初回安定版リリース
- 複数のAIプロバイダーサポート（ClaudeとGemini）
- 入力長に基づく自動モデル切り替え（40,000文字を超える入力の場合、Claude → Gemini）
- プロンプト、使用統計、設定のためのPostgreSQLデータベース統合
- AIプロバイダー管理のためのFactoryパターン実装
- 階層的プロンプトシステム（診療科 → 医師 → 文書タイプ）
- すべてのAI API呼び出しの使用状況追跡と統計
- より良い出力フォーマットのためのテキスト処理の強化
- すべてのAPIクライアントでのエラー処理の改善

---

## バージョン履歴

- **1.5.1** (2026-01-29): Vite版への完全移行、未使用ファイル削除、ドキュメント整理
- **1.5.0** (2026-01-28): Vite + TypeScript + Tailwind CSS導入、フロントエンド環境構築
- **1.4.0** (2026-01-27): 型ヒント追加、スキーマ最適化、ドキュメント更新
- **1.1.0** (2026-01-23): テスト修正とテキスト処理強化
- **1.0.0** (2026-01-21): 包括的な機能と完全なテストカバレッジを備えた安定版リリース