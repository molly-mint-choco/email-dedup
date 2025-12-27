from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Uuid, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from datetime import datetime, timezone
import json
import uuid

Base = declarative_base()

class CanonicalThread(Base):
    __tablename__ = 'CanonicalThread'
    id = Column(Uuid, primary_key=True, nullable=False, default=uuid.uuid4) # uuid
    parent_id = Column(Uuid, ForeignKey('canonical_thread.id'), nullable=True) # self-contained
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

class Document(Base):
    __tablename__ = 'Document'
    id = Column(Uuid, primary_key=True, nullable=False, default=uuid.uuid4) # uuid
    file_name = Column(String(255), nullable=False, index=True)
    cano_id = Column(Uuid, ForeignKey('CanonicalThread.id'), nullable=False, index=True)
    metadata = Column(Text, nullable=True) # raw email content
    hash_chain = Column(Text, nullable=True) # simhash
    parent_hash_chain = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)





    
