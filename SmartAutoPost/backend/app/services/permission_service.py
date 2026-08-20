from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User

from app.schemas.audit_log import AuditLogCreate
from app.services.audit_log_service import AuditLogService
from app.services.role_service import RoleService


class PermissionService:

    # Project ki saari default permissions.
    DEFAULT_PERMISSIONS = [
        {
            "name": "dashboard.view",
            "description": "Dashboard dekh sakta hai.",
            "module": "dashboard",
        },
        {
            "name": "posts.create",
            "description": "Post create kar sakta hai.",
            "module": "posts",
        },
        {
            "name": "posts.view",
            "description": "Posts dekh sakta hai.",
            "module": "posts",
        },
        {
            "name": "posts.update",
            "description": "Post update kar sakta hai.",
            "module": "posts",
        },
        {
            "name": "posts.delete",
            "description": "Post delete kar sakta hai.",
            "module": "posts",
        },
        {
            "name": "media.upload",
            "description": "Media upload kar sakta hai.",
            "module": "media",
        },

        # Social Account permissions.
        {
            "name": "social_accounts.connect",
            "description": "Social account connect kar sakta hai.",
            "module": "social_accounts",
        },
        {
            "name": "social_accounts.view",
            "description": "Social accounts dekh sakta hai.",
            "module": "social_accounts",
        },
        {
            "name": "social_accounts.delete",
            "description": "Social account disconnect kar sakta hai.",
            "module": "social_accounts",
        },

        {
            "name": "publish.post",
            "description": "Post publish kar sakta hai.",
            "module": "publishing",
        },
        {
            "name": "analytics.view",
            "description": "Analytics dekh sakta hai.",
            "module": "analytics",
        },
        {
            "name": "brand_kit.view",
            "description": "Brand Kit dekh sakta hai.",
            "module": "brand_kit",
        },
        {
            "name": "brand_kit.update",
            "description": "Brand Kit update kar sakta hai.",
            "module": "brand_kit",
        },
        {
            "name": "members.view",
            "description": "Organization members dekh sakta hai.",
            "module": "members",
        },
        {
            "name": "members.manage",
            "description": "Organization members manage kar sakta hai.",
            "module": "members",
        },
        {
            "name": "roles.manage",
            "description": "Roles aur permissions manage kar sakta hai.",
            "module": "roles",
        },
    ]

    @staticmethod
    def seed_default_permissions(
        db: Session,
    ):
        """
        Default permissions database me insert karega.

        Jo permission pehle se database me exist karti hai,
        usko dobara create nahi karega.
        """

        # Nayi create hui permissions ki names.
        created_permissions = []

        # Pehle se existing permissions ki names.
        existing_permissions = []

        # Default permissions ko ek-ek karke process karenge.
        for permission_data in PermissionService.DEFAULT_PERMISSIONS:

            # Same permission name pehle se database me hai ya nahi.
            permission = (
                db.query(Permission)
                .filter(
                    Permission.name
                    == permission_data["name"]
                )
                .first()
            )

            # Permission pehle se hai to dobara create nahi karenge.
            if permission:
                existing_permissions.append(
                    permission.name
                )
                continue

            # Nayi permission object create kar rahe hain.
            permission = Permission(
                name=permission_data["name"],
                description=permission_data[
                    "description"
                ],
                module=permission_data["module"],
            )

            # Database session me permission add kar rahe hain.
            db.add(permission)

            # Created permissions list me name save kar rahe hain.
            created_permissions.append(
                permission_data["name"]
            )

        # Saari new permissions database me save karenge.
        db.commit()

        return {
            "message": (
                "Default permissions processed successfully."
            ),
            "created_permissions": created_permissions,
            "existing_permissions": existing_permissions,
        }

    @staticmethod
    def list_permissions(
        db: Session,
        module: str | None = None,
    ):
        """
        Saari permissions return karega.

        Module diya ho to module ke hisab se
        permissions filter karega.
        """

        # Permission table ki basic query.
        query = db.query(Permission)

        # Module diya gaya hai to module filter lagayenge.
        if module:
            query = query.filter(
                Permission.module == module
            )

        # Module aur permission name ke hisab se sorting.
        return (
            query
            .order_by(
                Permission.module.asc(),
                Permission.name.asc(),
            )
            .all()
        )

    @staticmethod
    def get_permission(
        db: Session,
        permission_id: int,
    ):
        """
        Single permission ID ke basis par return karega.
        """

        permission = (
            db.query(Permission)
            .filter(
                Permission.id == permission_id
            )
            .first()
        )

        # Permission nahi mili to 404.
        if not permission:
            raise HTTPException(
                status_code=404,
                detail="Permission not found.",
            )

        return permission

    @staticmethod
    def assign_permission_to_role(
        db: Session,
        role_id: int,
        permission_id: int,
        organization_id: int,
        current_user: User,
        request: Request,
    ):
        """
        Kisi organization role ko permission assign karega.
        """

        # Role exist karta hai aur current user ko access hai ya nahi.
        role = RoleService.get_role(
            db=db,
            role_id=role_id,
            organization_id=organization_id,
            current_user=current_user,
        )

        # Permission database me exist karti hai ya nahi.
        permission = (
            db.query(Permission)
            .filter(
                Permission.id == permission_id
            )
            .first()
        )

        if not permission:
            raise HTTPException(
                status_code=404,
                detail="Permission not found.",
            )

        # Same permission role ko pehle se assigned hai ya nahi.
        existing_assignment = (
            db.query(RolePermission)
            .filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id
                == permission_id,
            )
            .first()
        )

        if existing_assignment:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Permission already assigned "
                    "to this role."
                ),
            )

        # Role aur permission ka relationship create kar rahe hain.
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
        )

        db.add(role_permission)
        db.commit()
        db.refresh(role_permission)

        # Permission assignment ka audit log.
        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="permission_assigned",
                entity_type="role_permission",
                entity_id=role_permission.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "role_id": role.id,
                    "role_name": role.name,
                    "permission_id": permission.id,
                    "permission_name": permission.name,
                },
            ),
        )

        return {
            "message": "Permission assigned successfully.",
            "role_id": role.id,
            "permission_id": permission.id,
            "permission_name": permission.name,
        }

    @staticmethod
    def remove_permission_from_role(
        db: Session,
        role_id: int,
        permission_id: int,
        organization_id: int,
        current_user: User,
        request: Request,
    ):
        """
        Kisi organization role se permission remove karega.
        """

        # Role aur owner access check.
        role = RoleService.get_role(
            db=db,
            role_id=role_id,
            organization_id=organization_id,
            current_user=current_user,
        )

        # Permission exist karti hai ya nahi.
        permission = (
            db.query(Permission)
            .filter(
                Permission.id == permission_id
            )
            .first()
        )

        if not permission:
            raise HTTPException(
                status_code=404,
                detail="Permission not found.",
            )

        # RolePermission assignment search karenge.
        role_permission = (
            db.query(RolePermission)
            .filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id
                == permission_id,
            )
            .first()
        )

        # Permission role ko assigned hi nahi hai.
        if not role_permission:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Permission is not assigned "
                    "to this role."
                ),
            )

        # Audit log ke liye assignment ID save karenge.
        assignment_id = role_permission.id

        # Assignment delete karenge.
        db.delete(role_permission)
        db.commit()

        # Permission removal ka audit log.
        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="permission_removed",
                entity_type="role_permission",
                entity_id=assignment_id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "role_id": role.id,
                    "role_name": role.name,
                    "permission_id": permission.id,
                    "permission_name": permission.name,
                },
            ),
        )

        return {
            "message": "Permission removed successfully.",
            "role_id": role.id,
            "permission_id": permission.id,
        }

    @staticmethod
    def get_role_permissions(
        db: Session,
        role_id: int,
        organization_id: int,
        current_user: User,
    ):
        """
        Kisi role ki saari assigned permissions return karega.
        """

        # Role exist aur accessible hai ya nahi.
        RoleService.get_role(
            db=db,
            role_id=role_id,
            organization_id=organization_id,
            current_user=current_user,
        )

        # RolePermission table ke through permission list.
        permissions = (
            db.query(Permission)
            .join(
                RolePermission,
                RolePermission.permission_id
                == Permission.id,
            )
            .filter(
                RolePermission.role_id == role_id
            )
            .order_by(
                Permission.module.asc(),
                Permission.name.asc(),
            )
            .all()
        )

        return permissions