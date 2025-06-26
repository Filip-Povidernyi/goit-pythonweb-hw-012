from fastapi import APIRouter, Depends, Request, UploadFile, File, Body, HTTPException
from fastapi.responses import JSONResponse
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession


from src.schemas import PasswordUpdateRequest, User, UserUpdatePassword
from src.services.auth import Hash, get_current_user
from limiter import limiter
from src.database.db import get_db
from src.conf.config import config
from src.services.upload_file import UploadFileService
from src.services.users import UserService


"""API router for user-related endpoints"""

router = APIRouter(prefix="/users", tags=["users"])

rate_limit_store = {}

MAX_REQUESTS = 2
TIME_WINDOW = timedelta(minutes=1)


@router.get("/me", response_model=User)
@limiter.limit("5/minute")
async def me(request: Request, user: User = Depends(get_current_user)):
    """Get the current user's information with rate limiting."""
    return user


@router.patch("/avatar", response_model=User)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the user's avatar."""
    avatar_url = UploadFileService(
        config.CLOUDINARY_NAME, config.CLOUDINARY_API_KEY, config.CLOUDINARY_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    if not user.is_admin:
        return JSONResponse(
            status_code=403,
            content={"error": "You have not permission to change avatar."},
        )
    user_new_ava = await user_service.update_avatar_url(user.email, avatar_url)

    return user_new_ava


@router.patch("/password", response_model=UserUpdatePassword)
async def update_avatar_user(passwords: PasswordUpdateRequest = Body(...), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Update the user's password."""
    user_id = user.id
    user_service = UserService(db)
    old_user = await user_service.get_current_user_password(user_id)
    if not Hash().verify_password(passwords.old_password, old_user.hashed_password):
        raise HTTPException(status_code=400, detail="Wrong current password.")

    if passwords.new_password1 != passwords.new_password2:
        raise HTTPException(
            status_code=400, detail="New passwords do not match.")

    new_hashed_password = Hash().get_password_hash(passwords.new_password1)
    old_user.hashed_password = new_hashed_password

    await db.commit()
    await db.refresh(old_user)

    return UserUpdatePassword(
        id=old_user.id,
        username=old_user.username,
        email=old_user.email,
        avatar=old_user.avatar,
        is_admin=old_user.is_admin
    )
