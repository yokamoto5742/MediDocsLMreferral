# Migration Plan: Streamlit → FastAPI シングルアプリケーション

## 概要

医療文書生成アプリを Streamlit から **FastAPI + Jinja2 テンプレート** のシングルアプリケーションに移行する。
Heroku での運用を継続し、1つのプロジェクト・1つのデプロイ単位で管理する。

---

## 現在のアーキテクチャ

```
現在 (Streamlit)
├── app.py                    # Streamlit エントリーポイント
├── views/                    # Streamlit ページ
├── ui_components/            # Streamlit UI コンポーネント
├── services/                 # ビジネスロジック
├── external_service/         # AI API (Claude/Gemini)
├── database/                 # PostgreSQL + SQLAlchemy
├── utils/                    # 設定・定数・ユーティリティ
└── tests/                    # テスト
```

---

## 新アーキテクチャ（シングルアプリケーション）

```
medidocs/
├── app/
│   ├── main.py                    # FastAPI エントリーポイント
│   ├── core/
│   │   ├── config.py              # 設定管理 (pydantic-settings)
│   │   ├── constants.py           # 定数・日本語メッセージ
│   │   └── database.py            # DB 接続（同期 SQLAlchemy）
│   ├── models/
│   │   ├── base.py                # SQLAlchemy Base
│   │   ├── prompt.py              # Prompt モデル
│   │   ├── usage.py               # SummaryUsage モデル
│   │   └── setting.py             # AppSetting モデル
│   ├── schemas/                   # Pydantic スキーマ
│   │   ├── summary.py             # 文書生成リクエスト/レスポンス
│   │   ├── prompt.py              # プロンプト CRUD
│   │   └── settings.py            # 設定
│   ├── api/
│   │   ├── router.py              # メインルーター
│   │   ├── summary.py             # 文書生成 API
│   │   ├── prompts.py             # プロンプト管理 API
│   │   ├── statistics.py          # 統計 API
│   │   └── settings.py            # 設定 API
│   ├── services/
│   │   ├── summary_service.py     # 文書生成ロジック
│   │   ├── prompt_service.py      # プロンプト管理ロジック
│   │   └── statistics_service.py  # 統計ロジック
│   ├── external/
│   │   ├── base_api.py            # 抽象クライアント
│   │   ├── claude_api.py          # Claude (AWS Bedrock)
│   │   ├── gemini_api.py          # Gemini (Vertex AI)
│   │   └── api_factory.py         # ファクトリパターン
│   ├── utils/
│   │   ├── text_processor.py      # テキスト処理
│   │   ├── exceptions.py          # カスタム例外
│   │   └── error_handlers.py      # エラーハンドラ
│   ├── templates/                 # Jinja2 テンプレート
│   │   ├── base.html              # ベーステンプレート
│   │   ├── index.html             # メインページ
│   │   ├── prompts.html           # プロンプト管理
│   │   ├── statistics.html        # 統計ページ
│   │   └── components/            # 再利用可能コンポーネント
│   │       ├── sidebar.html
│   │       ├── summary_form.html
│   │       └── summary_result.html
│   └── static/
│       ├── css/
│       │   └── style.css          # TailwindCSS (CDN or build)
│       └── js/
│           └── app.js             # htmx + Alpine.js
├── tests/
│   ├── conftest.py
│   ├── test_api/                  # API テスト
│   ├── test_services/             # サービステスト
│   └── test_utils/                # ユーティリティテスト
├── .env
├── requirements.txt
├── Procfile
└── README.md
```

---

## 技術スタック

| レイヤー | 現在 | 移行後 |
|---------|------|--------|
| Web フレームワーク | Streamlit | FastAPI |
| テンプレート | - | Jinja2 |
| フロントエンド連携 | Streamlit 組み込み | htmx + Alpine.js |
| CSS | Streamlit 組み込み | TailwindCSS (CDN) |
| データベース | PostgreSQL + SQLAlchemy (同期) | 同左（変更なし） |
| AI API | Claude / Gemini | 同左（変更なし） |
| デプロイ | Heroku (Streamlit) | Heroku (Uvicorn) |

**htmx + Alpine.js を選択する理由:**
- SPA に近いインタラクティブ性を実現
- ビルドステップ不要（CDN 読み込み）
- シングルアプリケーションとして管理しやすい
- Streamlit の UI 挙動（リアルタイム更新、フォーム操作）を再現可能

---

## 実行ステップ

### Phase 1: プロジェクト基盤構築（Day 1-2）

#### Step 1.1: 依存関係更新

