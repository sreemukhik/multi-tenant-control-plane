from app.database import engine
from sqlalchemy import text
import asyncio

async def add_column():
    print("Running migration...")
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE stores ADD COLUMN IF NOT EXISTS admin_password VARCHAR(255)"))
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(add_column())
