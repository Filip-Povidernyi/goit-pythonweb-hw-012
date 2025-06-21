from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.repository.contacts import ContactRepository
from src.schemas import ContactModel, ContactResponse, ContactUpdate


class ContactService:
    def __init__(self, db: AsyncSession):
        self.repository = ContactRepository(db)

    async def get_contacts(self, user, skip: int = 0, limit: int = 10) -> List[ContactModel]:
        return await self.repository.get_contacts(user, skip, limit)

    async def get_contact_by_id(self, contact_id: int, user: User) -> ContactResponse | None:
        return await self.repository.get_contact_by_id(contact_id, user)

    async def create_contact(self, contact: ContactModel, user: User) -> ContactModel:
        return await self.repository.create_contact(contact, user)

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate, user: User) -> ContactResponse | None:
        return await self.repository.update_contact(contact_id, contact_data, user)

    async def delete_contact(self, contact_id: int, user: User) -> ContactModel | None:
        return await self.repository.delete_contact(contact_id, user)

    async def search_contacts(self, query: str, user: User) -> List[ContactResponse]:
        return await self.repository.search_contacts(query, user)

    async def get_birthdays_in_next_days(self, days: int, user: User) -> List[ContactResponse]:
        return await self.repository.get_birthdays(days, user)
