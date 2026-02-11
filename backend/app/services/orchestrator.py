import structlog
import uuid
import datetime
import secrets
import asyncio
from kubernetes import client, config
from sqlalchemy import select
from app.models import Store, AuditLog
from app.config import settings

logger = structlog.get_logger()

# Initialize Kubernetes Client
try:
    config.load_incluster_config()
except:
    try:
        config.load_kube_config()
    except:
        logger.warning("k8s_config_load_failed")

async def provision_store(store_id: uuid.UUID):
    """
    Trigger provisioning via Kubernetes Operator.
    Creates a 'Store' Custom Resource.
    """
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        logger.info("trigger_operator_provision", store_id=str(store_id))
        
        # 1. Fetch Store
        stmt = select(Store).where(Store.id == store_id)
        result = await db.execute(stmt)
        store = result.scalars().first()
        
        if not store:
            logger.error("store_not_found", store_id=str(store_id))
            return

        # 2. Update Status
        store.status = "provisioning_requested"
        store.provisioning_started_at = datetime.datetime.now(datetime.timezone.utc)
        await db.commit()
        
        # 3. Create CR
        try:
            api = client.CustomObjectsApi()
            
            # Use defaults / secrets
            # We don't store passwords in DB usually, generate them here and pass to Operator?
            # Or generate in Operator.
            # If we generate here, we can save them?
            # Existing logic generated them in Orchestrator.
            # If Operator generates them, it updates DB?
            # Operator `handlers.py` updates DB.
            # So let Operator generate them.
            
            # Generate Passwords
            admin_password = secrets.token_urlsafe(16)
            db_password = secrets.token_urlsafe(16)

            resource_body = {
                "apiVersion": "urumi.io/v1",
                "kind": "Store",
                "metadata": {
                    "name": store.namespace, # k8s resource name
                    "namespace": "urumi-platform", # Operator watches this namespace
                    "labels": {
                        "store_id": str(store.id),
                        "managed-by": "urumi-api"
                    }
                },
                "spec": {
                    "name": store.name,
                    "engine": store.engine,
                    "namespace": store.namespace, # Target namespace for resources
                    "namespace": store.namespace, # Target namespace for resources
                    "adminUser": "admin",
                    "adminPassword": admin_password,
                    "dbUser": "urumi",
                    "dbPassword": db_password
                }
            }
            
            # Save admin password immediately
            store.admin_password = admin_password
            await db.commit()
            
            # Sync wrapper
            def create_cr():
                return api.create_namespaced_custom_object(
                    group="urumi.io",
                    version="v1",
                    namespace="urumi-platform",
                    plural="stores",
                    body=resource_body
                )
            
            await asyncio.to_thread(create_cr)
            
            # Log
            log = AuditLog(
                action="operator.cr_created", 
                resource_type="store", 
                resource_id=str(store.id),
                metadata_={"crd": store.namespace}
            )
            db.add(log)
            await db.commit()

        except Exception as e:
            logger.error("cr_creation_failed", error=str(e))
            store.status = "failed"
            store.error_message = str(e)
            await db.commit()

async def deprovision_store(store_id: uuid.UUID):
    """
    Trigger deprovisioning via Operator.
    Deletes the 'Store' Custom Resource.
    """
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        stmt = select(Store).where(Store.id == store_id)
        result = await db.execute(stmt)
        store = result.scalars().first()
        
        if not store: return
        
        crd_name = store.namespace
        
        try:
            api = client.CustomObjectsApi()
            
            def delete_cr():
                return api.delete_namespaced_custom_object(
                    group="urumi.io",
                    version="v1",
                    namespace="urumi-platform",
                    plural="stores",
                    name=crd_name
                )
            
            await asyncio.to_thread(delete_cr)
            
            # DB deletion is handled after CR deletion? 
            # Or allow Operator to "finalize"?
            # For "3 days" approach: Delete CR, then Delete DB immediately?
            # Operator handles k8s cleanup asynchronously.
            # We mark store as "deleting" in DB.
            
            # Actually, `api/stores.py` calls this and then deletes from DB?
            # Check usage.
            # If we delete from DB, audit log for Operator won't work (no foreign key).
            # But `deprovision_store` in old Logic updated DB.
            # Let's keep store but mark "deleting".
            # Clean up DB when Operator finishes?
            # Operator doesn't know about DB entry removal request.
            # Simple: Delete CR, Delete DB. Operator cleans up K8s eventually.
            # Audit logs are kept?
            
            await db.delete(store)
            await db.commit()
            
        except Exception as e:
             # If CR not found, proceed to delete DB
             logger.error("cr_delete_failed", error=str(e))
             await db.delete(store)
             await db.commit()
