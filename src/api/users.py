from fastapi import APIRouter, Depends, Request, UploadFile, File
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import User
from src.services.auth import get_current_user
from limiter import limiter
from src.database.db import get_db
from src.conf.config import config
from src.services.upload_file import UploadFileService
from src.services.users import UserService

router = APIRouter(prefix="/users", tags=["users"])

rate_limit_store = {}

MAX_REQUESTS = 2
TIME_WINDOW = timedelta(minutes=1)


@router.get("/me", response_model=User)
@limiter.limit("5/minute")
async def me(request: Request, user: User = Depends(get_current_user)):

    return user


@router.patch("/avatar", response_model=User)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    avatar_url = UploadFileService(
        config.CLOUDINARY_NAME, config.CLOUDINARY_API_KEY, config.CLOUDINARY_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user_new_ava = await user_service.update_avatar_url(user.email, avatar_url)

    return user_new_ava
