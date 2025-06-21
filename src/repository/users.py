from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        query = select(User).where(User.id == user_id)
        user = await self.db.execute(query)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        user = result.scalars().first()
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        user = await self.db.execute(query)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str = None) -> User:
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
        user = await self.get_user_by_email(email)
        user.avatar = url

        await self.db.commit()
        await self.db.refresh(user)

        return user
