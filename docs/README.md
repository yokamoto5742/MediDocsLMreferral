# MediDocsLM Referral

A FastAPI-based medical document generation application that uses multiple AI APIs (Claude and Gemini) to automatically generate medical referral documents from patient chart data.

## Overview

MediDocsLM Referral is an intelligent medical documentation system designed to streamline the creation of referral letters and medical reports. The application leverages advanced AI language models to parse patient chart information and generate structured medical documents according to customizable templates and prompts.

## Features

### Core Functionality
- **Multi-AI Provider Support**: Integrates with both Claude (Anthropic) and Gemini (Google Vertex AI)
- **Automatic Model Switching**: Intelligently switches from Claude to Gemini when input exceeds 40,000 characters
- **Structured Document Generation**: Generates medical documents with standardized sections:
  - Main diagnosis (主病名)
  - Referral purpose (紹介目的)
  - Medical history (既往歴)
  - Symptom progression (症状経過)
  - Treatment history (治療経過)
  - Current prescriptions (現在の処方)
  - Additional notes (備考)

### Document Management
- **Multiple Document Types**:
  - Referral to other institutions (他院への紹介)
  - Counter-referral to referring physician (紹介元への逆紹介)
  - Response letter (返書)
  - Final response letter (最終返書)
- **Department-Specific Customization**: Supports department-based configurations
- **Doctor-Specific Prompts**: Hierarchical prompt system (Department → Doctor → Document Type)

### Prompt Management
- **Custom Prompt Templates**: Create and manage custom prompts for different scenarios
- **Hierarchical Inheritance**: Department and doctor-specific prompt customization
- **Web-Based UI**: Easy-to-use interface for prompt creation and editing

### Analytics & Monitoring
- **Usage Statistics**: Track API usage, token consumption, and processing times
- **Performance Metrics**: Monitor response times and model performance
- **Cost Tracking**: Monitor API costs across different models

## Architecture Overview

### Design Patterns

**Factory Pattern**: `app/external/api_factory.py` manages AI provider instantiation
```python
# Dynamically creates appropriate API client based on model selection
api_client = get_api_client(model_name, api_key)
```

**Service Layer**: `app/services/` contains business logic separated from API routes
- `summary_service.py`: Document generation logic
- `prompt_service.py`: Prompt management
- `statistics_service.py`: Usage analytics

**Repository Pattern**: `app/models/` contains database models and data access
- `prompt.py`: Prompt templates
- `usage.py`: API usage statistics
- `setting.py`: Application settings

**MVC Architecture**:
- **Models**: SQLAlchemy ORM models in `app/models/`
- **Views**: Jinja2 templates in `app/templates/`
- **Controllers**: FastAPI routers in `app/api/`

### Data Flow

1. **User Input**: User enters chart data and selects document type via web interface
2. **Request Processing**: FastAPI endpoint receives and validates input
3. **Service Layer**: `SummaryService` coordinates document generation
4. **AI Integration**: Factory pattern instantiates appropriate API client
5. **Model Selection**: Auto-switches to Gemini if input exceeds Claude's optimal range
6. **Document Generation**: AI generates structured medical document
7. **Post-Processing**: Text processor parses output into sections
8. **Database Logging**: Usage statistics and metadata stored in PostgreSQL
9. **Response**: Structured document returned to user interface

### Key Components

```
app/
├── api/            # FastAPI route handlers
│   ├── router.py   # Main API router
│   ├── summary.py  # Document generation endpoints
│   ├── prompts.py  # Prompt management endpoints
│   ├── statistics.py  # Analytics endpoints
│   └── settings.py    # Settings endpoints
├── core/           # Core configuration
│   ├── config.py   # Environment settings
│   ├── constants.py  # Application constants
│   └── database.py   # Database connection
├── external/       # External API integrations
│   ├── api_factory.py  # API client factory
│   ├── base_api.py     # Base API client
│   ├── claude_api.py   # Claude/Bedrock integration
│   └── gemini_api.py   # Gemini/Vertex AI integration
├── models/         # Database models
│   ├── prompt.py   # Prompt templates
│   ├── usage.py    # Usage statistics
│   └── setting.py  # Application settings
├── schemas/        # Pydantic schemas
│   ├── summary.py  # Request/response schemas
│   ├── prompt.py   # Prompt schemas
│   └── statistics.py  # Statistics schemas
├── services/       # Business logic
│   ├── summary_service.py  # Document generation
│   ├── prompt_service.py   # Prompt management
│   └── statistics_service.py  # Analytics
├── utils/          # Utility functions
│   ├── text_processor.py  # Text parsing
│   ├── exceptions.py      # Custom exceptions
│   └── error_handlers.py  # Error handling
└── main.py         # FastAPI application
```

