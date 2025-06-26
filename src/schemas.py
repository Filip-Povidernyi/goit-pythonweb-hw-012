from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr


"""Schemas for user and contact management, including user creation, updates, and contact details."""


class User(BaseModel):
    """Schema representing a user in the system."""
    """Includes fields for user ID, username, email, admin status, and avatar URL."""
    id: int
    username: str
    email: str
    is_admin: bool
    avatar: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    """Includes fields for username, email, password, and admin status."""
    username: str
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False


class UserUpdatePassword(BaseModel):
    """Schema for updating a user's password."""
    """Includes fields for user ID, username, email, and hashed password."""
    id: int
    username: str
    email: str
    hashed_password: Optional[str] = None


class PasswordUpdateRequest(BaseModel):
    """Schema for requesting a password update."""
    """Includes fields for old password, new password, and confirmation of the new password."""
    old_password: str
    new_password1: str
    new_password2: str


class Token(BaseModel):
    """Schema for authentication tokens."""
    """Includes fields for access token, refresh token, and token type."""
    access_token: str
    refresh_token: str
    token_type: str


class TokenRefreshRequest(BaseModel):
    """Schema for requesting a new access token using a refresh token."""
    """Includes a field for the refresh token."""
    refresh_token: str


class ContactModel(BaseModel):
    """Base schema for contact information."""
    """Includes fields for contact name, last name, email, phone, birthday, and additional info."""
    """Fields have validation constraints such as maximum and minimum lengths."""
    name: str = Field(max_length=30, min_length=3)
    last_name: str = Field(max_length=50, min_length=1)
    email: EmailStr
    phone: str = Field(max_length=15, min_length=7)
    birthday: date
    additional_info: Optional[str] = Field(max_length=255, default=None)


class ContactCreate(ContactModel):
    """Schema for creating a new contact."""
    """Inherits from ContactModel and does not add any new fields."""
    pass


class ContactUpdate(ContactModel):
    """Schema for updating an existing contact."""
    """Inherits from ContactModel and allows optional fields to be None."""
    name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthday: Optional[date] = None


class ContactResponse(ContactModel):
    """Schema for the response of a contact."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)
