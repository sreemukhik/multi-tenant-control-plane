from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import Store
from app.schemas import StoreCreate, StoreResponse
import uuid

router = APIRouter()

@router.get("/", response_model=List[StoreResponse])
async def list_stores(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Store).offset(skip).limit(limit))
    stores = result.scalars().all()
    return stores

from app.utils.limiter import limiter
from app.config import settings
from sqlalchemy import func

from typing import Any

@router.get("/audit-logs")
async def get_audit_logs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    from app.models import AuditLog
    # Fetch high-level audit logs (exclude technical activity logs)
    stmt = select(AuditLog).where(~AuditLog.action.like('activity.%')).order_by(AuditLog.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "metadata_": log.metadata_
        }
        for log in logs
    ]

@router.post("/", response_model=StoreResponse)
@limiter.limit(f"{settings.RATE_LIMIT_CREATES_PER_MINUTE}/minute")
async def create_store(
    store_in: StoreCreate, 
    request: Request, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    from app.models import AuditLog
    # Quota Check
    result = await db.execute(select(func.count()).select_from(Store).where(Store.status != "failed"))
    count = result.scalar()
    
    if count >= settings.MAX_STORES_PER_USER:
         # Log quota failure
         log = AuditLog(
             action="quota.check.failed",
             resource_type="system",
             ip_address=request.client.host,
             metadata_={"requested_name": store_in.name, "current_count": count}
         )
         db.add(log)
         await db.commit()
         raise HTTPException(status_code=403, detail=f"Quota exceeded. Max {settings.MAX_STORES_PER_USER} stores allowed.")
    
    new_store = Store(
        name=store_in.name,
        engine=store_in.engine,
        status="requested",
        namespace=f"store-{str(uuid.uuid4())[:8]}",
        user_id=None
    )
    db.add(new_store)
    await db.commit()
    await db.refresh(new_store)
    
    # Audit Log: user.create_store
    log = AuditLog(
        action="user.create_store",
        resource_type="store",
        resource_id=str(new_store.id),
        ip_address=request.client.host,
        metadata_={"name": store_in.name, "engine": store_in.engine}
    )
    db.add(log)
    await db.commit()
    
    # Trigger background provisioning task
    from app.services.orchestrator import provision_store
    background_tasks.add_task(provision_store, new_store.id)
    
    return new_store

@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(store_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalars().first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

@router.delete("/{store_id}")
async def delete_store(store_id: uuid.UUID, request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    from app.models import AuditLog
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalars().first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    store.status = "deleting"
    
    # Audit Log: user.delete_store
    log = AuditLog(
        action="user.delete_store",
        resource_type="store",
        resource_id=str(store.id),
        ip_address=request.client.host,
        metadata_={"name": store.name}
    )
    db.add(log)
    await db.commit()
    
    # Trigger background deletion task here
    from app.services.orchestrator import deprovision_store
    
    background_tasks.add_task(deprovision_store, store.id)
    
    return {"message": "Store deletion initiated", "status": "deleting"}

@router.post("/{store_id}/retry", response_model=StoreResponse)
async def retry_store(
    store_id: uuid.UUID, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalars().first()
    
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
        
    if store.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed stores can be retried")
        
    store.status = "requested"
    store.error_message = None
    await db.commit()
    await db.refresh(store)
    
    from app.services.orchestrator import provision_store
    background_tasks.add_task(provision_store, store.id)
    
    return store

@router.get("/{store_id}/logs")
async def get_store_logs(store_id: uuid.UUID, limit: int = 50, db: AsyncSession = Depends(get_db)):
    from app.models import AuditLog
    # Fetch technical activity logs for specific store
    stmt = select(AuditLog).where(
        AuditLog.resource_id == str(store_id),
        (AuditLog.action.like('activity.%') | AuditLog.action.like('system.%'))
    ).order_by(AuditLog.created_at.asc()).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return logs



