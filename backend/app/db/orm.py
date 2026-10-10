from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class NotificationRecord(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    source_kind: Mapped[str] = mapped_column(String(30), default="fixture", index=True)
    is_fixture: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    posts: Mapped[list[PostRecord]] = relationship(back_populates="notification", cascade="all, delete-orphan")


class PostRecord(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notification_id: Mapped[int] = mapped_column(ForeignKey("notifications.id", ondelete="CASCADE"), index=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    notification: Mapped[NotificationRecord] = relationship(back_populates="posts")
    provenance: Mapped[list[FieldProvenanceRecord]] = relationship(back_populates="post", cascade="all, delete-orphan")


class FieldProvenanceRecord(Base):
    __tablename__ = "field_provenance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notification_id: Mapped[int] = mapped_column(ForeignKey("notifications.id", ondelete="CASCADE"), index=True)
    post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True)
    field_name: Mapped[str] = mapped_column(String(255), index=True)
    field_value: Mapped[Any] = mapped_column(JSON, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    method: Mapped[str] = mapped_column(String(20), default="regex")
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    post: Mapped[PostRecord | None] = relationship(back_populates="provenance")


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    profile: Mapped[ProfileRecord | None] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    applications: Mapped[list[ApplicationRecord]] = relationship(back_populates="user")


class ProfileRecord(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    user: Mapped[UserRecord] = relationship(back_populates="profile")


class ApplicationRecord(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    notification_id: Mapped[int | None] = mapped_column(ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True, index=True)
    job_title: Mapped[str] = mapped_column(String(500))
    organization: Mapped[str] = mapped_column(String(500))
    stage: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    user: Mapped[UserRecord | None] = relationship(back_populates="applications")
    reminders: Mapped[list[ReminderRecord]] = relationship(back_populates="application", cascade="all, delete-orphan")


class ReminderRecord(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(80), index=True)
    due_date: Mapped[str] = mapped_column(String(80), index=True)
    message: Mapped[str] = mapped_column(Text)
    application: Mapped[ApplicationRecord | None] = relationship(back_populates="reminders")


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[str] = mapped_column(String(100), index=True)
    actor: Mapped[str] = mapped_column(String(255), default="system")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class CompanySourceRecord(Base):
    __tablename__ = "company_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    city: Mapped[str] = mapped_column(String(255), index=True)
    is_fixture: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class PrivateJobRecord(Base):
    __tablename__ = "private_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    company: Mapped[str] = mapped_column(String(255), index=True)
    city: Mapped[str] = mapped_column(String(255), index=True)
    is_fixture: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class JobFairRecord(Base):
    __tablename__ = "job_fairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    district: Mapped[str] = mapped_column(String(255), index=True)
    is_fixture: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class SourcePolicyRecord(Base):
    __tablename__ = "source_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_kind: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    policy: Mapped[dict[str, Any]] = mapped_column(JSON)


class SourceHashRecord(Base):
    __tablename__ = "source_hashes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_url: Mapped[str] = mapped_column(Text, unique=True, index=True)
    content_sha256: Mapped[str] = mapped_column(String(64))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    notification_id: Mapped[int | None] = mapped_column(ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True, index=True)


class CuratorQueueRecord(Base):
    __tablename__ = "curator_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notification_id: Mapped[int | None] = mapped_column(ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    reason: Mapped[str] = mapped_column(Text)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
