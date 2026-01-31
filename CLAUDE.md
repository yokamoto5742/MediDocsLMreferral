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

**MediDocsLMreferral** is a FastAPI-based medical document generation application that uses Claude (AWS Bedrock/API) and Gemini (Vertex AI) to create structured referral letters (診療情報提供書). The app features automatic model switching, hierarchical prompt management, and usage statistics tracking.

## Essential Commands

### Backend Development

```bash
# Start development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v --tb=short

# Run with coverage
python -m pytest tests/ -v --tb=short --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/services/test_summary_service.py -v

# Run specific test
python -m pytest tests/services/test_summary_service.py::test_generate_summary -v

# Type checking
pyright
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Development server (port 5173, proxies to :8000)
npm run dev

# Type check
npm run typecheck

# Production build (outputs to ../app/static/dist/)
npm run build
```

## Architecture and Key Patterns

### Factory Pattern for AI Provider Management

The `APIFactory` in `app/external/api_factory.py` dynamically instantiates Claude or Gemini clients:

```python
from app.external.api_factory import APIFactory, APIProvider

client = APIFactory.create_client(APIProvider.CLAUDE)
result = client.generate_summary(medical_text, additional_info, ...)
```

### Service Layer Pattern

Business logic is separated from API routes in `app/services/`:

- **`summary_service.py`**: Document generation orchestration, automatic model switching logic
- **`prompt_service.py`**: Hierarchical prompt resolution (doctor → department → document type → default)
- **`evaluation_service.py`**: AI-based output evaluation
- **`statistics_service.py`**: Usage metrics and statistics

### Automatic Model Switching

Implemented in `summary_service.py::determine_model()`:
- Monitors input character count against `MAX_TOKEN_THRESHOLD` (default 100,000)
- Automatically switches from Claude to Gemini when threshold is exceeded
- Raises error if Gemini credentials are not configured
- Model name retrieval is centralized in `prompt_service.py::get_selected_model()`

### Hierarchical Prompt System

Prompts are resolved in specificity order (`prompt_service.py`):
1. Doctor + document type specific prompt
2. Department + document type specific prompt
3. Document type default prompt
4. System default from `config.ini`

This allows department-specific and doctor-specific customizations to override defaults.

### Constants Management

`app/core/constants.py` centralizes all magic strings:
- `ModelType` Enum: "Claude", "Gemini_Pro"
- `APIProvider` Enum: CLAUDE, GEMINI
- Department/doctor mappings
- Document types and section names
- User-facing messages

Always use these constants instead of string literals.

### API Authentication

API key authentication (`app/core/security.py::verify_api_key`):
- Configured via `MEDIDOCS_API_KEY` environment variable
- If unset: authentication is skipped (development mode)
- If set: requires `X-API-Key` header for `/api/*` public endpoints
- Admin routes (prompts, statistics, settings) accessible via Web UI without auth
- Public API routes (summary generation, evaluation) require authentication

## Project Structure

```
app/
├── api/                    # FastAPI route handlers
│   ├── router.py           # Main router (admin + public API separation)
│   ├── summary.py          # Document generation endpoints
│   ├── prompts.py          # Prompt management endpoints
│   ├── evaluation.py       # Output evaluation endpoints
│   ├── statistics.py       # Statistics endpoints
│   └── settings.py         # Settings endpoints
├── core/                   # Core configuration
│   ├── config.py           # Environment settings (Settings class)
│   ├── constants.py        # Application constants and Enums
│   ├── database.py         # Database connection
│   └── security.py         # API key authentication
├── external/               # External API integrations
│   ├── api_factory.py      # API client factory (Factory pattern)
│   ├── base_api.py         # Base API client
│   ├── claude_api.py       # Claude/Bedrock integration
│   └── gemini_api.py       # Gemini/Vertex AI integration
├── models/                 # SQLAlchemy ORM models
│   ├── prompt.py           # Prompt templates
│   ├── evaluation_prompt.py # Evaluation prompts
│   ├── usage.py            # Usage statistics
│   └── setting.py          # Application settings
├── schemas/                # Pydantic schemas (request/response)
├── services/               # Business logic layer
├── utils/                  # Utility functions
│   ├── text_processor.py   # Text parsing and formatting
│   ├── exceptions.py       # Custom exceptions
│   └── error_handlers.py   # Error handling
├── templates/              # Jinja2 templates
└── main.py                 # FastAPI application entry point

frontend/                   # Vite + TypeScript + Tailwind CSS
├── src/
│   ├── main.ts             # Entry point
│   ├── app.ts              # Alpine.js application logic
│   ├── types.ts            # TypeScript type definitions
│   └── styles/main.css     # Tailwind CSS + custom styles

tests/                      # Test suite (120+ tests)
├── conftest.py             # Shared fixtures
├── api/                    # API endpoint tests
├── core/                   # Core functionality tests
├── external/               # External API tests (mocked)
├── services/               # Business logic tests
└── test_utils/             # Utility tests
```

