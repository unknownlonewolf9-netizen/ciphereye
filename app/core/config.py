from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ciphereye:cipherpass@db:5432/ciphereyedb"
    DATABASE_URL_SYNC: str = "postgresql://ciphereye:cipherpass@db:5432/ciphereyedb"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    SECRET_KEY: str = "your-secret-key-change-this-in-production-use-openssl-rand-hex-32"
    
    class Config:
        env_file = ".env"

settings = Settings()
