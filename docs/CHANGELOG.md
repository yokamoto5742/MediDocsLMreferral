# Changelog

All notable changes to the MediDocsLM Referral Application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-21

### Added
- Initial stable release of MediDocsLM Referral Application
- Streamlit-based medical document generation interface
- Multi-AI provider support (Claude and Gemini)
- Automatic model switching based on input length (Claude → Gemini for inputs > 40,000 characters)
- PostgreSQL database integration for prompts, usage statistics, and settings
- Factory pattern implementation for AI provider management
- Hierarchical prompt system (Department → Doctor → Document Type)
- Usage tracking and statistics for all AI API calls
- Comprehensive test suite with 120 passing tests

### Changed
- Environment variable standardization from `GEMINI_CREDENTIALS` to `GOOGLE_CREDENTIALS_JSON`
- Text processing enhancements for better output formatting
- Error handling improvements across all API clients

## [Unreleased]

### Changed
- Updated `pyrightconfig.json` configuration
- Renamed test directories for better organization

### Removed
- Test strategy document file (migrated to separate documentation)

## [0.3.0] - 2025-09-19

### Changed
- **Environment Variable Standardization**: Replaced `GEMINI_CREDENTIALS` with `GOOGLE_CREDENTIALS_JSON` across entire codebase
  - Updated `utils/config.py`: Changed environment variable definition
  - Updated `services/summary_service.py`: Modified imports and credential validation
  - Updated `ui_components/navigation.py`: Changed imports and model availability checks
  - Updated `scripts/VertexAI_API.py`: Migrated to new credential variable

### Updated
- All test files to use new `GOOGLE_CREDENTIALS_JSON` credential variable
  - `tests/test_summary_service.py`: Updated mock patches
  - `tests/test_config.py`: Updated test assertions
  - `tests/conftest.py`: Updated test environment variables
- Documentation to reflect new credential format
  - `docs/README.md`: Updated environment variable examples

### Fixed
- Verified all 120 tests pass with new credential system

## [0.2.0] - 2025-01-16

### Added
- Vertex AI API integration for Gemini models
- Vertex AI configuration to `utils/config.py`
  - `GOOGLE_PROJECT_ID` environment variable
  - `GOOGLE_LOCATION` environment variable
- Vertex AI specific error messages to `utils/constants.py`
  - `GOOGLE_PROJECT_ID_MISSING`
  - `GOOGLE_LOCATION_MISSING`
  - `VERTEX_AI_INIT_ERROR`
  - `VERTEX_AI_API_ERROR`

### Changed
- **Gemini API Integration**: Migrated from Google AI to Vertex AI
  - Updated `external_service/gemini_api.py` to use Vertex AI API
  - Changed client initialization to use `vertexai=True` with project and location parameters
  - Enhanced error handling with Vertex AI specific error messages

### Updated
- Environment variable validation for `GOOGLE_PROJECT_ID` and `GOOGLE_LOCATION`

## [0.1.1] - 2025-01-16

### Fixed
- **Test Suite**: All 120 unit tests now pass successfully
- `utils/env_loader.py`: Fixed output messages to match test expectations
- `tests/test_prompt_manager.py`: Updated document type reference to match constants
- `tests/test_summary_service.py`: Fixed exception handling test for queue-based error handling

### Updated
- **Text Processing Enhancements** in `utils/text_processor.py`
  - `format_output_summary`: Added removal of `#` symbols and half-width spaces
  - `section_aliases`: Simplified mapping structure (removed complex brackets)
  - `parse_output_summary`: Complete rewrite to handle colon/no-colon patterns properly

### Changed
- Enhanced text processing functions for better output formatting
- Improved section parsing logic to handle multiple format variations

## [0.1.0] - 2025-01-15

### Added
- Initial project structure and architecture
- Core services and API client implementations
- Database models and schema
- Streamlit UI components
- Basic test coverage
- Environment configuration system

---

## Version History Summary

- **1.0.0** (2026-01-21): Stable release with comprehensive features and full test coverage
- **0.3.0** (2025-09-19): Environment variable standardization
- **0.2.0** (2025-01-16): Vertex AI integration
- **0.1.1** (2025-01-16): Test fixes and text processing updates
- **0.1.0** (2025-01-15): Initial release
