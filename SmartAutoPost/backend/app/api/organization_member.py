from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember

from app.schemas.organization_member import MemberInvite
from app.schemas.audit_log import AuditLogCreate

from app.services.audit_log_service import AuditLogService


router = APIRouter(
    prefix="/organizations",
    tags=["Organization Members"],
)


def create_member_audit_log(
    db: Session,
    request: Request,
    current_user: User,
    organization_id: int,
    action: str,
    entity_id: int | None = None,
    details: dict | None = None,
):
    """
    Organization member related important actions
    audit_logs table me save karega.
    """

    try:
        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action=action,
                entity_type="organization_member",
                entity_id=entity_id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get("user-agent"),
                details=details,
            ),
        )

    except Exception as error:
        db.rollback()
        print(f"Organization member audit log error: {error}")


@router.post("/{organization_id}/members")
def add_member(
    organization_id: int,
    member_data: MemberInvite,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    if organization.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only owner can add members",
        )

    user_to_add = (
        db.query(User)
        .filter(User.email == member_data.email)
        .first()
    )

    if not user_to_add:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    existing_member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_to_add.id,
        )
        .first()
    )

    if existing_member:
        raise HTTPException(
            status_code=400,
            detail="User already member of this organization",
        )

    new_member = OrganizationMember(
        organization_id=organization_id,
        user_id=user_to_add.id,
        role=member_data.role,
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    create_member_audit_log(
        db=db,
        request=request,
        current_user=current_user,
        organization_id=organization_id,
        action="member_added",
        entity_id=new_member.id,
        details={
            "member_id": new_member.id,
            "user_id": user_to_add.id,
            "name": user_to_add.name,
            "email": user_to_add.email,
            "role": new_member.role,
        },
    )

    return {
        "message": "Member added successfully",
        "member_id": new_member.id,
        "user_id": new_member.user_id,
        "role": new_member.role,
    }


@router.get("/{organization_id}/members")
def list_members(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    current_member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id,
        )
        .first()
    )

    is_owner = organization.owner_id == current_user.id

    if not is_owner and not current_member:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to view members",
        )

    members = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id
        )
        .all()
    )

    result = []

    for member in members:
        user = (
            db.query(User)
            .filter(User.id == member.user_id)
            .first()
        )

        result.append(
            {
                "member_id": member.id,
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": member.role,
            }
        )

    return result


@router.put("/{organization_id}/members/{member_id}")
def update_member_role(
    organization_id: int,
    member_id: int,
    member_data: MemberInvite,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    if organization.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only owner can update member roles",
        )

    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == organization_id,
        )
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )

    member_user = (
        db.query(User)
        .filter(User.id == member.user_id)
        .first()
    )

    old_role = member.role
    member.role = member_data.role

    db.commit()
    db.refresh(member)

    create_member_audit_log(
        db=db,
        request=request,
        current_user=current_user,
        organization_id=organization_id,
        action="member_role_updated",
        entity_id=member.id,
        details={
            "member_id": member.id,
            "user_id": member.user_id,
            "email": member_user.email if member_user else None,
            "old_role": old_role,
            "new_role": member.role,
        },
    )

    return {
        "message": "Member role updated successfully",
        "member_id": member.id,
        "user_id": member.user_id,
        "role": member.role,
    }


@router.delete("/{organization_id}/members/{member_id}")
def remove_member(
    organization_id: int,
    member_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    if organization.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only owner can remove members",
        )

    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == organization_id,
        )
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )

    member_user = (
        db.query(User)
        .filter(User.id == member.user_id)
        .first()
    )

    removed_member_data = {
        "member_id": member.id,
        "user_id": member.user_id,
        "name": member_user.name if member_user else None,
        "email": member_user.email if member_user else None,
        "role": member.role,
    }

    create_member_audit_log(
        db=db,
        request=request,
        current_user=current_user,
        organization_id=organization_id,
        action="member_removed",
        entity_id=member.id,
        details=removed_member_data,
    )

    db.delete(member)
    db.commit()

    return {
        "message": "Member removed successfully"
    }