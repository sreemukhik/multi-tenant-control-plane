from app.database import AsyncSessionLocal
from app.models import Store
from sqlalchemy import select, update
import asyncio

async def mark_ready():
    target_id = None
    namespace = "store-63e4bb79" # Hardcoded latest from step 4543
    
    print(f"Searching for store with namespace {namespace}...")
    async with AsyncSessionLocal() as db:
        stmt = select(Store).where(Store.namespace == namespace)
        result = await db.execute(stmt)
        store = result.scalars().first()
        
        if store:
            print(f"Found store: {store.name} ({store.id})")
            print(f"Current Status: {store.status}")
            
            # Force Ready
            stmt = update(Store).where(Store.id == store.id).values(status="ready") # Use lowercase 'ready' per StoreModel
            await db.execute(stmt)
            await db.commit()
            print("Status updated to 'ready'.")
        else:
            print("Store not found.")

if __name__ == "__main__":
    asyncio.run(mark_ready())
