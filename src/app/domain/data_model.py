from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Uuid, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import JSON
import uuid

Base = declarative_base()

class CanonicalThread(Base):
    __tablename__ = 'canonical_thread'
    id = Column(Uuid, primary_key=True, nullable=False, default=uuid.uuid4) # uuid
    parent_id = Column(Uuid, ForeignKey('canonical_thread.id'), nullable=True) # self-contained
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Document(Base):
    __tablename__ = 'document'
    id = Column(Uuid, primary_key=True, nullable=False, default=uuid.uuid4) # uuid
    file_name = Column(String(255), nullable=False, index=True)
    cano_id = Column(Uuid, ForeignKey('canonical_thread.id'), nullable=False, index=True)
    email_metadata = Column(Text, nullable=True) # raw email content
    hash_chain = Column(Text, nullable=True) # simhash
    parent_hash_chain = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    action_type = Column(String(50), nullable=False) # db operation, kafka, api calls
    action = Column(String(50), nullable=False) # INSERT/UPDATE, Pub/Sub
    action_content = Column(JSON, nullable=True) # serialized object
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

