# FastAPI imports.
from fastapi import APIRouter, Depends, HTTPException, Request

# SQLAlchemy Session.
from sqlalchemy.orm import Session

# Database session.
from app.database.session import get_db

# Models.
from app.models.organization import Organization
from app.models.user import User
from app.models.organization_member import OrganizationMember

# Auth dependency.
from app.dependencies.auth import get_current_user

# Schemas.
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

# Audit log imports.
from app.schemas.audit_log import AuditLogCreate
from app.services.audit_log_service import AuditLogService


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


def create_slug(name: str):
    return name.lower().strip().replace(" ", "-")


def create_organization_audit_log(
    db: Session,
    request: Request,
    current_user: User,
    organization_id: int,
    action: str,
    details: dict | None = None,
):
    """
    Organization ke important actions audit_logs table me save karega.
    Audit log fail hone par main organization API fail nahi hogi.
    """

    try:
        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action=action,
                entity_type="organization",
                entity_id=organization_id,
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
        print(f"Organization audit log error: {error}")


@router.post(
    "/",
    response_model=OrganizationResponse,
)
def create_organization(
    org_data: OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    slug = create_slug(org_data.name)

    # Same slug already exist hai ya nahi.
    existing_organization = (
        db.query(Organization)
        .filter(Organization.slug == slug)
        .first()
    )

    if existing_organization:
        raise HTTPException(
            status_code=400,
            detail="Organization with this name already exists",
        )

    new_org = Organization(
        name=org_data.name,
        slug=slug,
        industry=org_data.industry,
        timezone=org_data.timezone,
        language=org_data.language,
        owner_id=current_user.id,
    )

    db.add(new_org)

    # Organization ID generate karne ke liye flush
    db.flush()

    # Owner ko organization member banao
    owner_member = OrganizationMember(
        organization_id=new_org.id,
        user_id=current_user.id,
        role="owner",
    )

    db.add(owner_member)

    db.commit()
    db.refresh(new_org)

    create_organization_audit_log(
        db=db,
        request=request,
        current_user=current_user,
        organization_id=new_org.id,
        action="organization_created",
        details={
            "name": new_org.name,
            "slug": new_org.slug,
            "industry": new_org.industry,
        },
    )

    return new_org


@router.get(
    "/",
    response_model=list[OrganizationResponse],
)
def list_my_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organizations = (
        db.query(Organization)
        .filter(
            Organization.owner_id == current_user.id
        )
        .all()
    )

    return organizations


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def get_organization_detail(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
            detail="Organization not found",
        )

    return organization


@router.put(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def update_organization(
    organization_id: int,
    org_data: OrganizationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
            detail="Organization not found",
        )

    old_data = {
        "name": organization.name,
        "industry": organization.industry,
        "timezone": organization.timezone,
        "language": organization.language,
    }

    updated_fields = {}

    if org_data.name is not None:
        new_slug = create_slug(org_data.name)

        duplicate_organization = (
            db.query(Organization)
            .filter(
                Organization.slug == new_slug,
                Organization.id != organization.id,
            )
            .first()
        )

        if duplicate_organization:
            raise HTTPException(
                status_code=400,
                detail="Organization with this name already exists",
            )

        organization.name = org_data.name
        organization.slug = new_slug
        updated_fields["name"] = org_data.name

    if org_data.industry is not None:
        organization.industry = org_data.industry
        updated_fields["industry"] = org_data.industry

    if org_data.timezone is not None:
        organization.timezone = org_data.timezone
        updated_fields["timezone"] = org_data.timezone

    if org_data.language is not None:
        organization.language = org_data.language
        updated_fields["language"] = org_data.language

    db.commit()
    db.refresh(organization)

    create_organization_audit_log(
        db=db,
        request=request,
        current_user=current_user,
        organization_id=organization.id,
        action="organization_updated",
        details={
            "old_data": old_data,
            "updated_fields": updated_fields,
        },
    )

    return organization


@router.delete("/{organization_id}")
def delete_organization(
    organization_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
            detail="Organization not found",
        )

    deleted_organization_data = {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "industry": organization.industry,
    }

    deleted_organization_id = organization.id

    # Organization delete hone se pehle audit log save karo.
    # Kyunki organization_id foreign key ON DELETE SET NULL hai.
    create_organization_audit_log(
        db=db,
        request=request,
        current_user=current_user,
        organization_id=deleted_organization_id,
        action="organization_deleted",
        details=deleted_organization_data,
    )

    db.delete(organization)
    db.commit()

    return {
        "message": "Organization deleted successfully"
    }    
      
         