from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.competitor import Competitor
from app.models.organization import Organization
from app.models.user import User

from app.schemas.audit_log import AuditLogCreate
from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorUpdate,
)

from app.services.audit_log_service import AuditLogService


class CompetitorService:

    def check_organization_access(
        self,
        db: Session,
        organization_id: int,
        current_user: User,
    ):
        """
        Check karega ki current user organization ka owner hai ya nahi.
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

    def create_competitor(
        self,
        db: Session,
        competitor_data: CompetitorCreate,
        current_user: User,
        request: Request,
    ):
        """
        Organization ke liye naya competitor create karega.
        """

        self.check_organization_access(
            db=db,
            organization_id=competitor_data.organization_id,
            current_user=current_user,
        )

        existing_competitor = (
            db.query(Competitor)
            .filter(
                Competitor.organization_id
                == competitor_data.organization_id,
                Competitor.platform
                == competitor_data.platform,
                Competitor.profile_url
                == competitor_data.profile_url,
            )
            .first()
        )

        if existing_competitor:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This competitor profile already exists "
                    "for this organization"
                ),
            )

        competitor = Competitor(
            organization_id=competitor_data.organization_id,
            name=competitor_data.name,
            platform=competitor_data.platform,
            profile_name=competitor_data.profile_name,
            profile_url=competitor_data.profile_url,
            status=competitor_data.status,
            notes=competitor_data.notes,
        )

        db.add(competitor)
        db.commit()
        db.refresh(competitor)

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=competitor.organization_id,
                action="competitor_created",
                entity_type="competitor",
                entity_id=competitor.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "competitor_name": competitor.name,
                    "platform": competitor.platform,
                    "profile_name": competitor.profile_name,
                    "profile_url": competitor.profile_url,
                    "status": competitor.status,
                },
            ),
        )

        return competitor

    def list_competitors(
        self,
        db: Session,
        organization_id: int,
        current_user: User,
        platform: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        Organization ke saare competitors return karega.
        Platform aur status ke basis par filter bhi kar sakte hain.
        """

        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        query = (
            db.query(Competitor)
            .filter(
                Competitor.organization_id
                == organization_id
            )
        )

        if platform:
            query = query.filter(
                Competitor.platform == platform
            )

        if status:
            query = query.filter(
                Competitor.status == status
            )

        competitors = (
            query
            .order_by(
                Competitor.created_at.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return competitors

    def get_competitor(
        self,
        db: Session,
        competitor_id: int,
        organization_id: int,
        current_user: User,
    ):
        """
        Ek particular competitor ki detail return karega.
        """

        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        competitor = (
            db.query(Competitor)
            .filter(
                Competitor.id == competitor_id,
                Competitor.organization_id
                == organization_id,
            )
            .first()
        )

        if not competitor:
            raise HTTPException(
                status_code=404,
                detail="Competitor not found",
            )

        return competitor

    def update_competitor(
        self,
        db: Session,
        competitor_id: int,
        organization_id: int,
        competitor_data: CompetitorUpdate,
        current_user: User,
        request: Request,
    ):
        """
        Existing competitor ki information update karega.
        """

        competitor = self.get_competitor(
            db=db,
            competitor_id=competitor_id,
            organization_id=organization_id,
            current_user=current_user,
        )

        update_data = competitor_data.model_dump(
            exclude_unset=True
        )

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No update data provided",
            )

        old_data = {
            "name": competitor.name,
            "platform": competitor.platform,
            "profile_name": competitor.profile_name,
            "profile_url": competitor.profile_url,
            "status": competitor.status,
            "notes": competitor.notes,
        }

        new_platform = update_data.get(
            "platform",
            competitor.platform,
        )

        new_profile_url = update_data.get(
            "profile_url",
            competitor.profile_url,
        )

        duplicate_competitor = (
            db.query(Competitor)
            .filter(
                Competitor.organization_id
                == organization_id,
                Competitor.platform
                == new_platform,
                Competitor.profile_url
                == new_profile_url,
                Competitor.id != competitor_id,
            )
            .first()
        )

        if duplicate_competitor:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Another competitor with this platform "
                    "and profile URL already exists"
                ),
            )

        for field, value in update_data.items():
            setattr(
                competitor,
                field,
                value,
            )

        db.commit()
        db.refresh(competitor)

        changed_fields = {}

        for field in update_data:
            changed_fields[field] = {
                "old": old_data.get(field),
                "new": getattr(
                    competitor,
                    field,
                    None,
                ),
            }

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="competitor_updated",
                entity_type="competitor",
                entity_id=competitor.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "competitor_name": competitor.name,
                    "changed_fields": changed_fields,
                },
            ),
        )

        return competitor

    def delete_competitor(
        self,
        db: Session,
        competitor_id: int,
        organization_id: int,
        current_user: User,
        request: Request,
    ):
        """
        Competitor ko database se delete karega.
        """

        competitor = self.get_competitor(
            db=db,
            competitor_id=competitor_id,
            organization_id=organization_id,
            current_user=current_user,
        )

        deleted_competitor_data = {
            "competitor_id": competitor.id,
            "competitor_name": competitor.name,
            "platform": competitor.platform,
            "profile_name": competitor.profile_name,
            "profile_url": competitor.profile_url,
            "status": competitor.status,
        }

        deleted_competitor_id = competitor.id

        db.delete(competitor)
        db.commit()

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="competitor_deleted",
                entity_type="competitor",
                entity_id=deleted_competitor_id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details=deleted_competitor_data,
            ),
        )

        return {
            "message": "Competitor deleted successfully",
            "competitor_id": deleted_competitor_id,
        }