import redis
import pickle
from datetime import datetime, timedelta, UTC
from typing import Optional, Literal
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db
from src.conf.config import config
from src.database.models import User
from src.services.users import UserService


"""Service for handling authentication-related operations, including token creation and password hashing."""


class Hash:
    """Class for hashing and verifying passwords using bcrypt."""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """Verify a plain password against a hashed password."""
        """Returns True if the plain password matches the hashed password, otherwise False."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """Hash a plain password using bcrypt."""
        """Returns the hashed password."""
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
"""OAuth2PasswordBearer is a class that provides a way to extract the token from the request.
It is used to secure endpoints that require authentication."""
r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)


def create_token(
    data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh", "email"]
):
    """Create a JWT token with the given data and expiration time."""
    """The token will include the expiration time, issued at time, and token type."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    encoded_jwt = jwt.encode(
        to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt


async def create_access_token(data: dict, expires_delta: Optional[int] = None):
    """Create an access token with the given data and optional expiration time."""
    """If expires_delta is provided, it will be used as the expiration time."""
    if expires_delta:
        access_token = create_token(data, expires_delta, "access")
    else:
        access_token = create_token(
            data, timedelta(
                minutes=config.JWT_EXPIRATION_MINUTES), "access"
        )
    return access_token


async def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
    """Create a refresh token with the given data and optional expiration time."""
    """If expires_delta is provided, it will be used as the expiration time."""
    if expires_delta:
        refresh_token = create_token(data, expires_delta, "refresh")
    else:
        refresh_token = create_token(
            data, timedelta(
                minutes=config.REFRESH_TOKEN_EXPIRE_MINUTES), "refresh"
        )
    return refresh_token


def create_email_token(data: dict, expires_delta: Optional[int] = None):
    """Create an email verification token with the given data and optional expiration time."""
    """If expires_delta is provided, it will be used as the expiration time."""

    if expires_delta:
        email_token = create_token(data, expires_delta, "email")
    else:
        email_token = create_token(
            data, timedelta(
                minutes=60), "email"
        )
    return email_token


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current user from the token.
    This function decodes the JWT token, retrieves the username from the payload
    and fetches the user from the database or cache.
    If the user is not found in the cache, it queries the database and caches the user.
    If the token is invalid or the user is not found, it raises an HTTPException."""
    """If the user is found, it returns the User object."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
        username = payload["sub"]
        if username is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception

    user = r.get(f"user: {username}")

    if user is None:
        user_service = UserService(db)
        user = await user_service.get_user_by_username(username)
        r.set(f"user: {username}", pickle.dumps(user))
        r.expire(f"user: {username}", timedelta(minutes=15))
    else:
        user = pickle.loads(user)

    if user is None:
        raise credentials_exception

    return user


async def verify_refresh_token(refresh_token: str, db: AsyncSession):
    """Verify the refresh token by decoding it and checking the username and token type."""
    """If the token is valid, it retrieves the user from the database using the username and refresh token."""
    """If the token is invalid or the user is not found, it returns None."""
    try:
        payload = jwt.decode(refresh_token, config.JWT_SECRET,
                             algorithms=[config.JWT_ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("token_type")
        if username is None or token_type != "refresh":
            return None

        stmt = select(User).where(
            User.username == username,
            User.refresh_token == refresh_token
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        return user
    except JWTError:
        return None


async def get_email_from_token(token: str) -> str:
    """Extract the email from the email verification token."""
    try:
        payload = jwt.decode(
            token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
        email = payload["sub"]
        token_type = payload["token_type"]
        if token_type != "email":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid token"
        )
