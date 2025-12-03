import asyncio
import sys
from sqlmodel import select
from app.db.database import AsyncSessionLocal
from app.models import User

async def promote_user(email):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User {email} not found.")
            return
        
        user.is_admin = True
        session.add(user)
        await session.commit()
        print(f"✅ SUCCESS: {email} is now an ADMIN.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage.py <email>")
        sys.exit(1)
    
    target_email = sys.argv[1]
    asyncio.run(promote_user(target_email))
