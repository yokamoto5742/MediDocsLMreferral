# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返すこと。Return patch diffs, not prose.
- 不明な点がある場合は、トレードオフを明記した2つの選択肢を提案すること（80語以内）。
- 変更範囲は最小限に抑えること
- Pythonコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## Automatic Notifications (Hooks)
自動通知は`.claude/settings.local.json` で設定済：

- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## Development Commands

### Running the Application
```bash
streamlit run app.py
```
Application runs on http://localhost:8501

### Testing
```bash
# Run all tests
python -m pytest tests/ -v --tb=short

# Run tests with coverage
python -m pytest tests/ -v --tb=short --disable-warnings

# Run specific test file
python -m pytest tests/services/test_summary_service.py -v
```

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Update requirements (if using uv)
uv add <package_name>
```

## Changelog

### 2025-09-19 - Environment Variable Standardization
- **Refactored**: Replaced `GEMINI_CREDENTIALS` with `GOOGLE_CREDENTIALS_JSON` across codebase
  - `utils/config.py`: Updated environment variable definition
  - `services/summary_service.py`: Updated imports and credential validation
  - `ui_components/navigation.py`: Updated imports and model availability checks
  - `scripts/VertexAI_API.py`: Updated to use new credential variable
- **Updated**: All test files to use new credential variable
  - `tests/test_summary_service.py`: Updated mock patches
  - `tests/test_config.py`: Updated test assertions
  - `tests/conftest.py`: Updated test environment variables
- **Updated**: Documentation to reflect new credential format
  - `docs/README.md`: Updated environment variable example
- **Verified**: All 120 tests pass with new credential system

### 2025-01-16 - Test Code Fixes & Text Processing Updates
- **Fixed**: All failing unit tests (120 tests now pass)
- **Updated**: `utils/text_processor.py` - Enhanced text processing functions
  - `format_output_summary`: Added removal of `#` symbols and half-width spaces
  - `section_aliases`: Simplified mapping structure (removed complex brackets)
  - `parse_output_summary`: Complete rewrite to handle colon/no-colon patterns properly
- **Updated**: `utils/env_loader.py` - Fixed output messages to match test expectations
- **Fixed**: Test files to align with actual implementation behavior
  - `tests/test_prompt_manager.py`: Updated document type reference to match constants
  - `tests/test_summary_service.py`: Fixed exception handling test for queue-based error handling

### 2025-01-16 - Vertex AI Integration
- **Updated**: `external_service/gemini_api.py` to use Vertex AI API instead of Google AI
  - Changed client initialization to use `vertexai=True` with project and location parameters
  - Added environment variable validation for `GOOGLE_PROJECT_ID` and `GOOGLE_LOCATION`
  - Enhanced error handling with Vertex AI specific error messages
- **Added**: Vertex AI configuration to `utils/config.py`
  - `GOOGLE_PROJECT_ID` and `GOOGLE_LOCATION` environment variables
- **Added**: Vertex AI error messages to `utils/constants.py`
  - `GOOGLE_PROJECT_ID_MISSING`, `GOOGLE_LOCATION_MISSING`
  - `VERTEX_AI_INIT_ERROR`, `VERTEX_AI_API_ERROR`

## Architecture Overview

### Core Structure
This is a **Streamlit-based medical document generation app** that uses multiple AI APIs (Claude, Gemini) to generate medical referral documents from patient chart data.

**Key architectural patterns:**
- **Factory Pattern**: `external_service/api_factory.py` manages AI provider instantiation
- **Service Layer**: `services/summary_service.py` handles business logic for document generation
- **Repository Pattern**: `database/` contains models and data access logic
- **View Components**: Streamlit pages in `views/` with reusable UI components in `ui_components/`

### Data Flow
1. **Input**: User enters chart data, additional info, and selects AI model in Streamlit UI
2. **Processing**: `SummaryService` coordinates with API clients via factory pattern
3. **AI Integration**: Auto-switches between models based on input length (Claude → Gemini for large inputs)
4. **Output**: Generated document parsed into structured sections (main disease, treatment history, etc.)
5. **Storage**: Usage statistics and prompts stored in PostgreSQL

### External Dependencies
- **AI APIs**: Claude (Anthropic), Gemini (Google) - at least one required
- **Database**: PostgreSQL for prompts, usage stats, and app settings
- **Web Framework**: Streamlit for the UI

### Configuration Management
- **Environment**: `.env` file with API keys and database settings
- **Constants**: `utils/constants.py` for departments, doctors, document types
- **User Settings**: Saved to database via `ui_components/navigation.py`

### Key Business Logic
- **Auto Model Switching**: Switches from Claude to Gemini when input exceeds 40,000 characters
- **Hierarchical Prompts**: Department → Doctor → Document Type specific prompt inheritance
- **Usage Tracking**: All AI API calls logged with token counts and timing data

### Database Schema
- `prompts`: Custom prompts by department/doctor/document type
- `summary_usage`: API usage statistics and timing
- `app_settings`: User preferences and settings

## Important Implementation Notes

### Adding New AI Providers
1. Create new client in `external_service/` inheriting from `BaseAPIClient`
2. Register in `api_factory.py`
3. Add environment variables and model constants

### Customizing Departments/Doctors
Edit `utils/constants.py`:
- `DEFAULT_DEPARTMENT`: Available departments
- `DEPARTMENT_DOCTORS_MAPPING`: Doctor assignments per department
- `DOCUMENT_TYPES`: Available document types

### Testing Structure
Tests are organized by module:
- `tests/services/`: Business logic tests
- `tests/utils/`: Utility function tests
- Use `pytest-mock` for API mocking in tests