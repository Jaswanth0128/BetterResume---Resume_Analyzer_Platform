# auth/hashing.py
from passlib.context import CryptContext

# Set up the hashing context, specifying the bcrypt algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    """Hashes a plain-text password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verifies a plain-text password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)