from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime
import uuid

# --- Shared Models ---

class StoreBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    engine: str = Field(..., pattern='^(woocommerce|medusa)$')

    @validator('name')
    def validate_name(cls, v):
        if not v.replace('-', '').isalnum():
            raise ValueError('Name must be alphanumeric + hyphens')
        return v.lower()

class StoreCreate(StoreBase):
    pass

class StoreResponse(StoreBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    status: str
    namespace: str
    domain: Optional[str] = None
    admin_url: Optional[str] = None
    admin_password: Optional[str] = None
    storefront_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    provisioning_started_at: Optional[datetime] = None
    provisioning_completed_at: Optional[datetime] = None
    provisioning_timeline: Optional[List[dict]] = None
    activity_log: Optional[List[dict]] = None

    class Config:
        from_attributes = True

class StoreUpdate(BaseModel):
    pass # Currently only status updates happen internally

# --- Audit Log Models ---

class AuditLogResponse(BaseModel):
    id: int
    action: str
    created_at: datetime
    metadata: Optional[dict] = Field(None, alias="metadata_") 

    class Config:
        from_attributes = True
