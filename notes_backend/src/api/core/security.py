from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against its stored hash."""
    return pwd_context.verify(plain_password, password_hash)
