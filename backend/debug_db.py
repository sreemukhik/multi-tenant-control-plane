from app.database import AsyncSessionLocal
from app.models import Store
from sqlalchemy import select
import asyncio

async def check_passwords():
    print("Checking database for passwords...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Store).order_by(Store.created_at.desc()))
        stores = result.scalars().all()
        for s in stores:
            print(f"Store: {s.name}, ID: {s.id}, Pass: '{s.admin_password}'")

if __name__ == "__main__":
    asyncio.run(check_passwords())
