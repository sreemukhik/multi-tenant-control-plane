from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Text, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    max_stores = Column(Integer, default=5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # Check spec regarding nullable
    name = Column(String(255), nullable=False)
    engine = Column(String(50), nullable=False) # woocommerce, medusa
    status = Column(String(50), nullable=False) # requested, provisioning, ready, failed, deleting
    namespace = Column(String(255), unique=True, nullable=False)
    domain = Column(String(255))
    admin_url = Column(String(255))
    # Direct access to password - V202
    admin_password = Column(String(255)) 
    storefront_url = Column(String(255))
    error_message = Column(Text)
    provisioning_started_at = Column(DateTime(timezone=True))
    provisioning_completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    __table_args__ = (
        Index('idx_stores_status', 'status'),
        Index('idx_stores_user_id', 'user_id'),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True) # BigSerial equivalent
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    ip_address = Column(INET) # SQLAlchemy supports INET
    metadata_ = Column("metadata", JSONB) # Metadata is reserved in Base
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_audit_logs_store_id', 'store_id'),
        Index('idx_audit_logs_created_at', 'created_at', postgresql_using='btree'), # desc handled in query usually, or specialized index
    )
