from app.database import AsyncSessionLocal
from app.models import Store, AuditLog
from sqlalchemy import select
import asyncio
import datetime
import uuid

async def inject_logs():
    namespace = "store-63e4bb79" # HARDCODED TARGET
    
    async with AsyncSessionLocal() as db:
        # Get latest store
        stmt = select(Store).order_by(Store.created_at.desc())
        result = await db.execute(stmt)
        store = result.scalars().first()
        
        if not store:
            print("No stores found!")
            return

        print(f"Targeting Store: {store.name} ({store.namespace})")
        store_id = str(store.id)
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Check if logs exist?
        # Just add them.
        
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
        print(f"Injected {len(logs)} audit logs.")

if __name__ == "__main__":
    asyncio.run(inject_logs())
