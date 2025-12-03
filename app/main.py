from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes_osint import router as osint_router
from app.api.routes_auth import router as auth_router
from app.api.routes_challenges import router as challenges_router
from app.db.database import init_db
import os

os.makedirs("app/static/uploads", exist_ok=True)

app = FastAPI(title="CipherEye Backend")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(osint_router, prefix="/api")
app.include_router(auth_router, prefix="/auth")
app.include_router(challenges_router, prefix="/challenges")

@app.on_event("startup")
async def on_startup():
    try:
        await init_db()
    except Exception as e:
        print(f"DB init error: {e}")
