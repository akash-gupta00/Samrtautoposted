from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.audit_log import AuditLogCreate, AuditLogResponse
from app.services.audit_log_service import AuditLogService


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.post(
    "/",
    response_model=AuditLogResponse,
)
def create_audit_log(
    audit_data: AuditLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AuditLogService.create_log(
        db=db,
        audit_data=audit_data,
    )


@router.get(
    "/",
    response_model=list[AuditLogResponse],
)
def list_audit_logs(
    organization_id: int | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AuditLogService.get_logs(
        db=db,
        organization_id=organization_id,
        user_id=user_id,
    )


@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
def get_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AuditLogService.get_log(
        db=db,
        audit_log_id=audit_log_id,
    )


@router.delete(
    "/{audit_log_id}",
)
def delete_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AuditLogService.delete_log(
        db=db,
        audit_log_id=audit_log_id,
    )