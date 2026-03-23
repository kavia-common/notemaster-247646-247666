import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.settings import get_settings
from src.api.db.models import User
from src.api.db.session import get_db

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

TOKEN_SUBJECT_CLAIM = "sub"


# PUBLIC_INTERFACE
def create_access_token(*, user_id: uuid.UUID) -> str:
    """Create an access token for the given user_id."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {TOKEN_SUBJECT_CLAIM: str(user_id), "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _get_user_from_token(db: Session, token: str) -> Optional[User]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub = payload.get(TOKEN_SUBJECT_CLAIM)
        if not sub:
            return None
        user_id = uuid.UUID(sub)
    except (JWTError, ValueError):
        return None

    return db.scalar(select(User).where(User.id == user_id))


# PUBLIC_INTERFACE
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """FastAPI dependency that returns current authenticated user from JWT."""
    user = _get_user_from_token(db, token)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user
