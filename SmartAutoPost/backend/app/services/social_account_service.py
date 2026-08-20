from fastapi import HTTPException, Request

from app.dependencies.permission import check_user_permission
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.social_account import SocialAccount

from app.repositories.social_account_repository import (
    SocialAccountRepository,
)

from app.schemas.audit_log import AuditLogCreate
from app.services.audit_log_service import AuditLogService


class SocialAccountService:

    def __init__(self):
        self.repository = SocialAccountRepository()

    # Organization owner ya member ka basic access check karega.
    def check_organization_access(
        self,
        db,
        organization_id: int,
        current_user,
    ):
        organization = (
            db.query(Organization)
            .outerjoin(
                OrganizationMember,
                OrganizationMember.organization_id
                == Organization.id,
            )
            .filter(
                Organization.id == organization_id,
                (
                    (Organization.owner_id == current_user.id)
                    | (
                        OrganizationMember.user_id
                        == current_user.id
                    )
                ),
            )
            .first()
        )

        if not organization:
            raise HTTPException(
                status_code=403,
                detail="Organization not found or access denied",
            )

        return organization

    # Social account actions ka audit log create karega.
    def create_social_account_audit_log(
        self,
        db,
        request: Request,
        current_user,
        organization_id: int,
        action: str,
        entity_id: int | None = None,
        details: dict | None = None,
    ):
        try:
            AuditLogService.create_log(
                db=db,
                audit_data=AuditLogCreate(
                    user_id=current_user.id,
                    organization_id=organization_id,
                    action=action,
                    entity_type="social_account",
                    entity_id=entity_id,
                    ip_address=(
                        request.client.host
                        if request.client
                        else None
                    ),
                    user_agent=request.headers.get(
                        "user-agent"
                    ),
                    details=details,
                ),
            )

        except Exception as error:
            db.rollback()
            print(
                f"Social account audit log error: {error}"
            )

    # =========================================================
    # CONNECT SOCIAL ACCOUNT
    # Required Permission: social_accounts.connect
    # =========================================================
    def connect_account(
        self,
        db,
        data,
        current_user,
        request: Request,
    ):
        self.check_organization_access(
            db=db,
            organization_id=data.organization_id,
            current_user=current_user,
        )

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=data.organization_id,
            permission_name="social_accounts.connect",
        )

        existing_account = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.organization_id
                == data.organization_id,

                SocialAccount.provider
                == data.provider,

                SocialAccount.account_name
                == data.account_name,
            )
            .first()
        )

        if existing_account:
            raise HTTPException(
                status_code=400,
                detail="Social account already connected",
            )

        account = SocialAccount(
            organization_id=data.organization_id,
            provider=data.provider,
            account_name=data.account_name,
            access_token=data.access_token,
            refresh_token=data.refresh_token,
        )

        created_account = self.repository.create(
            db,
            account,
        )

        self.create_social_account_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            organization_id=created_account.organization_id,
            action="social_account_connected",
            entity_id=created_account.id,
            details={
                "provider": created_account.provider,
                "account_name": created_account.account_name,
            },
        )

        return created_account

    # =========================================================
    # LIST SOCIAL ACCOUNTS
    # Required Permission: social_accounts.view
    # =========================================================
    def list_accounts(
        self,
        db,
        organization_id: int,
        current_user,
    ):
        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=organization_id,
            permission_name="social_accounts.view",
        )

        return self.repository.list_by_organization(
            db,
            organization_id,
        )

    # =========================================================
    # DELETE / DISCONNECT SOCIAL ACCOUNT
    # Required Permission: social_accounts.delete
    # =========================================================
    def delete_account(
        self,
        db,
        account_id: int,
        current_user,
        request: Request,
    ):
        account = self.repository.get_by_id(
            db,
            account_id,
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Social account not found",
            )

        self.check_organization_access(
            db=db,
            organization_id=account.organization_id,
            current_user=current_user,
        )

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=account.organization_id,
            permission_name="social_accounts.delete",
        )

        account_details = {
            "provider": account.provider,
            "account_name": account.account_name,
        }

        organization_id = account.organization_id
        deleted_account_id = account.id

        self.create_social_account_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            organization_id=organization_id,
            action="social_account_disconnected",
            entity_id=deleted_account_id,
            details=account_details,
        )

        self.repository.delete(
            db,
            account,
        )

        return {
            "message": (
                "Social account disconnected successfully"
            )
        }