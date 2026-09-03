from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.organization import Organization
from app.models.user import User

from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
)

from app.schemas.audit_log import AuditLogCreate

from app.services.audit_log_service import AuditLogService


class RoleService:

    @staticmethod
    def check_organization_access(
        db: Session,
        organization_id: int,
        current_user: User,
    ):
        """
        User ke paas organization access hai ya nahi.
        """

        organization = (
            db.query(Organization)
            .filter(
                Organization.id == organization_id,
                Organization.owner_id == current_user.id,
            )
            .first()
        )

        if not organization:
            raise HTTPException(
                status_code=404,
                detail="Organization not found.",
            )

        return organization

    @staticmethod
    def create_role(
        db: Session,
        role_data: RoleCreate,
        current_user: User,
        request: Request,
    ):
        """
        Naya role create karega.
        """

        RoleService.check_organization_access(
            db=db,
            organization_id=role_data.organization_id,
            current_user=current_user,
        )

        existing_role = (
            db.query(Role)
            .filter(
                Role.organization_id == role_data.organization_id,
                Role.name == role_data.name,
            )
            .first()
        )

        if existing_role:
            raise HTTPException(
                status_code=400,
                detail="Role already exists.",
            )

        role = Role(
            organization_id=role_data.organization_id,
            name=role_data.name,
            description=role_data.description,
        )

        db.add(role)
        db.commit()
        db.refresh(role)

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=role.organization_id,
                action="role_created",
                entity_type="role",
                entity_id=role.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "role_name": role.name,
                },
            ),
        )

        return role

    @staticmethod
    def list_roles(
        db: Session,
        organization_id: int,
        current_user: User,
    ):
        """
        Organization ke saare roles.
        """

        RoleService.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        return (
            db.query(Role)
            .filter(
                Role.organization_id == organization_id,
            )
            .order_by(Role.id.desc())
            .all()
        )

    @staticmethod
    def get_role(
        db: Session,
        role_id: int,
        organization_id: int,
        current_user: User,
    ):
        """
        Single role return karega.
        """

        RoleService.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
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

        return role
    
    @staticmethod
    def update_role(
        db: Session,
        role_id: int,
        organization_id: int,
        role_data: RoleUpdate,
        current_user: User,
        request: Request,
    ):
        """
        Existing role update karega.
        """

        role = RoleService.get_role(
            db=db,
            role_id=role_id,
            organization_id=organization_id,
            current_user=current_user,
        )

        update_data = role_data.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No update data provided.",
            )

        if "name" in update_data:
            existing_role = (
                db.query(Role)
                .filter(
                    Role.organization_id == organization_id,
                    Role.name == update_data["name"],
                    Role.id != role_id,
                )
                .first()
            )

            if existing_role:
                raise HTTPException(
                    status_code=400,
                    detail="Role name already exists.",
                )

        old_data = {
            "name": role.name,
            "description": role.description,
        }

        for field, value in update_data.items():
            setattr(
                role,
                field,
                value,
            )

        db.commit()
        db.refresh(role)

        changed_fields = {}

        for field in update_data:
            changed_fields[field] = {
                "old": old_data.get(field),
                "new": getattr(role, field),
            }

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="role_updated",
                entity_type="role",
                entity_id=role.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "role_name": role.name,
                    "changed_fields": changed_fields,
                },
            ),
        )

        return role

    @staticmethod
    def delete_role(
        db: Session,
        role_id: int,
        organization_id: int,
        current_user: User,
        request: Request,
    ):
        """
        Existing role delete karega.
        """

        role = RoleService.get_role(
            db=db,
            role_id=role_id,
            organization_id=organization_id,
            current_user=current_user,
        )

        role_data = {
            "name": role.name,
            "description": role.description,
        }

        role_id_value = role.id

        db.delete(role)
        db.commit()

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="role_deleted",
                entity_type="role",
                entity_id=role_id_value,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details=role_data,
            ),
        )

        return {
            "message": "Role deleted successfully.",
            "role_id": role_id_value,
        }