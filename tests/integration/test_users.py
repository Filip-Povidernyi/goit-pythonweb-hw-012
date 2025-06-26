import pytest
from httpx import AsyncClient
from sqlalchemy import text
from unittest.mock import patch

from src.services.auth import create_access_token
from src.services.auth import Hash
from src.database.models import User


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, db_session):
    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=Hash().get_password_hash("password123"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = await create_access_token(data={"sub": user.email})

    response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == user.email


@pytest.mark.asyncio
async def test_update_avatar_admin_success(client: AsyncClient, db_session):
    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()
    user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=Hash().get_password_hash("adminpass"),
        is_verified=True,
        is_admin=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = await create_access_token(data={"sub": user.email})

    with open("tests/data/avatar.png", "rb") as avatar_file:
        response = await client.patch(
            "/api/users/avatar",
            files={"file": ("avatar.png", avatar_file, "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert "avatar" in response.json()


@pytest.mark.asyncio
async def test_update_avatar_not_admin(client: AsyncClient, db_session):
    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()
    user = User(
        username="user",
        email="user@example.com",
        hashed_password=Hash().get_password_hash("pass"),
        is_verified=True,
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()

    token = await create_access_token(data={"sub": user.email})

    with open("tests/data/avatar.png", "rb") as avatar_file:
        response = await client.patch(
            "/api/users/avatar",
            files={"file": ("avatar.png", avatar_file, "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
    assert response.json()[
        "error"] == "You have not permission to change avatar."


@pytest.mark.asyncio
async def test_update_password_success(client: AsyncClient, db_session):
    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()
    password = "oldpassword"
    user = User(
        username="changepass",
        email="change@example.com",
        hashed_password=Hash().get_password_hash(password),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = await create_access_token(data={"sub": user.email})

    payload = {
        "old_password": password,
        "new_password1": "newsecurepass",
        "new_password2": "newsecurepass"
    }

    response = await client.patch(
        "/api/users/password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == user.username


@pytest.mark.asyncio
async def test_update_password_wrong_old(client: AsyncClient, db_session):
    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()
    user = User(
        username="wrongold",
        email="wrong@example.com",
        hashed_password=Hash().get_password_hash("realpass"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = await create_access_token(data={"sub": user.email})

    payload = {
        "old_password": "wrongpass",
        "new_password1": "newpass",
        "new_password2": "newpass"
    }

    response = await client.patch(
        "/api/users/password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Wrong current password."


@pytest.mark.asyncio
async def test_update_password_mismatch(client: AsyncClient, db_session):
    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()
    user = User(
        username="mismatch",
        email="mismatch@example.com",
        hashed_password=Hash().get_password_hash("pass"),
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = await create_access_token(data={"sub": user.email})

    payload = {
        "old_password": "pass",
        "new_password1": "pass1",
        "new_password2": "pass2"
    }

    response = await client.patch(
        "/api/users/password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "New passwords do not match."
