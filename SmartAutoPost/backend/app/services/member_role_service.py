from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.organization_member import OrganizationMember
from app.models.organization_member_role import OrganizationMemberRole
from app.models.role import Role
from app.models.user import User

from app.schemas.audit_log import AuditLogCreate

from app.services.audit_log_service import AuditLogService
from app.services.role_service import RoleService


class MemberRoleService:

    @staticmethod
    def assign_role(
        db: Session,
        member_id: int,
        role_id: int,
        organization_id: int,
        current_user: User,
        request: Request,
    ):
        """
        Member ko role assign karega.
        """

        RoleService.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
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
                detail="Member not found.",
            )

        role = (
            db.query(Role)
            .filter(
                Role.id == role_id,
                Role.organization_id == organization_id,
            )
            .first()
        )

        if not role:
            raise HTTPException(
                status_code=404,
                detail="Role not found.",
            )

        existing = (
            db.query(OrganizationMemberRole)
            .filter(
                OrganizationMemberRole.member_id == member_id,
                OrganizationMemberRole.role_id == role_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Role already assigned.",
            )

        member_role = OrganizationMemberRole(
            member_id=member_id,
            role_id=role_id,
        )

        db.add(member_role)
        db.commit()
        db.refresh(member_role)

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="member_role_assigned",
                entity_type="organization_member_role",
                entity_id=member_role.id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                details={
                    "member_id": member.id,
                    "role_id": role.id,
                    "role_name": role.name,
                },
            ),
        )

        return {
            "message": "Role assigned successfully.",
            "member_role_id": member_role.id,
        }

    @staticmethod
    def remove_role(
        db: Session,
        member_id: int,
        role_id: int,
        organization_id: int,
        current_user: User,
        request: Request,
    ):
        """
        Member se role remove karega.
        """

        RoleService.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        member_role = (
            db.query(OrganizationMemberRole)
            .join(
                OrganizationMember,
                OrganizationMember.id == OrganizationMemberRole.member_id,
            )
            .filter(
                OrganizationMemberRole.member_id == member_id,
                OrganizationMemberRole.role_id == role_id,
                OrganizationMember.organization_id == organization_id,
            )
            .first()
        )

        if not member_role:
            raise HTTPException(
                status_code=404,
                detail="Assigned role not found.",
            )

        assignment_id = member_role.id

        db.delete(member_role)
        db.commit()

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="member_role_removed",
                entity_type="organization_member_role",
                entity_id=assignment_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                details={
                    "member_id": member_id,
                    "role_id": role_id,
                },
            ),
        )

        return {
            "message": "Role removed successfully.",
        }

    @staticmethod
    def member_roles(
        db: Session,
        member_id: int,
        organization_id: int,
        current_user: User,
    ):
        """
        Member ke saare roles return karega.
        """

        RoleService.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        return (
            db.query(Role)
            .join(
                OrganizationMemberRole,
                OrganizationMemberRole.role_id == Role.id,
            )
            .join(
                OrganizationMember,
                OrganizationMember.id == OrganizationMemberRole.member_id,
            )
            .filter(
                OrganizationMember.id == member_id,
                OrganizationMember.organization_id == organization_id,
            )
            .all()
        )