import pytest
from unittest.mock import AsyncMock, MagicMock

from src.repository.users import UserRepository
from src.database.models import User
from src.schemas import UserCreate


@pytest.fixture
def test_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_pass",
        is_verified=False,
        avatar="https://example.com/avatar.jpg"
    )


@pytest.fixture
def user_create():
    return UserCreate(
        username="testuser",
        email="test@example.com",
        password="hashed_pass"
    )


@pytest.mark.asyncio
async def test_get_user_by_id(test_user):
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user

    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(mock_session)
    result = await repo.get_user_by_id(test_user.id)

    assert result == test_user


@pytest.mark.asyncio
async def test_get_user_by_username(test_user):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = test_user
    mock_session.execute.return_value = mock_result

    repo = UserRepository(mock_session)
    result = await repo.get_user_by_username("testuser")

    assert result == test_user


@pytest.mark.asyncio
async def test_get_user_by_email(test_user):
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user

    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(mock_session)
    result = await repo.get_user_by_email(test_user.email)

    assert result == test_user


@pytest.mark.asyncio
async def test_create_user(user_create):
    mock_session = AsyncMock()

    repo = UserRepository(mock_session)
    result = await repo.create_user(user_create, avatar="https://avatar.png")

    assert result.username == user_create.username
    assert result.email == user_create.email
    assert result.hashed_password == user_create.password
    assert result.avatar == "https://avatar.png"

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_verifyed_email(test_user):
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user

    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(mock_session)
    result = await repo.verifyed_email(test_user.email)

    assert result.is_verified is True
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(test_user)


@pytest.mark.asyncio
async def test_update_avatar_url(test_user):
    mock_session = AsyncMock()
    mock_repo = UserRepository(mock_session)
    mock_repo.get_user_by_email = AsyncMock(return_value=test_user)

    result = await mock_repo.update_avatar_url("test@example.com", "https://new-avatar.jpg")

    assert result.avatar == "https://new-avatar.jpg"
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_get_current_user_password(test_user):
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user

    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(mock_session)
    result = await repo.get_current_user_password(test_user.id)

    assert result.hashed_password == test_user.hashed_password