```bash
# requirements.txt に追加
fastapi==0.115.0
uvicorn[standard]==0.32.0
jinja2==3.1.6
python-multipart==0.0.18
# 既存の依存関係は維持
```

**確認コマンド:**
```bash
pip install -r requirements.txt
```

#### Step 1.2: ディレクトリ構造作成

```bash
mkdir -p app/{core,models,schemas,api,services,external,utils,templates/components,static/{css,js}}
touch app/__init__.py app/core/__init__.py app/models/__init__.py \
      app/schemas/__init__.py app/api/__init__.py app/services/__init__.py \
      app/external/__init__.py app/utils/__init__.py
```

#### Step 1.3: 設定管理移行

**ファイル:** `app/core/config.py`

現在の `utils/config.py` を pydantic-settings ベースに移行:

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_db: str = "medidocs"
    postgres_ssl: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    database_url: str | None = None  # Heroku DATABASE_URL

    # AWS Bedrock (Claude)
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "ap-northeast-1"
    anthropic_model: str | None = None
    claude_api_key: str | None = None
    claude_model: str | None = None

    # Google Vertex AI (Gemini)
    google_credentials_json: str | None = None
    gemini_model: str | None = None
    google_project_id: str | None = None
    google_location: str = "global"
    gemini_thinking_level: str = "HIGH"

    # Application
    max_input_tokens: int = 200000
    min_input_tokens: int = 100
    max_token_threshold: int = 100000
    prompt_management: bool = True
    app_type: str = "default"
    selected_ai_model: str = "Claude"

    def get_database_url(self) -> str:
        """Heroku DATABASE_URL または個別設定から接続URLを構築"""
        if self.database_url:
            url = self.database_url
            # Heroku postgres:// → postgresql:// 変換
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        ssl_param = "?sslmode=require" if self.postgres_ssl else ""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}{ssl_param}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**確認方法:**
```python
from app.core.config import get_settings
settings = get_settings()
print(settings.get_database_url())
```

#### Step 1.4: 定数移行

**ファイル:** `app/core/constants.py`

現在の `utils/constants.py` をそのままコピー。追加で UI メッセージを定義:

```python
# 既存の定数をそのまま移行 + 以下を追加

# UI Messages
MESSAGES = {
    "NO_INPUT": "カルテ情報を入力してください",
    "INPUT_TOO_SHORT": "入力文字数が少なすぎます",
    "COPY_INSTRUCTION": "上記テキストボックスをクリックしてCtrl+Aで全選択、Ctrl+Cでコピーできます",
    "PROCESSING_TIME": "処理時間",
    "MODEL_SWITCHED": "入力が長いため、モデルを {} に自動切替しました",
    "API_ERROR": "API エラーが発生しました",
    "GENERATING": "生成中...",
    "AI_DISCLAIMER": "生成AIは不正確な場合があります。回答をカルテでご確認ください。",
}

TAB_NAMES = [
    "全文",
    "【主病名】",
    "【紹介目的】",
    "【既往歴】",
    "【症状経過】",
    "【治療経過】",
    "【現在の処方】",
    "【備考】",
]
```

#### Step 1.5: データベース層移行

**ファイル:** `app/core/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from .config import get_settings

settings = get_settings()

engine = create_engine(
    settings.get_database_url(),
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """FastAPI Depends 用"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """サービス層用コンテキストマネージャ"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

#### Step 1.6: モデル移行

**ファイル:** `app/models/base.py`
```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

**ファイル:** `app/models/prompt.py`
```python
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from .base import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True)
    department = Column(String(100), nullable=False)
    document_type = Column(String(100), nullable=False)
    doctor = Column(String(100), nullable=False)
    content = Column(Text)
    selected_model = Column(String(50))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**ファイル:** `app/models/usage.py`
```python
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .base import Base


class SummaryUsage(Base):
    __tablename__ = "summary_usage"

    id = Column(Integer, primary_key=True)
    department = Column(String(100))
    doctor = Column(String(100))
    document_type = Column(String(100))
    model = Column(String(50))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    processing_time = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**ファイル:** `app/models/setting.py`
