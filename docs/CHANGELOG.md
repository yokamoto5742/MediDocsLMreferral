# 変更履歴

診療情報提供書作成アプリのすべての重要な変更は、このファイルに記録されます。

このフォーマットは [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/spec/v2.0.0.html) に準拠しています。

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

- **1.4.0** (2026-01-27): 型ヒント追加、スキーマ最適化、ドキュメント更新
- **1.1.0** (2026-01-23): テスト修正とテキスト処理強化
- **1.0.0** (2026-01-21): 包括的な機能と完全なテストカバレッジを備えた安定版リリース