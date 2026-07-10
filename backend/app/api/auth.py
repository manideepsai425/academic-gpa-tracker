"""
Authentication routes. Sessions are httpOnly cookies, not
Authorization headers — the frontend never touches the raw token,
which is the entire point of httpOnly (it's inaccessible to JS,
including any XSS payload that might get injected).
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import COOKIE_NAME, get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.crud.user import create_user, get_user_by_username
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def _set_auth_cookie(response: Response, username: str) -> None:
    token = create_access_token(subject=username)
    max_age = settings.access_token_expire_minutes * 60

    # SameSite=None + Secure is required for the cookie to survive a
    # cross-site request — Vercel and Render are different domains, so
    # without this the cookie simply never arrives on the frontend.
    # In local dev (http://localhost) Secure cookies are dropped by
    # browsers over plain HTTP, hence the environment-based switch.
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=max_age,
        secure=settings.is_production,
        samesite="none" if settings.is_production else "lax",
        path="/",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, response: Response, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken",
        )
    user = create_user(db, user_in)
    _set_auth_cookie(response, user.username)
    return user


@router.post("/login", response_model=UserOut)
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = get_user_by_username(db, credentials.username)
    if not user or not verify_password(credentials.password, user.hashed_password):
        # Deliberately identical error for "no such user" and "wrong
        # password" — distinguishing them lets an attacker enumerate
        # valid usernames.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    _set_auth_cookie(response, user.username)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
