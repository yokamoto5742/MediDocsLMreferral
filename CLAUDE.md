# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返す。
- コードの変更範囲は最小限に抑える。
- コードの修正は直接適用する。
- Pythonのコーディング規約はPEP8に従います。
- KISSの原則に従い、できるだけシンプルなコードにします。
- 可読性を優先します。一度読んだだけで理解できるコードが最高のコードです。
- Pythonのコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## CHANGELOG
このプロジェクトにおけるすべての重要な変更は日本語でdcos/CHANGELOG.mdに記録します。
フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づきます。

## Automatic Notifications (Hooks)
自動通知は`.claude/settings.local.json` で設定済：
- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## クリーンコードガイドライン
- 関数のサイズ：関数は50行以下に抑えることを目標にしてください。関数の処理が多すぎる場合は、より小さな関数に分割してください。
- 単一責任：各関数とモジュールには明確な目的が1つあるようにします。無関係なロジックをまとめないでください。
- 命名：説明的な名前を使用してください。`tmp` 、`data`、`handleStuff`のような一般的な名前は避けてください。例えば、`doCalc`よりも`calculateInvoiceTotal` の方が適しています。
- DRY原則：コードを重複させないでください。類似のロジックが2箇所に存在する場合は、共有関数にリファクタリングしてください。それぞれに独自の実装が必要な場合はその理由を明確にしてください。
- コメント:分かりにくいロジックについては説明を加えます。説明不要のコードには過剰なコメントはつけないでください。
- コメントとdocstringは必要最小限に日本語で記述します。文末に"。"や"."をつけないでください。

## Project Overview

This is a FastAPI-based medical document generation system that uses AI (Claude/Gemini) to create standardized medical referral letters. The application supports multiple AI providers and automatically switches between them based on input length.

## Development Commands

### Running the Application

**Development mode with auto-reload:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing

**Run all tests:**
```bash
python -m pytest tests/ -v --tb=short
```

**Run with coverage:**
```bash
python -m pytest tests/ -v --tb=short --cov=app --cov-report=html
```

**Run specific test file:**
```bash
python -m pytest tests/services/test_summary_service.py -v
```

**Run specific test:**
```bash
python -m pytest tests/services/test_summary_service.py::test_generate_summary -v
```

### Type Checking

The project uses pyright for static type checking:
```bash
pyright
```

### Database Migrations

Alembic is configured for database migrations. Database tables are created automatically on startup, but you can also manage migrations:

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Architecture Overview

### Design Patterns

**Factory Pattern** (`app/external/api_factory.py`):
- `APIFactory.create_client()` dynamically instantiates the appropriate AI provider (Claude or Gemini)
- `generate_summary()` function uses the factory to select and invoke the correct API client

**Service Layer Pattern** (`app/services/`):
- Business logic is separated from API routes
- `summary_service.py`: Core document generation logic
- `prompt_service.py`: Hierarchical prompt template management
- `statistics_service.py`: Usage tracking and analytics
- `evaluation_service.py`: Document quality evaluation

**Repository Pattern** (`app/models/`):
- Database models using SQLAlchemy ORM
- `prompt.py`: Stores prompt templates with hierarchical inheritance
- `usage.py`: Tracks API usage, tokens, and costs
- `setting.py`: Application configuration
- `evaluation_prompt.py`: Evaluation criteria and templates

### Critical Business Logic

**Automatic Model Switching** (`app/services/summary_service.py:determine_model`):
- When input exceeds 40,000 characters and Claude is selected, automatically switches to Gemini
- Threshold is configurable via `MAX_TOKEN_THRESHOLD` environment variable
- If Gemini is not configured, raises an error instead of processing with Claude

**Hierarchical Prompt System** (`app/services/prompt_service.py`):
Prompts are resolved in order of specificity:
1. Doctor + Document Type specific prompt
2. Department + Document Type specific prompt
3. Document Type default prompt
4. Fallback to system default from `config.ini`

This allows flexible customization while maintaining defaults.

**Model Selection Priority**:
1. Explicit user selection in UI (highest priority)
2. Prompt-level model configuration (per department/doctor/document type)
3. Application default from environment variables

### Data Flow

1. User submits medical chart data via web interface
2. FastAPI endpoint receives and validates input
3. `SummaryService` orchestrates document generation:
   - Retrieves appropriate prompt template from database
   - Determines which AI model to use (with automatic switching)
   - Calls `APIFactory.generate_summary()` with provider-specific logic
4. AI generates structured medical document
5. `TextProcessor` parses output into sections
6. Usage statistics (tokens, time, cost) saved to PostgreSQL
7. Structured document returned to user interface

### API Integration Architecture

