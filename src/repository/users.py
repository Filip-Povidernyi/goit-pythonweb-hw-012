from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate, UserUpdatePassword


"""Repository for managing users in the database."""


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Retrieve a user by their ID."""
        query = select(User).where(User.id == user_id)
        user = await self.db.execute(query)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """Retrieve a user by their username."""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        user = result.scalars().first()
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email."""
        query = select(User).where(User.email == email)
        user = await self.db.execute(query)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str = None) -> User:
        """Create a new user in the database."""
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=body.password,
            avatar=avatar
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def verifyed_email(self, email: str):
        """Verify a user's email by setting is_verified to True."""
        """This method updates the user's is_verified status to True."""
        query = select(User).where(User.email == email)
        user = await self.db.execute(query)
        user = user.scalar_one_or_none()
        if user:
            user.is_verified = True
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def update_avatar_url(self, email: str, url: str) -> User:
        """Update the avatar URL for a user by their email."""
        """This method updates the avatar field of the user."""
        user = await self.get_user_by_email(email)
        user.avatar = url

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_current_user_password(self, user_id: int) -> UserUpdatePassword:
        """Retrieve the current user's password by their ID."""
        """This method returns the user's password information."""
        query = select(User).where(User.id == user_id)
        user = await self.db.execute(query)
        return user.scalar_one_or_none()
