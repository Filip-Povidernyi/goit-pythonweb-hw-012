from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect
from datetime import datetime, timedelta

from src.database.models import Contact, User
from src.schemas import ContactModel, ContactResponse, ContactUpdate


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(self, user: User, skip: int = 0, limit: int = 10) -> List[ContactModel]:
        query = select(Contact).filter(Contact.user_id ==
                                       user.id).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User):
        contact = await self.db.execute(
            select(Contact).filter(Contact.id ==
                                   contact_id, Contact.user_id == user.id)
        )
        return contact.scalars().first()

    async def create_contact(self, contact: ContactModel, user: User) -> ContactModel:
        result = Contact(**contact.model_dump(), user_id=user.id)
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        return result

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate, user: User) -> ContactResponse | None:
        result = await self.db.execute(
            select(Contact).filter(Contact.id ==
                                   contact_id, Contact.user_id == user.id)
        )
        db_contact = result.scalars().first()
        if db_contact:
            for key, value in contact_data.model_dump(exclude_unset=True).items():
                setattr(db_contact, key, value)
            await self.db.commit()
            await self.db.refresh(db_contact)

            return db_contact

        return None

    async def delete_contact(self, contact_id: int, user: User) -> ContactModel | None:
        q_contact = await self.get_contact_by_id(contact_id, user)
        if q_contact:
            await self.db.delete(q_contact)
            await self.db.commit()

        return q_contact

    async def search_contacts(self, query: str, user: User) -> List[ContactResponse]:

        stmt = select(Contact).where(
            (Contact.name.ilike(f'%{query}%')) |
            (Contact.last_name.ilike(f'%{query}%')) |
            (Contact.email.ilike(f'%{query}%')) |
            (Contact.phone.ilike(f'%{query}%'))
        ).where(Contact.user_id == user.id)
        result = await self.db.execute(stmt)
        contacts = result.scalars().all()

        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def get_birthdays(self, days: int, user: User) -> List[ContactResponse]:
        today = datetime.today()
        end = today + timedelta(days=days)
        days_range = [
            (today + timedelta(days=i)).strftime("%m-%d")
            for i in range((end - today).days + 1)
        ]
        birthday_days = func.to_char(Contact.birthday, "MM-DD")
        stmt = select(Contact).where(birthday_days.in_(
            days_range), Contact.user_id == user.id)
        result = await self.db.execute(stmt)
        contacts = result.scalars().all()

        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def get_contacts_count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Contact))
        return result.scalar_one()
