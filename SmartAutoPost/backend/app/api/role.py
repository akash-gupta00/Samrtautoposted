from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
)
from sqlalchemy.orm import Session

from app.database.session import get_db

from app.dependencies.auth import (
    get_current_user,
)

from app.models.user import User

from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
)

from app.services.role_service import (
    RoleService,
)


router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)

role_service = RoleService()


@router.post(
    "",
    response_model=RoleResponse,
    status_code=201,
)
def create_role(
    role_data: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create new role.
    """

    return role_service.create_role(
        db=db,
        role_data=role_data,
        current_user=current_user,
        request=request,
    )


@router.get(
    "",
    response_model=list[RoleResponse],
)
def list_roles(
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all roles.
    """

    return role_service.list_roles(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
def get_role(
    role_id: int,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get single role.
    """

    return role_service.get_role(
        db=db,
        role_id=role_id,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    request: Request,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update role.
    """

    return role_service.update_role(
        db=db,
        role_id=role_id,
        organization_id=organization_id,
        role_data=role_data,
        current_user=current_user,
        request=request,
    )


@router.delete(
    "/{role_id}",
)
def delete_role(
    role_id: int,
    request: Request,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete role.
    """

    return role_service.delete_role(
        db=db,
        role_id=role_id,
        organization_id=organization_id,
        current_user=current_user,
        request=request,
    )