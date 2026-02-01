from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import bcrypt
import structlog
from pydantic import BaseModel

from ..database import get_db, Recruiter
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger("auth")

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

# JWT Configuration
SECRET_KEY = settings.secret_key.get_secret_value()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class LoginRequest(BaseModel):
    email: str   # Changed from EmailStr to support generic IDs
    password: str = None

class IdentityRequest(BaseModel):
    identity: str   # Changed from email to identity for clarity

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company: str = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    company: str = None
    is_active: bool
    created_at: datetime

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), db: Session = Depends(get_db)):
    if not credentials:
        return None
        
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None

        user = db.query(Recruiter).filter(Recruiter.id == user_id).first()
        return user
    except (jwt.ExpiredSignatureError, jwt.PyJWTError):
        return None

def get_authenticated_user(user: Optional[Recruiter] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(Recruiter).filter(Recruiter.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(request.password)
    new_user = Recruiter(
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.full_name,
        company=request.company
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create access token
    access_token = create_access_token(data={"sub": str(new_user.id)})

    return TokenResponse(
        access_token=access_token,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "company": new_user.company,
            "is_active": new_user.is_active
        }
    )

@router.post("/identity", response_model=TokenResponse)
async def login_by_identity(request: IdentityRequest, db: Session = Depends(get_db)):
    """Log in or register automatically using only an identity string."""
    # Find or create user
    user = db.query(Recruiter).filter(Recruiter.email == request.identity).first()
    
    if not user:
        # Create a new simplified user identity
        user = Recruiter(
            email=request.identity,
            hashed_password="ID_ONLY_ACCOUNT", # Placeholder
            full_name=request.identity,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created new password-less identity", identity=request.identity, user_id=user.id)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "company": user.company,
            "is_active": user.is_active
        }
    )

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: Recruiter = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        company=current_user.company,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    full_name: str = None,
    company: str = None,
    current_user: Recruiter = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    if full_name is not None:
        current_user.full_name = full_name
    if company is not None:
        current_user.company = company

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        company=current_user.company,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )