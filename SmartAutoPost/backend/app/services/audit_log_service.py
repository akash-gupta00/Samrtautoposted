from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate


class AuditLogService:

    @staticmethod
    def create_log(
        db: Session,
        audit_data: AuditLogCreate,
    ):
        audit_log = AuditLog(
            user_id=audit_data.user_id,
            organization_id=audit_data.organization_id,
            action=audit_data.action,
            entity_type=audit_data.entity_type,
            entity_id=audit_data.entity_id,
            ip_address=audit_data.ip_address,
            user_agent=audit_data.user_agent,
            details=audit_data.details,
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    @staticmethod
    def get_logs(
        db: Session,
        organization_id: int | None = None,
        user_id: int | None = None,
    ):
        query = db.query(AuditLog)

        if organization_id:
            query = query.filter(
                AuditLog.organization_id == organization_id
            )

        if user_id:
            query = query.filter(
                AuditLog.user_id == user_id
            )

        return (
            query.order_by(
                AuditLog.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def get_log(
        db: Session,
        audit_log_id: int,
    ):
        return (
            db.query(AuditLog)
            .filter(
                AuditLog.id == audit_log_id
            )
            .first()
        )

    @staticmethod
    def delete_log(
        db: Session,
        audit_log_id: int,
    ):
        audit_log = (
            db.query(AuditLog)
            .filter(
                AuditLog.id == audit_log_id
            )
            .first()
        )

        if not audit_log:
            return {
                "message": "Audit log not found"
            }

        db.delete(audit_log)
        db.commit()

        return {
            "message": "Audit log deleted successfully"
        }