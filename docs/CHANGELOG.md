# 変更履歴

診療情報提供書作成アプリのすべての重要な変更は、このファイルに記録されます。

このフォーマットは [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/spec/v2.0.0.html) に準拠しています。

## [1.1.0] - 2026-01-23

### 変更
- **環境変数の標準化**: `GEMINI_CREDENTIALS`を`GOOGLE_CREDENTIALS_JSON`にリファクタリング
  - `app/core/config.py`: 環境変数定義を更新
  - `app/services/summary_service.py`: インポートと認証情報検証を更新
  - すべてのテストファイルを新しい認証情報変数に更新（`tests/test_summary_service.py`, `tests/test_config.py`, `tests/conftest.py`）
  - ドキュメント（`docs/README.md`）を新しい認証情報形式に更新
- **Vertex AI統合**: Google AI Studio APIからVertex AI APIへ移行
  - `app/external/gemini_api.py`: プロジェクトとロケーションパラメータで`vertexai=True`を使用するようにクライアント初期化を変更
  - `GOOGLE_PROJECT_ID`と`GOOGLE_LOCATION`の環境変数検証を追加
  - Vertex AI固有のエラーメッセージでエラー処理を強化
  - `app/core/config.py`: `GOOGLE_PROJECT_ID`と`GOOGLE_LOCATION`環境変数を追加
  - `app/core/constants.py`: Vertex AIエラーメッセージ（`GOOGLE_PROJECT_ID_MISSING`, `GOOGLE_LOCATION_MISSING`, `VERTEX_AI_INIT_ERROR`, `VERTEX_AI_API_ERROR`）を追加

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

- **1.1.0** (2026-01-23): Vertex AI統合、環境変数標準化、テスト修正とテキスト処理強化
- **1.0.0** (2026-01-21): 包括的な機能と完全なテストカバレッジを備えた安定版リリース