## Data Flow

1. User submits medical record data via Web UI
2. FastAPI endpoint receives and validates input
3. `SummaryService` orchestrates document generation
4. Factory pattern instantiates appropriate API client
5. Auto model selection based on input length
6. AI generates structured medical document
7. Text processor parses output into sections
8. Usage statistics (tokens, time, cost) saved to PostgreSQL
9. Structured document returned to UI

## Code Style Guidelines

- **Python**: PEP 8 compliant
- **Type hints**: All functions must have parameter and return type hints
- **Imports**: stdlib → third-party → local, alphabetically sorted (imports first, then from imports)
- **Function size**: Target ≤50 lines
- **Comments**: Japanese only for complex logic, no trailing period
- **Constants**: Use `constants.py` Enums instead of magic strings
- **Commit format**: Conventional commits with emoji prefixes (`✨ feat`, `🐛 fix`, `📝 docs`, `♻️ refactor`, `✅ test`)

## Testing Strategy

Test order when adding new features:
1. Write service layer tests first (TDD recommended)
2. Add API integration tests
3. Add external API tests with mocks if needed (use `pytest-mock`)

Tests are organized by layer:
- **API tests**: Endpoint and request/response validation
- **Service tests**: Business logic unit tests
- **External tests**: Provider integration with mocks
- **DB tests**: ORM and database operations
- **Utils tests**: Text processing and error handling

## Environment Configuration

Key environment variables (`.env`):

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=medidocs

# Claude API (AWS Bedrock recommended)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-northeast-1
ANTHROPIC_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0

# Gemini (Vertex AI)
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
GOOGLE_PROJECT_ID=your-gcp-project-id
GOOGLE_LOCATION=asia-northeast1
GEMINI_MODEL=gemini-2.0-flash

# Authentication
MEDIDOCS_API_KEY=your_api_key_here  # Optional, skips auth if unset

# Application
MAX_TOKEN_THRESHOLD=100000
SELECTED_AI_MODEL=Claude
```

## Frontend Development

Frontend uses **Vite + TypeScript + Tailwind CSS + Alpine.js**:

- **Entry point**: `frontend/src/main.ts`
- **Alpine.js logic**: `frontend/src/app.ts` (typed)
- **Type definitions**: `frontend/src/types.ts` (sync with Pydantic schemas)
- **Styles**: `frontend/src/styles/main.css` (use `@apply` for custom classes)
- **Build output**: `app/static/dist/`
- **Dev server**: Port 5173 with proxy to backend `:8000`

Workflow:
1. Add typed methods to `app.ts`
2. Add type definitions to `types.ts`
3. Reference in Jinja2 templates (`app/templates/`)
4. Run `npm run typecheck` regularly

## Common Tasks

### Adding a New AI Provider

1. Create client in `app/external/` extending `BaseAPI`
2. Add provider to `APIProvider` enum in `api_factory.py`
3. Update factory's `create_client()` method
4. Add configuration to `app/core/config.py`
5. Add tests in `tests/external/`

### Adding a New Document Type

1. Add to `DOCUMENT_TYPES` in `app/core/constants.py`
2. Add purpose mapping in `DOCUMENT_TYPE_TO_PURPOSE_MAPPING`
3. Create default prompt in database or `config.ini`
4. Update frontend type definitions in `frontend/src/types.ts`

### Modifying Prompt Resolution

Edit `app/services/prompt_service.py` - the hierarchical resolution logic is centralized in `get_prompt()`.

## Important Notes

- Tables are auto-created on first run via SQLAlchemy
- Use Alembic for schema changes in production
- Always mock external API calls in tests
- Frontend and backend type definitions should be kept in sync
- Review all AI-generated medical content before clinical use (disclaimer applies)
