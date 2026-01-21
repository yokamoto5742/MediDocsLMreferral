# 変更履歴

MediDocsLM Referralアプリケーションのすべての重要な変更は、このファイルに記録されます。

このフォーマットは [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/spec/v2.0.0.html) に準拠しています。

## [1.0.0] - 2026-01-21

### 追加
- MediDocsLM Referralアプリケーションの初回安定版リリース
- Streamlitベースの医療文書生成インターフェース
- 複数のAIプロバイダーサポート（ClaudeとGemini）
- 入力長に基づく自動モデル切り替え（40,000文字を超える入力の場合、Claude → Gemini）
- プロンプト、使用統計、設定のためのPostgreSQLデータベース統合
- AIプロバイダー管理のためのFactoryパターン実装
- 階層的プロンプトシステム（診療科 → 医師 → 文書タイプ）
- すべてのAI API呼び出しの使用状況追跡と統計
- 120のテストに合格する包括的なテストスイート

### 変更
- 環境変数を `GEMINI_CREDENTIALS` から `GOOGLE_CREDENTIALS_JSON` に標準化
- より良い出力フォーマットのためのテキスト処理の強化
- すべてのAPIクライアントでのエラー処理の改善

## [未リリース]

### 変更
- `pyrightconfig.json` 構成を更新
- より良い整理のためにテストディレクトリの名前を変更

### 削除
- テスト戦略ドキュメントファイル（別ドキュメントに移行）

## [0.3.0] - 2025-09-19

### 変更
- **環境変数の標準化**: コードベース全体で `GEMINI_CREDENTIALS` を `GOOGLE_CREDENTIALS_JSON` に置換
  - `utils/config.py` を更新: 環境変数定義を変更
  - `services/summary_service.py` を更新: インポートと認証情報検証を変更
  - `ui_components/navigation.py` を更新: インポートとモデル可用性チェックを変更
  - `scripts/VertexAI_API.py` を更新: 新しい認証情報変数に移行

### 更新
- すべてのテストファイルを新しい `GOOGLE_CREDENTIALS_JSON` 認証情報変数を使用するように更新
  - `tests/test_summary_service.py`: モックパッチを更新
  - `tests/test_config.py`: テストアサーションを更新
  - `tests/conftest.py`: テスト環境変数を更新
- 新しい認証情報形式を反映するようにドキュメントを更新
  - `docs/README.md`: 環境変数の例を更新

### 修正
- 新しい認証情報システムですべての120テストが合格することを確認

## [0.2.0] - 2025-01-16

### 追加
- GeminiモデルのためのVertex AI API統合
- `utils/config.py` へのVertex AI設定
  - `GOOGLE_PROJECT_ID` 環境変数
  - `GOOGLE_LOCATION` 環境変数
- `utils/constants.py` へのVertex AI固有のエラーメッセージ
  - `GOOGLE_PROJECT_ID_MISSING`
  - `GOOGLE_LOCATION_MISSING`
  - `VERTEX_AI_INIT_ERROR`
  - `VERTEX_AI_API_ERROR`

### 変更
- **Gemini API統合**: Google AIからVertex AIへ移行
  - `external_service/gemini_api.py` をVertex AI APIを使用するように更新
  - クライアント初期化をプロジェクトとロケーションパラメータで `vertexai=True` を使用するように変更
  - Vertex AI固有のエラーメッセージでエラー処理を強化

### 更新
- `GOOGLE_PROJECT_ID` と `GOOGLE_LOCATION` の環境変数検証

## [0.1.1] - 2025-01-16

### 修正
- **テストスイート**: すべての120ユニットテストが成功
- `utils/env_loader.py`: テスト期待値に合わせて出力メッセージを修正
- `tests/test_prompt_manager.py`: 定数に一致するように文書タイプ参照を更新
- `tests/test_summary_service.py`: キューベースのエラー処理のための例外処理テストを修正

### 更新
- `utils/text_processor.py` での**テキスト処理の強化**
  - `format_output_summary`: `#` 記号と半角スペースの除去を追加
  - `section_aliases`: マッピング構造を簡素化（複雑な括弧を削除）
  - `parse_output_summary`: コロン/コロンなしパターンを適切に処理するための完全な書き直し

### 変更
- より良い出力フォーマットのためにテキスト処理関数を強化
- 複数のフォーマットバリエーションを処理するためにセクション解析ロジックを改善

## [0.1.0] - 2025-01-15

### 追加
- 初期プロジェクト構造とアーキテクチャ
- コアサービスとAPIクライアント実装
- データベースモデルとスキーマ
- Streamlit UIコンポーネント
- 基本的なテストカバレッジ
- 環境設定システム

---

## バージョン履歴サマリー

- **1.0.0** (2026-01-21): 包括的な機能と完全なテストカバレッジを備えた安定版リリース
- **0.3.0** (2025-09-19): 環境変数の標準化
- **0.2.0** (2025-01-16): Vertex AI統合
- **0.1.1** (2025-01-16): テスト修正とテキスト処理の更新
- **0.1.0** (2025-01-15): 初回リリース
