import pytest
import asyncio
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch


from src.services.auth import create_access_token
from main import app
from src.services.auth import Hash
from src.database.db import get_db
from src.database.models import Base, User, Contact


TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, expire_on_commit=False, class_=AsyncSession)

test_user_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "123456789",
    "is_admin": False,
}


@pytest.fixture(autouse=True)
def mock_redis():
    """Автоматичне мокання глобального Redis-з'єднання."""
    mock_r = MagicMock()
    mock_r.get.return_value = None
    mock_r.set.return_value = True
    mock_r.expire.return_value = True

    # ВАЖЛИВО: точно вказуємо імпортовану змінну `r` в auth.py
    with patch("src.services.auth.r", mock_r):
        yield mock_r


@pytest.fixture(scope="session")
def event_loop():
    """Ініціалізація event loop для pytest-asyncio."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def init_models():
    """Створення тестової бази даних."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        hashed_pw = Hash().get_password_hash(test_user_data["password"])
        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            hashed_password=hashed_pw,
            is_verified=True,
            avatar="https://example.com/avatar.jpg",
            is_admin=test_user_data["is_admin"],
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        test_user_data["id"] = user.id


@pytest.fixture
async def override_db_session():
    """Переопреділення залежності get_db на тестову БД."""
    async def _override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
async def db_session() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture()
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user():
    """Фікстура для доступу до даних тестового користувача."""
    return test_user_data


@pytest.fixture
async def test_user_token(test_user):
    token = await create_access_token({"sub": test_user["username"]})
    return token
