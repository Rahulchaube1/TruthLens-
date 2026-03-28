"""Authentication and API key management routes."""
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

router = APIRouter()
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_DEFAULT_SECRET = "change-me-in-production-super-secret-key-xyz"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEFAULT_SECRET)
if SECRET_KEY == _DEFAULT_SECRET:
    import warnings
    warnings.warn(
        "JWT_SECRET_KEY is not set — using insecure default. "
        "Set the JWT_SECRET_KEY environment variable before deploying to production.",
        stacklevel=1,
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# In-memory user store (replace with DB in production)
_users: dict = {}
_api_keys: dict = {}


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class ApiKeyResponse(BaseModel):
    api_key: str
    created_at: datetime


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    # Check if it's an API key
    if token in _api_keys:
        return _api_keys[token]
    # Otherwise validate JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None or user_id not in _users:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return _users[user_id]
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    if any(u["email"] == req.email for u in _users.values()):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    _users[user_id] = {
        "id": user_id,
        "email": req.email,
        "name": req.name,
        "hashed_password": pwd_context.hash(req.password),
    }
    token = create_access_token({"sub": user_id})
    return TokenResponse(access_token=token, user_id=user_id)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = next((u for u in _users.values() if u["email"] == req.email), None)
    if not user or not pwd_context.verify(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user["id"]})
    return TokenResponse(access_token=token, user_id=user["id"])


@router.get("/apikey", response_model=ApiKeyResponse)
async def get_api_key(current_user: dict = Depends(get_current_user)):
    api_key = f"tl_{secrets.token_urlsafe(32)}"
    _api_keys[api_key] = current_user
    return ApiKeyResponse(api_key=api_key, created_at=datetime.now(timezone.utc))
