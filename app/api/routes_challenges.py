from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, delete
from app.db.database import get_async_session
from app.models import Challenge, User, Solve
from typing import List, Optional
import uuid
import shutil
import os

router = APIRouter()

# --- INPUT SCHEMAS ---
class ChallengeCreate(BaseModel):
    title: str
    description: str
    resources: str
    flag: str
    level: int
    points: int

class ChallengeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    resources: Optional[str] = None
    flag: Optional[str] = None
    level: Optional[int] = None
    points: Optional[int] = None

class FlagSubmission(BaseModel):
    user_email: str
    challenge_id: uuid.UUID
    flag: str

# --- FILE UPLOAD ---
@router.post("/upload")
async def upload_resource(file: UploadFile = File(...)):
    try:
        file_ext = file.filename.split(".")[-1]
        new_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = f"app/static/uploads/{new_filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"resource_url": f"/static/uploads/{new_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- CRUD ---
@router.post("/create", response_model=Challenge)
async def create_challenge(challenge: ChallengeCreate, session: AsyncSession = Depends(get_async_session)):
    existing = await session.execute(select(Challenge).where(Challenge.title == challenge.title))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Challenge exists!")
    new_challenge = Challenge(**challenge.dict())
    session.add(new_challenge)
    await session.commit()
    session.refresh(new_challenge)
    return new_challenge

@router.get("/list", response_model=List[Challenge])
async def list_challenges(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Challenge).order_by(Challenge.level, Challenge.title))
    return result.scalars().all()

@router.delete("/{challenge_id}")
async def delete_challenge(challenge_id: uuid.UUID, session: AsyncSession = Depends(get_async_session)):
    challenge = await session.get(Challenge, challenge_id)
    if not challenge: raise HTTPException(status_code=404, detail="Not found")
    
    # 1. DELETE RELATED SOLVES FIRST
    await session.execute(delete(Solve).where(Solve.challenge_id == challenge_id))
    
    # 2. DELETE THE CHALLENGE
    await session.delete(challenge)
    await session.commit()
    return {"ok": True}

@router.put("/{challenge_id}", response_model=Challenge)
async def update_challenge(challenge_id: uuid.UUID, data: ChallengeUpdate, session: AsyncSession = Depends(get_async_session)):
    challenge = await session.get(Challenge, challenge_id)
    if not challenge: raise HTTPException(status_code=404, detail="Not found")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(challenge, key, value)
    session.add(challenge)
    await session.commit()
    session.refresh(challenge)
    return challenge

# --- VERIFICATION ---
@router.post("/verify")
async def verify_flag(sub: FlagSubmission, session: AsyncSession = Depends(get_async_session)):
    challenge = await session.get(Challenge, sub.challenge_id)
    if not challenge: raise HTTPException(status_code=404, detail="Challenge not found")
    
    result = await session.execute(select(User).where(User.email == sub.user_email))
    user = result.scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")

    if sub.flag.strip() == challenge.flag.strip():
        solved_check = await session.execute(
            select(Solve).where(Solve.user_id == user.id, Solve.challenge_id == challenge.id)
        )
        if solved_check.scalar_one_or_none():
            return {"correct": True, "message": "Already solved!", "new_total_score": user.score}

        user.score += challenge.points
        new_solve = Solve(user_id=user.id, challenge_id=challenge.id)
        
        session.add(user)
        session.add(new_solve)
        await session.commit()
        session.refresh(user) 
        
        return {"correct": True, "message": f"Correct! +{challenge.points} Points!", "new_total_score": user.score}
    else:
        return {"correct": False, "message": "Incorrect flag.", "new_total_score": user.score}

# --- LEADERBOARD (UPDATED TO HIDE ADMINS) ---
@router.get("/leaderboard")
async def get_leaderboard(session: AsyncSession = Depends(get_async_session)):
    # Select Users where is_admin is FALSE, order by Score
    result = await session.execute(
        select(User)
        .where(User.is_admin == False)  # <--- THIS IS THE FIX
        .order_by(User.score.desc())
        .limit(10)
    )
    users = result.scalars().all()
    return [{"email": u.email.split('@')[0], "score": u.score} for u in users]