```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .base import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(String(500))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Phase 1 完了確認:**
```bash
python -c "from app.core.config import get_settings; print(get_settings().app_type)"
python -c "from app.core.database import engine; print(engine.url)"
python -c "from app.models.prompt import Prompt; print(Prompt.__tablename__)"
```

---

### Phase 2: 外部 API 連携移行（Day 2-3）

#### Step 2.1: ベース API クライアント

**ファイル:** `app/external/base_api.py`

現在の `external_service/base_api.py` をそのまま移行（同期版を維持）。

```python
# external_service/base_api.py の内容をコピー
# インポートパスのみ変更: utils.* → app.utils.*
```

#### Step 2.2: Claude API クライアント

**ファイル:** `app/external/claude_api.py`

現在の `external_service/claude_api.py` をそのまま移行。

```python
# external_service/claude_api.py の内容をコピー
# インポートパスのみ変更
```

#### Step 2.3: Gemini API クライアント

**ファイル:** `app/external/gemini_api.py`

現在の `external_service/gemini_api.py` をそのまま移行。

```python
# external_service/gemini_api.py の内容をコピー
# インポートパスのみ変更
```

#### Step 2.4: API ファクトリ

**ファイル:** `app/external/api_factory.py`

```python
# external_service/api_factory.py の内容をコピー
# インポートパスのみ変更
```

**Phase 2 完了確認:**
```bash
python -c "from app.external.api_factory import APIFactory; print(APIFactory)"
```

---

### Phase 3: サービス層移行（Day 3-4）

#### Step 3.1: サマリサービス

**ファイル:** `app/services/summary_service.py`

現在の `services/summary_service.py` から UI 関連コード（Streamlit st.* 呼び出し）を除去し、純粋なビジネスロジックのみを抽出:

```python
from dataclasses import dataclass
from datetime import datetime
import time
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.database import get_db_session
from app.external.api_factory import APIFactory, generate_summary
from app.models.usage import SummaryUsage
from app.utils.text_processor import format_output_summary, parse_output_summary

JST = ZoneInfo("Asia/Tokyo")
settings = get_settings()


@dataclass
class SummaryResult:
    success: bool
    output_summary: str
    parsed_summary: dict[str, str]
    input_tokens: int
    output_tokens: int
    processing_time: float
    model_used: str
    model_switched: bool
    error_message: str | None = None


def validate_input(medical_text: str) -> tuple[bool, str | None]:
    """入力検証"""
    if not medical_text or not medical_text.strip():
        return False, "カルテ情報を入力してください"
    if len(medical_text) < settings.min_input_tokens:
        return False, "入力文字数が少なすぎます"
    if len(medical_text) > settings.max_input_tokens:
        return False, f"入力文字数が{settings.max_input_tokens}を超えています"
    return True, None


def determine_model(requested_model: str, input_length: int) -> tuple[str, bool]:
    """モデル自動切替判定"""
    if input_length > settings.max_token_threshold and requested_model == "Claude":
        return "Gemini_Pro", True
    return requested_model, False


def execute_summary_generation(
    medical_text: str,
    additional_info: str,
    referral_purpose: str,
    current_prescription: str,
    department: str,
    doctor: str,
    document_type: str,
    model: str,
) -> SummaryResult:
    """文書生成を実行"""
    # 入力検証
    is_valid, error_msg = validate_input(medical_text)
    if not is_valid:
        return SummaryResult(
            success=False,
            output_summary="",
            parsed_summary={},
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            model_used=model,
            model_switched=False,
            error_message=error_msg,
        )

    # モデル決定
    final_model, model_switched = determine_model(model, len(medical_text))

    # AI API 呼び出し
    start_time = time.time()
    try:
        output_summary, input_tokens, output_tokens = generate_summary(
            medical_text=medical_text,
            additional_info=additional_info,
            referral_purpose=referral_purpose,
            current_prescription=current_prescription,
            department=department,
            document_type=document_type,
            doctor=doctor,
            model=final_model,
        )
    except Exception as e:
        return SummaryResult(
            success=False,
            output_summary="",
            parsed_summary={},
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            model_used=final_model,
            model_switched=model_switched,
            error_message=str(e),
        )

    processing_time = time.time() - start_time

    # 出力フォーマット
    formatted_summary = format_output_summary(output_summary)
    parsed_summary = parse_output_summary(formatted_summary)

    # 使用統計保存
    save_usage(
        department=department,
        doctor=doctor,
        document_type=document_type,
        model=final_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        processing_time=processing_time,
    )

    return SummaryResult(
        success=True,
        output_summary=formatted_summary,
        parsed_summary=parsed_summary,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        processing_time=processing_time,
        model_used=final_model,
        model_switched=model_switched,
    )


def save_usage(
    department: str,
    doctor: str,
    document_type: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    processing_time: float,
) -> None:
    """使用統計をDBに保存"""
    with get_db_session() as db:
        usage = SummaryUsage(
            department=department,
            doctor=doctor,
            document_type=document_type,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            processing_time=processing_time,
        )
        db.add(usage)
```

#### Step 3.2: プロンプトサービス

**ファイル:** `app/services/prompt_service.py`

```python
from sqlalchemy.orm import Session
from app.models.prompt import Prompt


