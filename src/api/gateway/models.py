from sqlalchemy import Column, ForeignKey, Integer, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from gateway.database import Base

class Recording(Base):
    __tablename__ = "recordings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    sample_rate = Column(Integer, nullable=False)
    channel_count = Column(Integer, nullable=False)
    file_extension = Column(Text, nullable=False)
    fragments = relationship("Fragment", back_populates="recording", cascade="all, delete-orphan")

class Fragment(Base):
    __tablename__ = "fragments"
    recording_id = Column(UUID(as_uuid=True), ForeignKey("recordings.id", ondelete="CASCADE"), primary_key=True)
    index = Column(Integer, primary_key=True)
    sample_number = Column(Integer, nullable=False)
    recording = relationship("Recording", back_populates="fragments")