## Setup and Installation

### Prerequisites

- Python 3.13+
- PostgreSQL 12+
- At least one AI API account:
  - Claude API (Anthropic) or AWS Bedrock access
  - Google Cloud Platform account with Vertex AI enabled

### Installation Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd MediDocsLMreferral
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL database**
```bash
# Create database
createdb medidocs

# Database tables will be created automatically on first run
```

5. **Configure environment variables**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
```

6. **Run database migrations** (if applicable)
```bash
# Tables are auto-created via SQLAlchemy on startup
```

## Environment Variables Configuration

Create a `.env` file in the project root with the following variables:

### Database Configuration
```env
# PostgreSQL Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=medidocs
POSTGRES_SSL=false

# Connection Pool Settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Heroku Database URL (optional, overrides individual settings)
DATABASE_URL=postgresql://user:password@host:port/database
```

### Claude API Configuration

**Option 1: Direct Claude API**
```env
CLAUDE_API_KEY=sk-ant-your-api-key
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

**Option 2: AWS Bedrock**
```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-northeast-1
ANTHROPIC_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Google Vertex AI Configuration
```env
# Google Cloud Credentials (JSON format)
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project",...}

# Or path to credentials file
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Vertex AI Settings
GOOGLE_PROJECT_ID=your-gcp-project-id
GOOGLE_LOCATION=asia-northeast1
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_THINKING_LEVEL=HIGH
```

### Application Settings
```env
# Token Limits
MAX_INPUT_TOKENS=200000
MIN_INPUT_TOKENS=100
MAX_TOKEN_THRESHOLD=100000

# Features
PROMPT_MANAGEMENT=true
APP_TYPE=default
SELECTED_AI_MODEL=Claude
```

### Example .env File
```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=medidocs
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=medidocs_db

# Claude API
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# Google Vertex AI
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"my-gcp-project"}
GOOGLE_PROJECT_ID=my-gcp-project
GOOGLE_LOCATION=asia-northeast1
GEMINI_MODEL=gemini-2.0-flash-exp

# Application
MAX_INPUT_TOKENS=200000
PROMPT_MANAGEMENT=true
```

## Usage Instructions

### Starting the Application

**Development Mode:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### Using the Web Interface

1. **Access the main page**: Navigate to `http://localhost:8000`
2. **Enter patient information**:
   - Select department and doctor
   - Choose document type
   - Enter chart data in the text area
   - Add any additional information
3. **Select AI model**: Choose between Claude or Gemini (or let auto-switching handle it)
4. **Generate document**: Click the generate button
5. **Review output**: Generated document appears in structured sections
6. **Copy to clipboard**: Use Ctrl+A and Ctrl+C to copy the generated text

### Managing Prompts

1. Navigate to the **Prompts** page
2. **Create new prompt**:
   - Select department, doctor, and document type
   - Enter custom prompt template
   - Save the prompt
3. **Edit existing prompts**: Click edit icon next to any prompt
4. **Delete prompts**: Click delete icon (requires confirmation)

### Viewing Statistics

1. Navigate to the **Statistics** page
2. Select date range for analytics
3. View metrics:
   - Total API calls
   - Token usage by model
   - Average processing time
   - Cost breakdown
4. Export data for further analysis

### API Usage

**Generate Document via API:**
```bash
curl -X POST "http://localhost:8000/api/summary/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "chart_data": "患者情報とカルテデータ",
    "additional_info": "追加情報",
    "department": "眼科",
    "doctor": "橋本義弘",
    "document_type": "他院への紹介",
    "model_name": "Claude"
  }'
```

**Get Usage Statistics:**
```bash
curl -X GET "http://localhost:8000/api/statistics?start_date=2026-01-01&end_date=2026-01-21"
```

## Testing

