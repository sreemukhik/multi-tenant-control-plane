from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Store, AuditLog
import asyncio
from kubernetes import client, config
import shutil

router = APIRouter()

@router.get("/health")
async def get_platform_health(db: AsyncSession = Depends(get_db)):
    """
    Check core platform components health.
    """
    health = {
        "database": "Disconnected",
        "kubernetes_api": "Disconnected",
        "helm_cli": "Missing",
        "status": "Healthy"
    }
    
    # 1. Check Database
    try:
        await db.execute(select(1))
        health["database"] = "Connected"
    except Exception as e:
        health["database"] = f"Error: {str(e)}"
        health["status"] = "Degraded"

    # 2. Check Kubernetes
    try:
        # Simple list namespaces to verify connectivity
        def check_k8s():
            api = client.CoreV1Api()
            return api.list_namespace(timeout_seconds=2)
        
        await asyncio.to_thread(check_k8s)
        health["kubernetes_api"] = "Connected"
    except Exception as e:
        health["kubernetes_api"] = f"Error: {str(e)}"
        health["status"] = "Degraded"

    # 3. Check Helm CLI
    helm_path = shutil.which("helm")
    if helm_path:
        health["helm_cli"] = "Available"
    else:
        health["status"] = "Degraded"

    return health

@router.get("/metrics")
async def get_platform_metrics(db: AsyncSession = Depends(get_db)):
    """
    Aggregate system metrics from DB.
    """
    # 1. Basic Counts
    total_result = await db.execute(select(func.count()).select_from(Store))
    total_stores = total_result.scalar() or 0

    failed_result = await db.execute(select(func.count()).select_from(Store).where(Store.status == "failed"))
    failed_stores = failed_result.scalar() or 0

    active_ns_result = await db.execute(select(func.count(Store.namespace.distinct())).select_from(Store).where(Store.status == "ready"))
    active_namespaces = active_ns_result.scalar() or 0

    # 2. Average Provisioning Time (in seconds)
    avg_time = 0
    try:
        # Cross-DB approach for average provisioning time
        stmt = select(Store).where(
            Store.status == "ready", 
            Store.provisioning_started_at.isnot(None),
            Store.provisioning_completed_at.isnot(None)
        )
        result = await db.execute(stmt)
        stores = result.scalars().all()
        
        if stores:
            durations = [
                (s.provisioning_completed_at - s.provisioning_started_at).total_seconds()
                for s in stores
            ]
            avg_time = sum(durations) / len(durations)
    except Exception as e:
        print(f"Metrics calc error: {e}")
        avg_time = "N/A"

    return {
        "total_stores": total_stores,
        "failed_stores": failed_stores,
        "active_namespaces": active_namespaces,
        "avg_provisioning_time_seconds": round(avg_time, 2) if isinstance(avg_time, (int, float)) else avg_time,
        "success_rate": round(((total_stores - failed_stores) / total_stores * 100), 1) if total_stores > 0 else 100
    }
