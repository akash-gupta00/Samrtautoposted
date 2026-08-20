from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user

from app.models.user import User

from app.schemas.permission import PermissionResponse

from app.services.permission_service import PermissionService


router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)

permission_service = PermissionService()


@router.post(
    "/seed",
)
def seed_permissions(
    db: Session = Depends(get_db),
):
    """
    Default permissions create karega.
    Sirf ek baar chalana hai.
    """

    return permission_service.seed_default_permissions(
        db=db,
    )


@router.get(
    "",
    response_model=list[PermissionResponse],
)
def list_permissions(
    module: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Saari permissions return karega.
    """

    return permission_service.list_permissions(
        db=db,
        module=module,
    )


@router.get(
    "/{permission_id}",
    response_model=PermissionResponse,
)
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
):
    """
    Single permission return karega.
    """

    return permission_service.get_permission(
        db=db,
        permission_id=permission_id,
    )


@router.post(
    "/roles/{role_id}/assign/{permission_id}",
)
def assign_permission(
    role_id: int,
    permission_id: int,
    organization_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Role ko permission assign karega.
    """

    return permission_service.assign_permission_to_role(
        db=db,
        role_id=role_id,
        permission_id=permission_id,
        organization_id=organization_id,
        current_user=current_user,
        request=request,
    )


@router.delete(
    "/roles/{role_id}/remove/{permission_id}",
)
def remove_permission(
    role_id: int,
    permission_id: int,
    organization_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Role se permission remove karega.
    """

    return permission_service.remove_permission_from_role(
        db=db,
        role_id=role_id,
        permission_id=permission_id,
        organization_id=organization_id,
        current_user=current_user,
        request=request,
    )


@router.get(
    "/roles/{role_id}",
    response_model=list[PermissionResponse],
)
def role_permissions(
    role_id: int,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Role ki saari permissions.
    """

    return permission_service.get_role_permissions(
        db=db,
        role_id=role_id,
        organization_id=organization_id,
        current_user=current_user,
    )