from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.brand_kit import BrandKit
from app.models.organization import Organization
from app.models.user import User

from app.schemas.audit_log import AuditLogCreate
from app.schemas.brand_kit import (
    BrandKitCreate,
    BrandKitUpdate,
)

from app.services.audit_log_service import AuditLogService


class BrandKitService:

    def check_organization_access(
        self,
        db: Session,
        organization_id: int,
        current_user: User,
    ):
        """
        Check karega ki organization current user ki hai ya nahi.
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
                status_code=403,
                detail="Organization not found or access denied",
            )

        return organization

    def create_brand_kit(
        self,
        db: Session,
        brand_data: BrandKitCreate,
        current_user: User,
        request: Request,
    ):
        """
        Naya Brand Kit create karega.
        """

        organization = self.check_organization_access(
            db=db,
            organization_id=brand_data.organization_id,
            current_user=current_user,
        )

        brand_kit = BrandKit(
            organization_id=brand_data.organization_id,
            brand_name=brand_data.brand_name,
            logo_url=brand_data.logo_url,
            primary_color=brand_data.primary_color,
            secondary_color=brand_data.secondary_color,
            font_family=brand_data.font_family,
            tone_of_voice=brand_data.tone_of_voice,
            default_hashtags=brand_data.default_hashtags,
            website_url=brand_data.website_url,
            contact_email=brand_data.contact_email,
            contact_phone=brand_data.contact_phone,
        )

        db.add(brand_kit)
        db.commit()
        db.refresh(brand_kit)

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization.id,
                action="brand_kit_created",
                entity_type="brand_kit",
                entity_id=brand_kit.id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                details={
                    "brand_name": brand_kit.brand_name,
                    "primary_color": brand_kit.primary_color,
                    "secondary_color": brand_kit.secondary_color,
                    "website_url": brand_kit.website_url,
                },
            ),
        )

        return brand_kit

    def list_brand_kits(
        self,
        db: Session,
        organization_id: int,
        current_user: User,
    ):
        """
        Organization ke saare Brand Kits return karega.
        """

        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        return (
            db.query(BrandKit)
            .filter(
                BrandKit.organization_id == organization_id,
            )
            .all()
        )

    def get_brand_kit(
        self,
        db: Session,
        brand_kit_id: int,
        organization_id: int,
        current_user: User,
    ):
        """
        Single Brand Kit return karega.
        """

        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        brand_kit = (
            db.query(BrandKit)
            .filter(
                BrandKit.id == brand_kit_id,
                BrandKit.organization_id == organization_id,
            )
            .first()
        )

        if not brand_kit:
            raise HTTPException(
                status_code=404,
                detail="Brand Kit not found",
            )

        return brand_kit
    
    def update_brand_kit(
        self,
        db: Session,
        brand_kit_id: int,
        organization_id: int,
        brand_data: BrandKitUpdate,
        current_user: User,
        request: Request,
    ):
        """
        Existing Brand Kit update karega.
        """

        brand_kit = self.get_brand_kit(
            db=db,
            brand_kit_id=brand_kit_id,
            organization_id=organization_id,
            current_user=current_user,
        )

        update_data = brand_data.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No update data provided",
            )

        old_data = {
            "brand_name": brand_kit.brand_name,
            "logo_url": brand_kit.logo_url,
            "primary_color": brand_kit.primary_color,
            "secondary_color": brand_kit.secondary_color,
            "font_family": brand_kit.font_family,
            "tone_of_voice": brand_kit.tone_of_voice,
            "default_hashtags": brand_kit.default_hashtags,
            "website_url": brand_kit.website_url,
            "contact_email": brand_kit.contact_email,
            "contact_phone": brand_kit.contact_phone,
        }

        for field, value in update_data.items():
            setattr(
                brand_kit,
                field,
                value,
            )

        db.commit()
        db.refresh(brand_kit)

        changed_fields = {}

        for field in update_data:
            changed_fields[field] = {
                "old": old_data.get(field),
                "new": getattr(
                    brand_kit,
                    field,
                ),
            }

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="brand_kit_updated",
                entity_type="brand_kit",
                entity_id=brand_kit.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "brand_name": brand_kit.brand_name,
                    "changed_fields": changed_fields,
                },
            ),
        )

        return brand_kit

    def delete_brand_kit(
        self,
        db: Session,
        brand_kit_id: int,
        organization_id: int,
        current_user: User,
        request: Request,
    ):
        """
        Brand Kit delete karega.
        """

        brand_kit = self.get_brand_kit(
            db=db,
            brand_kit_id=brand_kit_id,
            organization_id=organization_id,
            current_user=current_user,
        )

        deleted_data = {
            "brand_name": brand_kit.brand_name,
            "logo_url": brand_kit.logo_url,
            "primary_color": brand_kit.primary_color,
            "secondary_color": brand_kit.secondary_color,
            "font_family": brand_kit.font_family,
            "tone_of_voice": brand_kit.tone_of_voice,
            "default_hashtags": brand_kit.default_hashtags,
            "website_url": brand_kit.website_url,
            "contact_email": brand_kit.contact_email,
            "contact_phone": brand_kit.contact_phone,
        }

        brand_kit_id_value = brand_kit.id

        db.delete(brand_kit)
        db.commit()

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="brand_kit_deleted",
                entity_type="brand_kit",
                entity_id=brand_kit_id_value,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details=deleted_data,
            ),
        )

        return {
            "message": "Brand Kit deleted successfully",
            "brand_kit_id": brand_kit_id_value,
        }