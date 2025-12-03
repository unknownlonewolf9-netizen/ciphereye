from fastapi import FastAPI
from app.api.routes_osint import router as osint_router
from app.db.database import init_db

app = FastAPI(title="CipherEye Backend (Phase 1)")
app.include_router(osint_router, prefix="/api")

@app.on_event("startup")
async def on_startup():
    try:
        await init_db()
    except Exception as e:
        print("DB init error:", e)
