from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.role import RoleResponse
from app.services.member_role_service import MemberRoleService

router = APIRouter(
    prefix="/member-roles",
    tags=["Member Roles"],
)


@router.post("/members/{member_id}/assign/{role_id}")
def assign_role(
    member_id: int,
    role_id: int,
    request: Request,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MemberRoleService.assign_role(
        db=db,
        member_id=member_id,
        role_id=role_id,
        organization_id=organization_id,
        current_user=current_user,
        request=request,
    )


@router.delete("/members/{member_id}/remove/{role_id}")
def remove_role(
    member_id: int,
    role_id: int,
    request: Request,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MemberRoleService.remove_role(
        db=db,
        member_id=member_id,
        role_id=role_id,
        organization_id=organization_id,
        current_user=current_user,
        request=request,
    )


@router.get(
    "/members/{member_id}",
    response_model=list[RoleResponse],
)
def get_member_roles(
    member_id: int,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MemberRoleService.member_roles(
        db=db,
        member_id=member_id,
        organization_id=organization_id,
        current_user=current_user,
    )