### Running Tests

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

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── api/                     # API endpoint tests
│   ├── test_prompts.py
│   ├── test_summary.py
│   ├── test_statistics.py
│   └── test_settings.py
├── core/                    # Core functionality tests
│   └── test_config.py
├── external/                # External API tests
│   ├── test_api_factory.py
│   ├── test_base_api.py
│   ├── test_claude_api.py
│   └── test_gemini_api.py
├── services/                # Business logic tests
│   ├── test_prompt_service.py
│   ├── test_summary_service.py
│   └── test_statistics_service.py
└── test_utils/              # Utility tests
    └── test_text_processor.py
```

### Test Coverage

The project maintains comprehensive test coverage with 120+ tests covering:
- API endpoints
- Service layer logic
- External API integrations
- Database operations
- Text processing utilities
- Error handling

## Project Structure

```
MediDocsLMreferral/
├── .claude/                 # Claude Code configuration
├── .git/                    # Git repository
├── .venv/                   # Python virtual environment
├── app/                     # Main application code
│   ├── api/                 # API route handlers
│   ├── core/                # Core configuration
│   ├── external/            # External API clients
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── static/              # Static files (CSS, JS)
│   ├── templates/           # Jinja2 HTML templates
│   ├── utils/               # Utility functions
│   └── main.py              # FastAPI application
├── docs/                    # Documentation
│   ├── CHANGELOG.md         # Version history
│   ├── LICENSE              # License information
│   └── README.md            # This file
├── scripts/                 # Utility scripts
├── tests/                   # Test suite
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment file
├── .gitignore               # Git ignore rules
├── CLAUDE.md                # Claude Code instructions
├── config.ini               # Configuration file
├── Procfile                 # Heroku deployment
├── pyrightconfig.json       # Pyright type checker config
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Python dependencies
└── setup.sh                 # Setup script
```

## Technologies Used

### Backend Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for FastAPI
- **Pydantic**: Data validation using Python type annotations
- **SQLAlchemy**: SQL toolkit and ORM

### Database
- **PostgreSQL**: Primary database for storing prompts, settings, and usage data
- **psycopg2-binary**: PostgreSQL adapter for Python

### AI/ML Integration
- **Anthropic SDK**: Claude API integration
- **Google Generative AI**: Gemini API integration
- **Google Cloud AI Platform**: Vertex AI integration
- **boto3**: AWS SDK for Bedrock integration

### Frontend
- **Jinja2**: Template engine for HTML rendering
- **HTML/CSS/JavaScript**: Frontend technologies

### Testing
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking library for tests

### Development Tools
- **python-dotenv**: Environment variable management
- **pyright**: Static type checker for Python
- **uv**: Fast Python package installer

### Additional Libraries
- **httpx**: HTTP client for API calls
- **tenacity**: Retry library for API resilience
- **pydantic-settings**: Settings management
- **python-multipart**: Multipart form data parsing

## Key Business Logic

### Automatic Model Switching

The application intelligently switches between AI models based on input length:

```python
# If input exceeds 40,000 characters and Claude is selected
if input_length > 40000 and selected_model == "Claude":
    # Switch to Gemini for better handling of long inputs
    switch_to_model("Gemini_Pro")
```

### Hierarchical Prompt System

Prompts are resolved in order of specificity:
1. Doctor + Document Type specific prompt
2. Department + Document Type specific prompt
3. Default prompt for Document Type

This allows for flexible customization while maintaining fallback defaults.

### Usage Tracking

Every API call is logged with:
- Model used
- Token counts (input/output)
- Processing time
- Timestamp
- Department/Doctor/Document Type context

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Import order: Standard library → Third-party → Local modules
- Keep imports alphabetically sorted

### Commit Messages
- Use descriptive commit messages
- Follow conventional commit format when possible
- Include both Japanese and English descriptions if applicable

## License

[Specify your license here]

## Support

For issues, questions, or contributions, please refer to the project repository.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and updates.

## Security Notes

- Never commit `.env` files containing credentials
- Rotate API keys regularly
- Use environment variables for all sensitive configuration
- Keep dependencies up to date for security patches
- Review AI-generated content before use in production medical settings

## Medical Disclaimer

This application uses generative AI to create medical documents. All AI-generated content must be reviewed and verified by qualified medical professionals before use. The application is a tool to assist with documentation and should not replace professional medical judgment.

---

**Note**: This README is based on the current codebase structure. For the most up-to-date development guidelines, refer to [CLAUDE.md](../CLAUDE.md).
