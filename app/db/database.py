from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Async Engine (for FastAPI)
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)

# Sync Engine (for Celery Worker)
# Handles the case where the URL might already be sync
if "postgresql+asyncpg" in settings.DATABASE_URL:
    SYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
else:
    SYNC_DATABASE_URL = settings.DATABASE_URL

engine_sync = create_engine(SYNC_DATABASE_URL, echo=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# --- THIS IS THE MISSING FUNCTION CAUSING THE CRASH ---
async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session