def get_all_prompts(db: Session) -> list[Prompt]:
    return db.query(Prompt).all()


def get_prompt(
    db: Session,
    department: str,
    document_type: str,
    doctor: str,
) -> Prompt | None:
    return db.query(Prompt).filter(
        Prompt.department == department,
        Prompt.document_type == document_type,
        Prompt.doctor == doctor,
    ).first()


def create_or_update_prompt(
    db: Session,
    department: str,
    document_type: str,
    doctor: str,
    content: str,
    selected_model: str | None = None,
) -> Prompt:
    existing = get_prompt(db, department, document_type, doctor)
    if existing:
        existing.content = content
        existing.selected_model = selected_model
        return existing
    new_prompt = Prompt(
        department=department,
        document_type=document_type,
        doctor=doctor,
        content=content,
        selected_model=selected_model,
    )
    db.add(new_prompt)
    return new_prompt


def delete_prompt(db: Session, prompt_id: int) -> bool:
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if prompt:
        db.delete(prompt)
        return True
    return False
```

#### Step 3.3: 統計サービス

**ファイル:** `app/services/statistics_service.py`

```python
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.usage import SummaryUsage


def get_usage_summary(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
) -> dict:
    query = db.query(SummaryUsage)
    if start_date:
        query = query.filter(SummaryUsage.created_at >= start_date)
    if end_date:
        query = query.filter(SummaryUsage.created_at <= end_date)
    if model:
        query = query.filter(SummaryUsage.model == model)

    total_count = query.count()
    total_input = query.with_entities(func.sum(SummaryUsage.input_tokens)).scalar() or 0
    total_output = query.with_entities(func.sum(SummaryUsage.output_tokens)).scalar() or 0
    avg_time = query.with_entities(func.avg(SummaryUsage.processing_time)).scalar() or 0

    return {
        "total_count": total_count,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "average_processing_time": round(avg_time, 2),
    }


