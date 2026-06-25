"""
Database schema.

Tables: users, appointments, documents, document_chunks, sessions, messages, analytics_events
Relationships:
  - User 1---N Appointment
  - User 1---N Session
  - Session 1---N Message
  - Document 1---N DocumentChunk
"""
import uuid
import datetime as dt
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    appointments = relationship("Appointment", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    appointment_date = Column(String, nullable=False)  # YYYY-MM-DD
    original_date_text = Column(String, nullable=True)
    status = Column(String, default="CONFIRMED")  # CONFIRMED, CANCELLED, COMPLETED
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    user = relationship("User", back_populates="appointments")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_uuid)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    num_pages = Column(Integer, default=0)
    num_chunks = Column(Integer, default=0)
    size_bytes = Column(Integer, default=0)
    status = Column(String, default="PROCESSING")  # PROCESSING, READY, FAILED
    uploaded_at = Column(DateTime, default=dt.datetime.utcnow)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=gen_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    vector_id = Column(String, nullable=True)  # id in chroma collection

    document = relationship("Document", back_populates="chunks")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    booking_state = Column(String, default="IDLE")
    booking_draft = Column(JSON, default=dict)  # partial appointment fields in progress
    last_active = Column(DateTime, default=dt.datetime.utcnow)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    agent = Column(String, nullable=True)  # which agent produced this (assistant only)
    meta = Column(JSON, default=dict)  # citations, confidence, etc.
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    session = relationship("Session", back_populates="messages")


class AnalyticsEvent(Base):
    __tablename__ = "analytics"

    id = Column(String, primary_key=True, default=gen_uuid)
    event_type = Column(String, nullable=False)  # chat, appointment, document_upload, agent_call
    agent = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
