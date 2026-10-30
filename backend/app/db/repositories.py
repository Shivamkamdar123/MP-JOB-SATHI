from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.orm import (
    ApplicationRecord,
    AuditEventRecord,
    CompanySourceRecord,
    CuratorQueueRecord,
    FieldProvenanceRecord,
    JobFairRecord,
    NotificationRecord,
    PostRecord,
    PrivateJobRecord,
    ProfileRecord,
    ReminderRecord,
    SourceHashRecord,
    SourcePolicyRecord,
    UserRecord,
)
from app.models import Application, CompanySource, GovtNotification, JobFair, PrivateJob, UserProfile


def _dump(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _notification_data(record: NotificationRecord) -> GovtNotification:
    data = dict(record.data)
    data["posts"] = [dict(post.data) for post in record.posts]
    return GovtNotification.model_validate(data)


def _record_audit(
    session: Session,
    event_type: str,
    entity_type: str,
    entity_id: int | str,
    actor: str,
    payload: dict[str, Any],
) -> AuditEventRecord:
    event = AuditEventRecord(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        actor=actor,
        payload=payload,
    )
    session.add(event)
    return event


class NotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, notification: GovtNotification) -> NotificationRecord:
        data = _dump(notification)
        record = NotificationRecord(
            title=notification.title,
            status=notification.status,
            source_kind=notification.source_kind,
            is_fixture=notification.source_kind == "fixture",
            data=data,
        )
        record.posts = [PostRecord(title=post.title, data=post.model_dump(mode="json")) for post in notification.posts]
        self.session.add(record)
        self.session.flush()
        return record

    def add_extracted(self, notification: GovtNotification, actor: str = "system") -> NotificationRecord:
        record = self.create(notification)
        values = _dump(notification)
        metadata_fields = {
            "posts", "source_urls", "notification_pdf_url", "source_kind", "verified_at",
            "verified_by", "discrepancies", "status", "age_relaxation_combination",
            "review_required", "field_provenance",
        }
        tracked_fields = [field_name for field_name in values if field_name not in metadata_fields]
        for field_name in tracked_fields:
            value = values.get(field_name)
            provenance = notification.field_provenance.get(field_name)
            self.session.add(FieldProvenanceRecord(
                notification_id=record.id,
                field_name=field_name,
                field_value=value,
                source_url=notification.source_urls[0] if notification.source_urls else notification.notification_pdf_url,
                source_page=provenance.source_page if provenance else None,
                source_snippet=provenance.snippet if provenance else "",
                confidence=provenance.confidence if provenance else 0.0,
                method=provenance.method if provenance else "regex",
            ))
        for post_record, post in zip(record.posts, notification.posts):
            for field_name, value in _dump(post).items():
                if field_name == "field_provenance":
                    continue
                provenance = post.field_provenance.get(field_name)
                self.session.add(FieldProvenanceRecord(
                    notification_id=record.id,
                    post_id=post_record.id,
                    field_name=f"posts.{field_name}",
                    field_value=value,
                    source_url=notification.source_urls[0] if notification.source_urls else notification.notification_pdf_url,
                    source_page=provenance.source_page if provenance else None,
                    source_snippet=provenance.snippet if provenance else "",
                    confidence=provenance.confidence if provenance else 0.0,
                    method=provenance.method if provenance else "regex",
                ))
        if notification.review_required:
            threshold = float(os.getenv("EXTRACTION_CONFIDENCE_THRESHOLD", "0.7"))
            CatalogRepository(self.session).add_curator_item(
                "Auto-extracted, verify before applying.",
                {"title": notification.title, "field_provenance": {
                    name: item.model_dump(mode="json") for name, item in notification.field_provenance.items()
                    if item.confidence < threshold
                }},
                notification_id=record.id,
            )
        _record_audit(
            self.session,
            "extraction",
            "notification",
            record.id,
            actor,
            {"source_kind": notification.source_kind, "title": notification.title},
        )
        self.session.commit()
        return record

    def get_record_by_pdf_url(self, pdf_url: str) -> NotificationRecord | None:
        return self.session.scalar(
            select(NotificationRecord)
            .join(SourceHashRecord, SourceHashRecord.notification_id == NotificationRecord.id)
            .where(SourceHashRecord.source_url == pdf_url)
        )

    def get(self, notification_id: int) -> GovtNotification | None:
        record = self.session.scalar(
            select(NotificationRecord)
            .options(selectinload(NotificationRecord.posts))
            .where(NotificationRecord.id == notification_id)
        )
        return _notification_data(record) if record else None

    def get_record(self, notification_id: int) -> NotificationRecord | None:
        return self.session.scalar(
            select(NotificationRecord)
            .options(selectinload(NotificationRecord.posts))
            .where(NotificationRecord.id == notification_id)
        )

    def list(self, include_closed: bool = True, include_fixtures: bool = True) -> list[GovtNotification]:
        query = select(NotificationRecord).options(selectinload(NotificationRecord.posts)).order_by(NotificationRecord.id)
        if not include_closed:
            query = query.where(or_(NotificationRecord.status != "closed", NotificationRecord.status.is_(None)))
        if not include_fixtures:
            query = query.where(NotificationRecord.source_kind != "fixture")
        return [_notification_data(item) for item in self.session.scalars(query).unique()]

    def list_with_ids(self, include_closed: bool = True, include_fixtures: bool = True) -> list[tuple[int, GovtNotification]]:
        query = select(NotificationRecord).options(selectinload(NotificationRecord.posts)).order_by(NotificationRecord.id)
        if not include_closed:
            query = query.where(or_(NotificationRecord.status != "closed", NotificationRecord.status.is_(None)))
        if not include_fixtures:
            query = query.where(NotificationRecord.source_kind != "fixture")
        return [(record.id, _notification_data(record)) for record in self.session.scalars(query).unique()]

    def verify(self, notification_id: int, actor: str, source_url: str | None = None) -> GovtNotification | None:
        record = self.get_record(notification_id)
        if record is None:
            return None
        notification = _notification_data(record)
        notification.verified_at = datetime.now(timezone.utc).isoformat()
        notification.verified_by = "curator"
        notification.source_kind = "official"
        notification.review_required = False
        if source_url and source_url not in notification.source_urls:
            notification.source_urls.append(source_url)
        record.source_kind = "official"
        record.is_fixture = False
        record.data = _dump(notification)
        _record_audit(self.session, "verification", "notification", record.id, actor, {"source_url": source_url})
        self.session.commit()
        return notification

    def curator_edit(self, notification_id: int, changes: dict[str, Any], actor: str) -> GovtNotification | None:
        record = self.get_record(notification_id)
        if record is None:
            return None
        current = _notification_data(record)
        merged = {**_dump(current), **changes}
        if current.verified_by == "curator":
            merged["verified_by"] = "curator"
            merged["verified_at"] = datetime.now(timezone.utc).isoformat()
            if "review_required" not in changes:
                merged["review_required"] = False
        updated = GovtNotification.model_validate(merged)
        record.title = updated.title
        record.status = updated.status
        record.source_kind = updated.source_kind
        record.is_fixture = updated.source_kind == "fixture"
        record.data = _dump(updated)
        record.posts.clear()
        record.posts.extend(PostRecord(title=post.title, data=post.model_dump(mode="json")) for post in updated.posts)
        _record_audit(self.session, "curator_edit", "notification", record.id, actor, {"fields": sorted(changes)})
        self.session.commit()
        return updated


class CatalogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_companies(self) -> list[CompanySource]:
        records = self.session.scalars(select(CompanySourceRecord).order_by(CompanySourceRecord.name)).all()
        return [CompanySource.model_validate(record.data) for record in records]

    def add_company(self, company: CompanySource) -> CompanySourceRecord:
        record = CompanySourceRecord(name=company.name, city=company.city, is_fixture=company.is_fixture, data=_dump(company))
        self.session.add(record)
        return record

    def list_private_jobs(self) -> list[PrivateJob]:
        records = self.session.scalars(select(PrivateJobRecord).order_by(PrivateJobRecord.title)).all()
        return [PrivateJob.model_validate(record.data) for record in records]

    def add_private_job(self, job: PrivateJob) -> PrivateJobRecord:
        record = PrivateJobRecord(title=job.title, company=job.company, city=job.city, is_fixture=job.is_fixture, data=_dump(job))
        self.session.add(record)
        return record

    def list_job_fairs(self) -> list[JobFair]:
        records = self.session.scalars(select(JobFairRecord).order_by(JobFairRecord.title)).all()
        return [JobFair.model_validate(record.data) for record in records]

    def add_job_fair(self, fair: JobFair) -> JobFairRecord:
        record = JobFairRecord(title=fair.title, district=fair.district, is_fixture=fair.is_fixture, data=_dump(fair))
        self.session.add(record)
        return record

    def list_source_policies(self) -> list[SourcePolicyRecord]:
        return list(self.session.scalars(select(SourcePolicyRecord).order_by(SourcePolicyRecord.source_kind)).all())

    def add_source_policy(self, source_kind: str, policy: dict[str, Any], enabled: bool = True) -> SourcePolicyRecord:
        record = SourcePolicyRecord(source_kind=source_kind, policy=policy, enabled=enabled)
        self.session.add(record)
        return record

    def record_source_hash(self, source_url: str, content_sha256: str, notification_id: int | None = None) -> None:
        record = self.session.scalar(select(SourceHashRecord).where(SourceHashRecord.source_url == source_url))
        if record is None:
            record = SourceHashRecord(source_url=source_url, content_sha256=content_sha256, notification_id=notification_id)
            self.session.add(record)
        else:
            record.content_sha256 = content_sha256
            record.notification_id = notification_id
            record.fetched_at = datetime.now(timezone.utc)

    def get_source_hash(self, source_url: str) -> str | None:
        record = self.session.scalar(select(SourceHashRecord).where(SourceHashRecord.source_url == source_url))
        return record.content_sha256 if record else None

    def add_curator_item(self, reason: str, data: dict[str, Any], notification_id: int | None = None) -> CuratorQueueRecord:
        record = CuratorQueueRecord(notification_id=notification_id, reason=reason, data=data)
        self.session.add(record)
        return record


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_profile(self, profile: UserProfile, user_id: int | None = None, email: str | None = None) -> ProfileRecord:
        if user_id is not None:
            user = self.session.get(UserRecord, user_id)
            if user is None:
                raise LookupError("User not found")
        else:
            user = self.session.scalar(select(UserRecord).where(UserRecord.email == email)) if email else None
            if user is None:
                user = UserRecord(email=email)
                self.session.add(user)
                self.session.flush()
        record = self.session.scalar(select(ProfileRecord).where(ProfileRecord.user_id == user.id))
        if record is None:
            record = ProfileRecord(user_id=user.id, name=profile.name, data=_dump(profile))
            self.session.add(record)
        else:
            record.name = profile.name
            record.data = _dump(profile)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_profile(self, user_id: int) -> UserProfile | None:
        record = self.session.scalar(select(ProfileRecord).where(ProfileRecord.user_id == user_id))
        return UserProfile.model_validate(record.data) if record else None

    def exists(self, user_id: int) -> bool:
        return self.session.get(UserRecord, user_id) is not None


class ApplicationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, application: Application, user_id: int | None = None, notification_id: int | None = None) -> ApplicationRecord:
        data = _dump(application)
        record = ApplicationRecord(
            user_id=user_id,
            notification_id=notification_id,
            job_title=application.job_title,
            organization=application.organization,
            stage=application.stage,
            status=application.status,
            data=data,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def list(self, user_id: int | None = None) -> list[ApplicationRecord]:
        query = select(ApplicationRecord).order_by(ApplicationRecord.id)
        if user_id is not None:
            query = query.where(ApplicationRecord.user_id == user_id)
        return list(self.session.scalars(query).all())

    def exists(self, application_id: int) -> bool:
        return self.session.get(ApplicationRecord, application_id) is not None

    def add_reminders(self, reminders: list[dict[str, str]], user_id: int | None = None, application_id: int | None = None) -> list[ReminderRecord]:
        records = [ReminderRecord(
            user_id=user_id,
            application_id=application_id,
            title=item["title"],
            kind=item["kind"],
            due_date=item["date"],
            message=item["message"],
        ) for item in reminders]
        self.session.add_all(records)
        self.session.commit()
        return records


def record_audit_event(session: Session, event_type: str, entity_type: str, entity_id: int | str, actor: str, payload: dict[str, Any]) -> AuditEventRecord:
    event = _record_audit(session, event_type, entity_type, entity_id, actor, payload)
    session.commit()
    return event


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[AuditEventRecord]:
        return list(self.session.scalars(select(AuditEventRecord).order_by(AuditEventRecord.id)).all())