**Base API Pattern** (`app/external/base_api.py`):
- Abstract base class defining common interface for all AI providers
- Implements retry logic with exponential backoff using `tenacity`
- Standardized error handling across providers

**Claude Integration** (`app/external/claude_api.py`):
- Supports both direct Anthropic API and AWS Bedrock
- Uses `anthropic` SDK for direct API or `boto3` for Bedrock
- Automatically selects based on environment variables

**Gemini Integration** (`app/external/gemini_api.py`):
- Uses Google Cloud Vertex AI
- Supports Gemini Pro and Gemini Flash models
- Configurable thinking level for deeper reasoning

## Environment Configuration

Key environment variables you'll work with:

**Database:**
- `DATABASE_URL` or individual `POSTGRES_*` variables for connection
- Connection pooling configured via `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`

**AI Models:**
- `CLAUDE_API_KEY` + `CLAUDE_MODEL` for direct Anthropic API
- `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` + `ANTHROPIC_MODEL` for Bedrock
- `GOOGLE_CREDENTIALS_JSON` + `GOOGLE_PROJECT_ID` + `GEMINI_MODEL` for Vertex AI

**Thresholds:**
- `MAX_TOKEN_THRESHOLD=100000` (default) - triggers switch from Claude to Gemini
- `MAX_INPUT_TOKENS=200000` - absolute maximum input length

## Code Organization

```
app/
├── api/            # FastAPI route handlers (controllers in MVC)
├── core/           # Configuration, constants, database setup
├── external/       # AI provider integrations with factory pattern
├── models/         # SQLAlchemy ORM models (repository pattern)
├── schemas/        # Pydantic schemas for request/response validation
├── services/       # Business logic layer
├── utils/          # Utilities (text processing, error handling)
├── templates/      # Jinja2 HTML templates
└── main.py         # FastAPI application entry point

tests/              # Mirror structure of app/ with comprehensive coverage
├── api/            # Integration tests for endpoints
├── core/           # Configuration tests
├── external/       # AI provider mocking and integration tests
├── services/       # Business logic unit tests
└── test_utils/     # Utility function tests
```

## Testing Philosophy

The project maintains 120+ tests covering:
- **API endpoints**: Integration tests using FastAPI TestClient
- **Service layer**: Unit tests with mocked dependencies
- **External APIs**: Tests use mocking to avoid real API calls
- **Database operations**: Tests use session fixtures from `conftest.py`
- **Error handling**: Comprehensive exception and edge case coverage

When adding new features, maintain test coverage by:
1. Adding service layer tests first (TDD approach encouraged)
2. Adding API integration tests
3. Mocking external API calls using `pytest-mock`

## Common Development Patterns

**Adding a New AI Provider:**
1. Create new class in `app/external/` inheriting from `BaseAPI`
2. Implement `generate_summary()` method
3. Register in `APIProvider` enum in `api_factory.py`
4. Add factory logic in `APIFactory.create_client()`
5. Add configuration in `app/core/config.py`
6. Add tests in `tests/external/`

**Adding a New Document Type:**
1. Update `DOCUMENT_TYPES` constant in `app/core/constants.py`
2. Add default prompt in `config.ini` under `[PROMPTS]`
3. Update UI template dropdowns in `app/templates/`
4. Add any type-specific logic in `app/services/summary_service.py`

**Database Schema Changes:**
1. Modify model in `app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration in `alembic/versions/`
4. Apply migration: `alembic upgrade head`

## Important Constraints

**Token Limits:**
- Claude optimized for inputs under 40,000 characters (configurable)
- Gemini handles longer inputs but may be more expensive
- System enforces MAX_INPUT_TOKENS (200,000) absolute limit

**Database:**
- PostgreSQL required (not compatible with SQLite)
- Connection pooling configured for production workloads
- All database access goes through `get_db_session()` context manager

**Medical Context:**
- All AI-generated content requires review by qualified medical professionals
- This is an assistive tool, not a replacement for medical judgment
- Code should never bypass safety checks or validation

## Coding Standards

**Type Hints:**
- All functions must have type hints for parameters and return values
- Use `from typing import` imports for complex types
- Use `cast()` from typing when narrowing types

**Import Order:**
1. Standard library
2. Third-party packages (fastapi, sqlalchemy, etc.)
3. Local modules (app.*)
Each group alphabetically sorted.

**Commit Messages:**
- Follow conventional commit format when possible
- Include both Japanese and English descriptions where applicable
- Use emoji prefixes: ✨ feat, 🐛 fix, 📝 docs, ♻️ refactor, ✅ test

**Comments:**
- Minimal Japanese comments for unclear logic only
- No comments for self-explanatory code
- No periods at end of comments or docstrings
