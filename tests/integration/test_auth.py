import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.services.auth import Hash, create_access_token, create_refresh_token, create_email_token
from main import app


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "strongpassword123"
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]


@pytest.mark.asyncio
async def test_register_user_conflict(client: AsyncClient, db_session: AsyncSession):
    # Add user to db first
    user = User(
        username="existinguser",
        email="existing@example.com",
        hashed_password=Hash().get_password_hash("pass"),
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()

    payload = {
        "username": "existinguser",
        "email": "existing@example.com",
        "password": "any"
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_user_success(client: AsyncClient, db_session: AsyncSession):
    password = "password123"
    user = User(
        username="logintest",
        email="logintest@example.com",
        hashed_password=Hash().get_password_hash(password),
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()

    data = {
        "username": "logintest",
        "password": password
    }
    response = await client.post("/api/auth/login", data=data)
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert "refresh_token" in json_data


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, db_session: AsyncSession):
    user = User(
        username="refreshme",
        email="refresh@example.com",
        hashed_password=Hash().get_password_hash("pass"),
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()

    refresh_token = await create_refresh_token({"sub": user.username})
    user.refresh_token = refresh_token
    await db_session.commit()

    response = await client.post("/api/auth/refresh-token", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_confirm_email(client: AsyncClient, db_session: AsyncSession):
    user = User(
        username="unconfirmed",
        email="unconfirmed@example.com",
        hashed_password=Hash().get_password_hash("pass"),
        is_verified=False
    )
    db_session.add(user)
    await db_session.commit()

    token = create_email_token({"sub": user.email})
    response = await client.get(f"/api/auth/confirm-email/{token}")
    assert response.status_code == 200
    assert response.json()[
        "message"] == "Your email has been successfully verified."