def get_usage_records(
    db: Session,
    limit: int = 100,
    offset: int = 0,
) -> list[SummaryUsage]:
    return (
        db.query(SummaryUsage)
        .order_by(SummaryUsage.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
```

**Phase 3 完了確認:**
```bash
python -c "from app.services.summary_service import SummaryResult; print(SummaryResult)"
```

---

### Phase 4: Pydantic スキーマ定義（Day 4）

#### Step 4.1: サマリスキーマ

**ファイル:** `app/schemas/summary.py`

```python
from pydantic import BaseModel, Field


class SummaryRequest(BaseModel):
    referral_purpose: str = ""
    current_prescription: str = ""
    medical_text: str = Field(..., min_length=1)
    additional_info: str = ""
    department: str = "default"
    doctor: str = "default"
    document_type: str = "他院への紹介"
    model: str = "Claude"


class SummaryResponse(BaseModel):
    success: bool
    output_summary: str
    parsed_summary: dict[str, str]
    input_tokens: int
    output_tokens: int
    processing_time: float
    model_used: str
    model_switched: bool
    error_message: str | None = None
```

#### Step 4.2: プロンプトスキーマ

**ファイル:** `app/schemas/prompt.py`

```python
from datetime import datetime
from pydantic import BaseModel


class PromptBase(BaseModel):
    department: str
    document_type: str
    doctor: str
    content: str
    selected_model: str | None = None


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    content: str | None = None
    selected_model: str | None = None


class PromptResponse(PromptBase):
    id: int
    is_default: bool
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True
```

#### Step 4.3: 統計スキーマ

**ファイル:** `app/schemas/statistics.py`

```python
from datetime import datetime
from pydantic import BaseModel


class UsageSummary(BaseModel):
    total_count: int
    total_input_tokens: int
    total_output_tokens: int
    average_processing_time: float


class UsageRecord(BaseModel):
    id: int
    department: str | None
    doctor: str | None
    document_type: str | None
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    processing_time: float | None
    created_at: datetime | None

    class Config:
        from_attributes = True
```

---

### Phase 5: API エンドポイント実装（Day 4-5）

#### Step 5.1: サマリ API

**ファイル:** `app/api/summary.py`

```python
from fastapi import APIRouter, BackgroundTasks
from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.summary_service import execute_summary_generation
from app.core.config import get_settings

router = APIRouter(prefix="/summary", tags=["summary"])
settings = get_settings()


@router.post("/generate", response_model=SummaryResponse)
def generate_summary(request: SummaryRequest):
    result = execute_summary_generation(
        medical_text=request.medical_text,
        additional_info=request.additional_info,
        referral_purpose=request.referral_purpose,
        current_prescription=request.current_prescription,
        department=request.department,
        doctor=request.doctor,
        document_type=request.document_type,
        model=request.model,
    )
    return SummaryResponse(
        success=result.success,
        output_summary=result.output_summary,
        parsed_summary=result.parsed_summary,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        processing_time=result.processing_time,
        model_used=result.model_used,
        model_switched=result.model_switched,
        error_message=result.error_message,
    )


@router.get("/models")
def get_available_models():
    models = []
    if settings.anthropic_model or settings.claude_model:
        models.append("Claude")
    if settings.gemini_model:
        models.append("Gemini_Pro")
    return {
        "available_models": models,
        "default_model": models[0] if models else None,
    }
```

#### Step 5.2: プロンプト API

**ファイル:** `app/api/prompts.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse
from app.services import prompt_service

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("/", response_model=list[PromptResponse])
def list_prompts(db: Session = Depends(get_db)):
    return prompt_service.get_all_prompts(db)


@router.post("/", response_model=PromptResponse)
def create_prompt(prompt: PromptCreate, db: Session = Depends(get_db)):
    result = prompt_service.create_or_update_prompt(
        db,
        department=prompt.department,
        document_type=prompt.document_type,
        doctor=prompt.doctor,
        content=prompt.content,
        selected_model=prompt.selected_model,
    )
    db.commit()
    db.refresh(result)
    return result


@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    if not prompt_service.delete_prompt(db, prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    db.commit()
    return {"status": "deleted"}
```

#### Step 5.3: 統計 API

**ファイル:** `app/api/statistics.py`

```python
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.statistics import UsageSummary, UsageRecord
from app.services import statistics_service

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/summary", response_model=UsageSummary)
def get_summary(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
    db: Session = Depends(get_db),
):
    return statistics_service.get_usage_summary(db, start_date, end_date, model)


@router.get("/records", response_model=list[UsageRecord])
def get_records(
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return statistics_service.get_usage_records(db, limit, offset)
```

#### Step 5.4: 設定 API

**ファイル:** `app/api/settings.py`

```python
from fastapi import APIRouter
from app.core.constants import DEFAULT_DEPARTMENT, DEPARTMENT_DOCTORS_MAPPING, DOCUMENT_TYPES

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/departments")
def get_departments():
    return {"departments": DEFAULT_DEPARTMENT}


@router.get("/doctors/{department}")
def get_doctors(department: str):
    doctors = DEPARTMENT_DOCTORS_MAPPING.get(department, ["default"])
    return {"doctors": doctors}


@router.get("/document-types")
def get_document_types():
    return {"document_types": DOCUMENT_TYPES}
```

#### Step 5.5: メインルーター

**ファイル:** `app/api/router.py`

```python
from fastapi import APIRouter
from app.api import summary, prompts, statistics, settings

api_router = APIRouter()
api_router.include_router(summary.router)
api_router.include_router(prompts.router)
api_router.include_router(statistics.router)
api_router.include_router(settings.router)
```

---

### Phase 6: テンプレート・静的ファイル（Day 5-6）

#### Step 6.1: ベーステンプレート

**ファイル:** `app/templates/base.html`

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}診療情報提供書作成{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body class="bg-gray-50" x-data="appState()">
    <div class="flex h-screen">
        {% include "components/sidebar.html" %}
        <main class="flex-1 overflow-auto p-6">
            {% block content %}{% endblock %}
        </main>
    </div>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

#### Step 6.2: サイドバー

**ファイル:** `app/templates/components/sidebar.html`

```html
<aside class="w-64 bg-white shadow-lg p-4 flex flex-col">
    <h1 class="text-xl font-bold text-gray-800 mb-6">診療情報提供書作成</h1>

    <div class="space-y-4 flex-1">
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">診療科</label>
            <select x-model="settings.department" @change="updateDoctors()"
                    class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500">
                {% for dept in departments %}
                <option value="{{ dept }}">{{ '全科共通' if dept == 'default' else dept }}</option>
                {% endfor %}
            </select>
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">医師名</label>
            <select x-model="settings.doctor"
                    class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500">
                <template x-for="doc in doctors" :key="doc">
                    <option :value="doc" x-text="doc === 'default' ? '医師共通' : doc"></option>
                </template>
            </select>
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">文書名</label>
            <select x-model="settings.documentType"
                    class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500">
                {% for type in document_types %}
                <option value="{{ type }}">{{ type }}</option>
                {% endfor %}
            </select>
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">AIモデル</label>
            <select x-model="settings.model"
                    class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500">
                {% for model in available_models %}
                <option value="{{ model }}">{{ model }}</option>
                {% endfor %}
            </select>
        </div>
    </div>

    <nav class="mt-6 space-y-2">
        <a href="/" class="block p-2 rounded hover:bg-gray-100 {{ 'bg-blue-50 text-blue-600' if active_page == 'index' else '' }}">
            文書作成
        </a>
        <a href="/prompts" class="block p-2 rounded hover:bg-gray-100 {{ 'bg-blue-50 text-blue-600' if active_page == 'prompts' else '' }}">
            プロンプト管理
        </a>
        <a href="/statistics" class="block p-2 rounded hover:bg-gray-100 {{ 'bg-blue-50 text-blue-600' if active_page == 'statistics' else '' }}">
            統計情報
        </a>
    </nav>

    <p class="mt-6 text-xs text-gray-500">
        生成AIは不正確な場合があります。回答をカルテでご確認ください。
    </p>
</aside>
```

#### Step 6.3: メインページ

**ファイル:** `app/templates/index.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="max-w-4xl">
    <form @submit.prevent="generateSummary()" class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">紹介目的</label>
            <textarea x-model="form.referralPurpose" rows="3"
                class="w-full border border-gray-300 rounded-md p-3 focus:ring-2 focus:ring-blue-500"></textarea>
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">現在の処方</label>
            <textarea x-model="form.currentPrescription" rows="3"
                class="w-full border border-gray-300 rounded-md p-3 focus:ring-2 focus:ring-blue-500"></textarea>
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">カルテ記載</label>
            <textarea x-model="form.medicalText" rows="8"
                class="w-full border border-gray-300 rounded-md p-3 focus:ring-2 focus:ring-blue-500"></textarea>
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">追加情報</label>
            <textarea x-model="form.additionalInfo" rows="3"
                class="w-full border border-gray-300 rounded-md p-3 focus:ring-2 focus:ring-blue-500"></textarea>
        </div>

        <div class="flex gap-4">
            <button type="submit" :disabled="isGenerating"
                class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
                <span x-show="!isGenerating">作成</span>
                <span x-show="isGenerating">生成中...</span>
            </button>
            <button type="button" @click="clearForm()"
                class="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-100">
                テキストをクリア
            </button>
        </div>
    </form>

    <!-- 結果表示 -->
    <div x-show="result.outputSummary" x-cloak class="mt-8">
        <div x-show="result.modelSwitched" class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
            入力が長いため、モデルを <span x-text="result.modelUsed"></span> に自動切替しました
        </div>

        <!-- タブ -->
        <div class="border-b border-gray-200">
            <nav class="flex -mb-px">
                <template x-for="(tab, index) in tabs" :key="tab">
                    <button @click="activeTab = index"
                        :class="activeTab === index ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
                        class="px-4 py-2 border-b-2 font-medium text-sm"
                        x-text="tab">
                    </button>
                </template>
            </nav>
        </div>

        <!-- タブコンテンツ -->
        <div class="mt-4 p-4 bg-white border rounded-md">
            <pre x-show="activeTab === 0" class="whitespace-pre-wrap font-mono text-sm" x-text="result.outputSummary"></pre>
            <template x-for="(tab, index) in tabs.slice(1)" :key="tab">
                <pre x-show="activeTab === index + 1" class="whitespace-pre-wrap font-mono text-sm"
                     x-text="result.parsedSummary[tab] || ''"></pre>
            </template>
        </div>

        <p x-show="result.processingTime" class="mt-2 text-sm text-gray-500">
            処理時間: <span x-text="result.processingTime.toFixed(2)"></span>秒
        </p>
    </div>

    <!-- エラー表示 -->
    <div x-show="error" x-cloak class="mt-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
        <span x-text="error"></span>
    </div>
</div>
{% endblock %}
```

#### Step 6.4: JavaScript（Alpine.js 状態管理）

**ファイル:** `app/static/js/app.js`

```javascript
function appState() {
    return {
        // Settings
        settings: {
            department: 'default',
            doctor: 'default',
            documentType: '他院への紹介',
            model: 'Claude'
        },
        doctors: ['default'],

        // Form
        form: {
            referralPurpose: '',
            currentPrescription: '',
            medicalText: '',
            additionalInfo: ''
        },

        // Result
        result: {
            outputSummary: '',
            parsedSummary: {},
            processingTime: null,
            modelUsed: '',
            modelSwitched: false
        },

        // UI state
        isGenerating: false,
        error: null,
        activeTab: 0,
        tabs: ['全文', '【主病名】', '【紹介目的】', '【既往歴】', '【症状経過】', '【治療経過】', '【現在の処方】', '【備考】'],

        async init() {
            await this.updateDoctors();
        },

        async updateDoctors() {
            const response = await fetch(`/api/settings/doctors/${this.settings.department}`);
            const data = await response.json();
            this.doctors = data.doctors;
            if (!this.doctors.includes(this.settings.doctor)) {
                this.settings.doctor = this.doctors[0];
            }
        },

        async generateSummary() {
            if (!this.form.medicalText.trim()) {
                this.error = 'カルテ情報を入力してください';
                return;
            }

            this.isGenerating = true;
            this.error = null;

            try {
                const response = await fetch('/api/summary/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        referral_purpose: this.form.referralPurpose,
                        current_prescription: this.form.currentPrescription,
                        medical_text: this.form.medicalText,
                        additional_info: this.form.additionalInfo,
                        department: this.settings.department,
                        doctor: this.settings.doctor,
                        document_type: this.settings.documentType,
                        model: this.settings.model
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.result = {
                        outputSummary: data.output_summary,
                        parsedSummary: data.parsed_summary,
                        processingTime: data.processing_time,
                        modelUsed: data.model_used,
                        modelSwitched: data.model_switched
                    };
                    this.activeTab = 0;
                } else {
                    this.error = data.error_message || 'エラーが発生しました';
                }
            } catch (e) {
                this.error = 'API エラーが発生しました';
            } finally {
                this.isGenerating = false;
            }
        },

        clearForm() {
            this.form = {
                referralPurpose: '',
                currentPrescription: '',
                medicalText: '',
                additionalInfo: ''
            };
            this.result = {
                outputSummary: '',
                parsedSummary: {},
                processingTime: null,
                modelUsed: '',
                modelSwitched: false
            };
            this.error = null;
        }
    };
}
```

#### Step 6.5: CSS

**ファイル:** `app/static/css/style.css`

```css
[x-cloak] {
    display: none !important;
}

/* カスタムスタイル（必要に応じて追加） */
pre {
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}
```

---

### Phase 7: FastAPI メインアプリケーション（Day 6）

#### Step 7.1: メインアプリケーション

**ファイル:** `app/main.py`

```python
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.constants import DEFAULT_DEPARTMENT, DOCUMENT_TYPES, TAB_NAMES

settings = get_settings()

app = FastAPI(
    title="MediDocs API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 静的ファイル
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# テンプレート
templates = Jinja2Templates(directory="app/templates")

# API ルーター
app.include_router(api_router, prefix="/api")


def get_available_models() -> list[str]:
    models = []
    if settings.anthropic_model or settings.claude_model:
        models.append("Claude")
    if settings.gemini_model:
        models.append("Gemini_Pro")
    return models if models else ["Claude"]


def get_common_context(active_page: str = "index") -> dict:
    return {
        "departments": DEFAULT_DEPARTMENT,
        "document_types": DOCUMENT_TYPES,
        "available_models": get_available_models(),
        "tab_names": TAB_NAMES,
        "active_page": active_page,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, **get_common_context("index")},
    )


@app.get("/prompts", response_class=HTMLResponse)
async def prompts_page(request: Request):
    return templates.TemplateResponse(
        "prompts.html",
        {"request": request, **get_common_context("prompts")},
    )


@app.get("/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request):
    return templates.TemplateResponse(
        "statistics.html",
        {"request": request, **get_common_context("statistics")},
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

### Phase 8: ユーティリティ移行（Day 6-7）

#### Step 8.1: テキスト処理

**ファイル:** `app/utils/text_processor.py`

```python
# utils/text_processor.py の内容をそのままコピー
```

#### Step 8.2: 例外

**ファイル:** `app/utils/exceptions.py`

```python
# utils/exceptions.py の内容をそのままコピー
```

#### Step 8.3: エラーハンドラ

**ファイル:** `app/utils/error_handlers.py`

```python
from fastapi import Request
from fastapi.responses import JSONResponse


async def api_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error_message": str(exc)},
    )
```

---

### Phase 9: テスト移行（Day 7-8）

#### Step 9.1: conftest.py 更新

**ファイル:** `tests/conftest.py`

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models.base import Base


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    return TestClient(app)
```

#### Step 9.2: API テスト

**ファイル:** `tests/test_api/test_summary.py`

```python
def test_get_available_models(client):
    response = client.get("/api/summary/models")
    assert response.status_code == 200
    data = response.json()
    assert "available_models" in data


def test_generate_summary_empty_input(client):
    response = client.post("/api/summary/generate", json={
        "medical_text": "",
        "model": "Claude"
    })
    assert response.status_code == 422  # Validation error
```

**Phase 9 完了確認:**
```bash
python -m pytest tests/ -v --tb=short
```

---

### Phase 10: デプロイ設定（Day 8）

#### Step 10.1: Procfile 更新

**ファイル:** `Procfile`

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### Step 10.2: requirements.txt 更新

追加パッケージ:
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
jinja2==3.1.6
python-multipart==0.0.18
pydantic-settings==2.7.1
```

#### Step 10.3: setup.sh（不要になる可能性あり）

Streamlit 固有の設定は削除。必要に応じて環境変数設定のみ残す。

---

## 移行チェックリスト

### Phase 1: 基盤構築
- [ ] ディレクトリ構造作成
- [ ] config.py 移行（pydantic-settings）
- [ ] constants.py 移行
- [ ] database.py 移行
- [ ] models/*.py 移行

### Phase 2: 外部 API
- [ ] base_api.py 移行
- [ ] claude_api.py 移行
- [ ] gemini_api.py 移行
- [ ] api_factory.py 移行

### Phase 3: サービス層
- [ ] summary_service.py 移行（UI コード除去）
- [ ] prompt_service.py 作成
- [ ] statistics_service.py 作成

### Phase 4: スキーマ
- [ ] summary.py 作成
- [ ] prompt.py 作成
- [ ] statistics.py 作成

### Phase 5: API エンドポイント
- [ ] summary.py 作成
- [ ] prompts.py 作成
- [ ] statistics.py 作成
- [ ] settings.py 作成
- [ ] router.py 作成

### Phase 6: テンプレート
- [ ] base.html 作成
- [ ] components/sidebar.html 作成
- [ ] index.html 作成
- [ ] prompts.html 作成
- [ ] statistics.html 作成
- [ ] static/js/app.js 作成
- [ ] static/css/style.css 作成

### Phase 7: メインアプリ
- [ ] main.py 作成

### Phase 8: ユーティリティ
- [ ] text_processor.py 移行
- [ ] exceptions.py 移行
- [ ] error_handlers.py 作成

### Phase 9: テスト
- [ ] conftest.py 更新
- [ ] API テスト作成
- [ ] 全テスト通過確認

### Phase 10: デプロイ
- [ ] Procfile 更新
- [ ] requirements.txt 更新
- [ ] Heroku デプロイ確認

---

## 検証方法

### ローカル起動
```bash
uvicorn app.main:app --reload --port 8000
# http://localhost:8000 でアクセス
# http://localhost:8000/api/docs で Swagger UI
```

### 機能検証チェックリスト
```
□ 文書生成: 4入力 → AI生成 → 8タブ表示
□ モデル切替: 40,000文字超でClaude→Gemini自動切替
□ プロンプト管理: 作成/編集/削除
□ 統計表示: 日付/モデル/文書タイプフィルタ
□ ユーザー設定: 診療科/医師/文書タイプ選択
```

---

## 既存ファイルとの対応表

| 現在 | 移行先 | 備考 |
|------|--------|------|
| `app.py` | `app/main.py` | エントリーポイント |
| `services/summary_service.py` | `app/services/summary_service.py` | UI コード除去 |
| `external_service/*.py` | `app/external/*.py` | インポートパス変更のみ |
| `database/models.py` | `app/models/*.py` | ファイル分割 |
| `database/db.py` | `app/core/database.py` | セッション管理改善 |
| `utils/config.py` | `app/core/config.py` | pydantic-settings 化 |
| `utils/constants.py` | `app/core/constants.py` | UI メッセージ追加 |
| `utils/prompt_manager.py` | `app/services/prompt_service.py` | サービス層に移動 |
| `utils/text_processor.py` | `app/utils/text_processor.py` | そのまま移行 |
| `views/main_page.py` | `app/templates/index.html` | HTML テンプレート化 |
| `views/prompt_management_page.py` | `app/templates/prompts.html` | HTML テンプレート化 |
| `views/statistics_page.py` | `app/templates/statistics.html` | HTML テンプレート化 |
| `ui_components/navigation.py` | `app/templates/components/sidebar.html` | HTML テンプレート化 |

---

## 注意事項

1. **データベース**: 既存の PostgreSQL スキーマをそのまま使用（マイグレーション不要）
2. **AI API**: 同期呼び出しを維持（将来的に非同期化可能）
3. **認証**: 現在は認証なし（将来追加可能な構造）
4. **セッション管理**: Alpine.js のローカルストレージで設定保存可能
5. **エラーハンドリング**: FastAPI の例外ハンドラで統一

---

## 旧コードの削除タイミング

移行完了・検証後に削除するファイル:
- `app.py`（旧 Streamlit エントリーポイント）
- `views/` ディレクトリ全体
- `ui_components/` ディレクトリ全体
- `setup.sh`（Streamlit 固有）
