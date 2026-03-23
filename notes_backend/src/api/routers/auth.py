from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.core.jwt import create_access_token, get_current_user
from src.api.core.security import hash_password, verify_password
from src.api.db.models import User
from src.api.db.session import get_db
from src.api.schemas import RegisterRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user. Email and username must be unique.",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserPublic:
    user = User(
        email=str(payload.email),
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email or username already exists")
    db.refresh(user)
    return UserPublic(id=user.id, email=user.email, username=user.username, created_at=user.created_at)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login (JWT)",
    description="Returns a JWT access token. Username may be username or email.",
)
def login(payload: RegisterRequest | None = None, body: dict | None = None, db: Session = Depends(get_db)) -> TokenResponse:
    # Accept either strict LoginRequest via JSON (preferred) or a compatible object.
    # This is to be resilient to frontend variations.
    if body is None:
        body = {}
    if payload is not None:
        username_or_email = payload.username  # type: ignore[attr-defined]
        password = payload.password  # type: ignore[attr-defined]
    else:
        username_or_email = body.get("username") or body.get("email") or ""
        password = body.get("password") or ""

    if not username_or_email or not password:
        raise HTTPException(status_code=400, detail="Missing username/password")

    user = db.scalar(
        select(User).where(or_(User.username == username_or_email, User.email == username_or_email))
    )
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    return TokenResponse(access_token=create_access_token(user_id=user.id))


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user",
    description="Returns the authenticated user's public profile.",
)
def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        created_at=current_user.created_at,
    )
