import json
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import List, Dict, Any
from backend.app.models.activity_log import ActivityLog

class ActivityLogRepository:
    """
    Append-only repository for the tamper-resistant activity_logs audit trail.
    Exposes insert and read methods ONLY (no update, no delete).
    Never stores or returns passwords or password hashes.
    """
    @staticmethod
    def insert(
        db: Session,
        action_type: str,
        entity_name: str,
        entity_id: int | None = None,
        user_id: int | None = None,
        details: Dict[str, Any] | None = None,
        ip_address: str | None = None,
        commit: bool = True
    ) -> ActivityLog:
        """
        Appends an immutable audit log record.
        Sensitive credentials (e.g. passwords, hashes) are strictly excluded from details.
        When commit=False, flushes without committing so callers can manage a single transaction.
        """
        # Ensure details dictionary never contains sensitive password fields
        sanitized_details = {}
        if details:
            for k, v in details.items():
                if "password" not in k.lower() and "hash" not in k.lower() and "secret" not in k.lower():
                    sanitized_details[k] = v

        log_entry = ActivityLog(
            user_id=user_id,
            action_type=action_type,
            entity_name=entity_name,
            entity_id=entity_id,
            details_json=json.dumps(sanitized_details),
            ip_address=ip_address
        )
        db.add(log_entry)
        if commit:
            db.commit()
            db.refresh(log_entry)
        else:
            db.flush()
        return log_entry

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[ActivityLog]:
        """Read activity logs ordered chronologically descending."""
        stmt = select(ActivityLog).order_by(desc(ActivityLog.timestamp)).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[ActivityLog]:
        """Read activity logs associated with a specific user."""
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .order_by(desc(ActivityLog.timestamp))
            .offset(skip)
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_by_entity(db: Session, entity_name: str, entity_id: int | None = None, limit: int = 100) -> List[ActivityLog]:
        """Read activity logs associated with a specific entity."""
        stmt = select(ActivityLog).where(ActivityLog.entity_name == entity_name)
        if entity_id is not None:
            stmt = stmt.where(ActivityLog.entity_id == entity_id)
        stmt = stmt.order_by(desc(ActivityLog.timestamp)).limit(limit)
        return list(db.execute(stmt).scalars().all())
