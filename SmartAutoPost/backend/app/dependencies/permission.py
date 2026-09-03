from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.organization_member_role import OrganizationMemberRole
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import User


def check_user_permission(
    db: Session,
    current_user: User,
    organization_id: int,
    permission_name: str,
) -> bool:
    """
    Check karega ki current user ke paas kisi organization ke andar
    required permission hai ya nahi.

    Example:
        permission_name = "posts.create"
    """

    # Organization database me exist karti hai ya nahi.
    organization = (
        db.query(Organization)
        .filter(
            Organization.id == organization_id
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    # Temporary debug information.
    # Ye terminal me batayega request kis user se aa rahi hai
    # aur organization ka actual owner kaun hai.
    print("======================================")
    print("PERMISSION CHECK STARTED")
    print("CURRENT USER ID:", current_user.id)
    print("CURRENT USER EMAIL:", current_user.email)
    print("ORGANIZATION ID:", organization.id)
    print("ORGANIZATION OWNER ID:", organization.owner_id)
    print("REQUIRED PERMISSION:", permission_name)
    print("======================================")

    # Organization owner ko saari permissions automatically milengi.
    if organization.owner_id == current_user.id:
        print("RESULT: USER IS ORGANIZATION OWNER")
        print("PERMISSION ALLOWED")
        return True

    # Current user organization ka member hai ya nahi.
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id,
        )
        .first()
    )

    if not member:
        print("RESULT: USER IS NOT AN ORGANIZATION MEMBER")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization.",
        )

    print("MEMBER ID:", member.id)

    # Member ko kaun-kaun se roles assign hain, debug ke liye dekhenge.
    assigned_roles = (
        db.query(OrganizationMemberRole)
        .filter(
            OrganizationMemberRole.member_id == member.id
        )
        .all()
    )

    print(
        "ASSIGNED ROLE IDS:",
        [member_role.role_id for member_role in assigned_roles],
    )

    # Member ke assigned roles ke through required permission check karenge.
    permission_exists = (
        db.query(Permission)
        .join(
            RolePermission,
            RolePermission.permission_id == Permission.id,
        )
        .join(
            OrganizationMemberRole,
            OrganizationMemberRole.role_id == RolePermission.role_id,
        )
        .filter(
            OrganizationMemberRole.member_id == member.id,
            Permission.name == permission_name,
        )
        .first()
    )

    if not permission_exists:
        print("RESULT: REQUIRED PERMISSION NOT FOUND")
        print("PERMISSION DENIED")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Permission denied. "
                f"Required permission: {permission_name}"
            ),
        )

    print("FOUND PERMISSION:", permission_exists.name)
    print("RESULT: PERMISSION ALLOWED")

    return True