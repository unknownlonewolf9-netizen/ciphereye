from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, delete
from jose import JWTError, jwt
from app.db.database import get_async_session
from app.models import User, Solve
from app.core.security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from typing import List
import uuid

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- SCHEMAS ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserCreateAdmin(BaseModel):  # New schema for Admin creation
    email: EmailStr
    password: str
    is_admin: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    is_admin: bool

class UserScoreUpdate(BaseModel):
    score: int

class UserDisplay(BaseModel):
    id: uuid.UUID
    email: str
    is_admin: bool
    score: int

# --- DEPENDENCIES ---
async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError: raise credentials_exception
        
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None: raise credentials_exception
    return user

# --- USER MANAGEMENT ---
@router.get("/users", response_model=List[UserDisplay])
async def get_all_users(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await session.execute(select(User).order_by(User.created_at))
    return result.scalars().all()

# NEW: Create User (Admin Only)
@router.post("/users", response_model=UserDisplay)
async def create_user_by_admin(new_user: UserCreateAdmin, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if exists
    result = await session.execute(select(User).where(User.email == new_user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create
    user = User(
        email=new_user.email,
        hashed_password=get_password_hash(new_user.password),
        is_admin=new_user.is_admin
    )
    session.add(user)
    await session.commit()
    session.refresh(user)
    return user

@router.put("/users/{user_id}/score")
async def update_user_score(user_id: uuid.UUID, update: UserScoreUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    target_user = await session.get(User, user_id)
    if not target_user: raise HTTPException(status_code=404, detail="User not found")
    
    target_user.score = update.score
    session.add(target_user)
    await session.commit()
    return {"ok": True, "new_score": target_user.score}

@router.delete("/users/{user_id}")
async def delete_user(user_id: uuid.UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin account.")

    target_user = await session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await session.execute(delete(Solve).where(Solve.user_id == user_id))
    await session.delete(target_user)
    await session.commit()
    
    return {"ok": True, "message": "User deleted"}

# --- PUBLIC AUTH ---
@router.post("/signup", response_model=Token)
async def signup(user: UserCreate, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        is_admin=False
    )
    session.add(new_user)
    await session.commit()
    
    access_token = create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer", "is_admin": False}

@router.post("/login", response_model=Token)
async def login(user: UserLogin, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer", "is_admin": db_user.is_admin}
