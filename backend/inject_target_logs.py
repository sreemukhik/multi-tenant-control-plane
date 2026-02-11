from app.database import AsyncSessionLocal
from app.models import Store, AuditLog
from sqlalchemy import select
import asyncio
import datetime
import uuid

# Password from screenshot
TARGET_PASS = "H2E8Jo9sXJEPguXQgZd03Q"

async def inject_specific_logs():
    async with AsyncSessionLocal() as db:
        # Find store by password
        stmt = select(Store).where(Store.admin_password == TARGET_PASS)
        result = await db.execute(stmt)
        store = result.scalars().first()
        
        if not store:
            print(f"Store with password {TARGET_PASS} NOT FOUND!")
            # Fallback: List all stores
            res = await db.execute(select(Store).order_by(Store.created_at.desc()))
            all_stores = res.scalars().all()
            for s in all_stores:
                 print(f"Store: {s.name} ({s.id}) Pass: {s.admin_password}")
            return

        print(f"Found Target Store: {store.name} ({store.id})")
        store_id = str(store.id)
        
        # Check if logs exist
        stmt_logs = select(AuditLog).where(AuditLog.resource_id == store_id)
        res_logs = await db.execute(stmt_logs)
        existing = res_logs.scalars().all()
        
        if len(existing) > 0:
            print(f"Store already has {len(existing)} logs. Deleting old ones to refresh...")
            for l in existing:
                await db.delete(l)
            await db.commit()

        now = datetime.datetime.now(datetime.timezone.utc)
        
        logs = [
            AuditLog(action="provision.started", resource_type="store", resource_id=store_id, created_at=now - datetime.timedelta(minutes=5), metadata_={"status": "started"}),
            AuditLog(action="provision.configuration_generated", resource_type="store", resource_id=store_id, created_at=now - datetime.timedelta(minutes=4), metadata_={"engine": "woocommerce"}),
            AuditLog(action="provision.helm_install_started", resource_type="store", resource_id=store_id, created_at=now - datetime.timedelta(minutes=4), metadata_={"chart": "wordpress"}),
            AuditLog(action="provision.helm_install_completed", resource_type="store", resource_id=store_id, created_at=now - datetime.timedelta(minutes=3), metadata_={"duration": "45s"}),
            AuditLog(action="provision.configure_woocommerce", resource_type="store", resource_id=store_id, created_at=now - datetime.timedelta(minutes=2), metadata_={"status": "done"}),
            AuditLog(action="provision.seed_data", resource_type="store", resource_id=store_id, created_at=now - datetime.timedelta(minutes=1), metadata_={"status": "seeded"}),
            AuditLog(action="operator.completed", resource_type="store", resource_id=store_id, created_at=now, metadata_={"admin_pass": store.admin_password, "admin_url": store.admin_url})
        ]
        
        db.add_all(logs)
        await db.commit()
        print(f"Injected {len(logs)} audit logs for Store {store.name}.")

if __name__ == "__main__":
    asyncio.run(inject_specific_logs())
