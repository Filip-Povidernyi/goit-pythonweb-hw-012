import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.database.models import Contact, User
from src.schemas import ContactModel, ContactUpdate
from src.repository.contacts import ContactRepository


@pytest.fixture
def user():
    return User(id=1, username="testuser", email="test@example.com")


@pytest.fixture
def contact_model():
    return ContactModel(
        name="John",
        last_name="Doe",
        email="john@example.com",
        phone="1234567890",
        birthday=datetime(1990, 1, 1).date(),
    )


@pytest.fixture
def contact():
    return Contact(
        id=1,
        name="John",
        last_name="Doe",
        email="john@example.com",
        phone="1234567890",
        birthday=datetime(1990, 1, 1).date(),
        created_at=datetime.utcnow(),
        user_id=1,
    )


@pytest.mark.asyncio
async def test_get_contacts(user, contact):
    mock_session = AsyncMock()

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [contact]

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session.execute.return_value = mock_result

    repo = ContactRepository(mock_session)
    result = await repo.get_contacts(user)

    assert result == [contact]


@pytest.mark.asyncio
async def test_get_contact_by_id(user, contact):
    mock_session = AsyncMock()

    mock_scalars = MagicMock()
    mock_scalars.first.return_value = contact

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session.execute.return_value = mock_result

    repo = ContactRepository(mock_session)
    result = await repo.get_contact_by_id(1, user)

    assert result == contact


@pytest.mark.asyncio
async def test_create_contact(user, contact_model):
    mock_session = AsyncMock()

    repo = ContactRepository(mock_session)
    result = await repo.create_contact(contact_model, user)

    assert isinstance(result, Contact)
    assert result.name == contact_model.name
    assert result.user_id == user.id
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_update_contact(user, contact):
    mock_session = AsyncMock()

    mock_scalars = MagicMock()
    mock_scalars.first.return_value = contact

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session.execute.return_value = mock_result

    update_data = ContactUpdate(phone="0987654321")
    repo = ContactRepository(mock_session)
    result = await repo.update_contact(1, update_data, user)

    assert result.phone == "0987654321"
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_delete_contact(user, contact):
    mock_session = AsyncMock()
    repo = ContactRepository(mock_session)
    repo.get_contact_by_id = AsyncMock(return_value=contact)

    result = await repo.delete_contact(1, user)

    assert result == contact
    mock_session.delete.assert_called_once_with(contact)
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_search_contacts(user, contact):
    mock_session = AsyncMock()

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [contact]

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session.execute.return_value = mock_result

    repo = ContactRepository(mock_session)
    result = await repo.search_contacts("john", user)

    assert len(result) == 1
    assert result[0].email == contact.email


@pytest.mark.asyncio
async def test_get_birthdays(user, contact):
    contact.birthday = (datetime.today() + timedelta(days=3)).date()
    mock_session = AsyncMock()

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [contact]

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session.execute.return_value = mock_result

    repo = ContactRepository(mock_session)
    result = await repo.get_birthdays(7, user)

    assert len(result) == 1
    assert result[0].name == contact.name
