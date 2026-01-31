from datetime import datetime
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import generate_csrf_token
from app.main import app
from app.models.base import Base
from app.models.prompt import Prompt
from app.models.usage import SummaryUsage


@pytest.fixture(scope="function", autouse=True)
def override_settings():
    """テスト環境用の設定をオーバーライド"""
    def get_test_settings():
        settings = Settings()
        # テスト環境ではCSRF秘密鍵を固定値に設定
        settings.csrf_secret_key = "test-csrf-secret-key"
        return settings

    app.dependency_overrides[get_settings] = get_test_settings
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_db():
    """テスト用のインメモリSQLiteデータベース"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal()

    Base.metadata.drop_all(bind=engine)
    # get_settingsのオーバーライドは維持（autouse fixtureで管理）
    db_override = app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client(test_db):
    """FastAPIテストクライアント"""
    return TestClient(app)


@pytest.fixture
def sample_prompts(test_db):
    """テスト用のサンプルプロンプト"""
    prompts = [
        Prompt(department="default", doctor="default", document_type="他院への紹介", content="デフォルトプロンプト",
               is_default=True),
        Prompt(
            department="眼科",
            doctor="橋本義弘",
            document_type="他院への紹介",
            content="眼科用プロンプト",
            selected_model="Claude",
            is_default=False,
        ),
    ]
    for prompt in prompts:
        test_db.add(prompt)
    test_db.commit()
    for prompt in prompts:
        test_db.refresh(prompt)
    return prompts


@pytest.fixture
def sample_usage_records(test_db):
    """テスト用のサンプル使用統計"""
    jst = ZoneInfo("Asia/Tokyo")
    records = [
        SummaryUsage(
            date=datetime.now(jst),
            department="眼科",
            doctor="橋本義弘",
            document_type="他院への紹介",
            model="Claude",
            input_tokens=1000,
            output_tokens=500,
            processing_time=2.5,
        ),
        SummaryUsage(
            date=datetime.now(jst),
            department="default",
            doctor="default",
            document_type="返書",
            model="Gemini_Pro",
            input_tokens=2000,
            output_tokens=800,
            processing_time=3.2,
        ),
    ]
    for record in records:
        test_db.add(record)
    test_db.commit()
    for record in records:
        test_db.refresh(record)
    return records


@pytest.fixture
def csrf_headers():
    """CSRFトークン付きヘッダーを生成"""
    settings = Settings()
    settings.csrf_secret_key = "test-csrf-secret-key"
    settings.csrf_token_expire_minutes = 60
    token = generate_csrf_token(settings)
    return {"X-CSRF-Token": token}
