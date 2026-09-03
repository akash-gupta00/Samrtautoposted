from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user

from app.models.user import User

from app.schemas.brand_kit import (
    BrandKitCreate,
    BrandKitUpdate,
    BrandKitResponse,
)

from app.services.brand_kit_service import (
    BrandKitService,
)


router = APIRouter(
    prefix="/brand-kits",
    tags=["Brand Kits"],
)

brand_kit_service = BrandKitService()


@router.post(
    "",
    response_model=BrandKitResponse,
    status_code=201,
)
def create_brand_kit(
    brand_data: BrandKitCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Naya Brand Kit create karega.
    """

    return brand_kit_service.create_brand_kit(
        db=db,
        brand_data=brand_data,
        current_user=current_user,
        request=request,
    )


@router.get(
    "",
    response_model=list[BrandKitResponse],
)
def list_brand_kits(
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Organization ke saare Brand Kits return karega.
    """

    return brand_kit_service.list_brand_kits(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.get(
    "/{brand_kit_id}",
    response_model=BrandKitResponse,
)
def get_brand_kit(
    brand_kit_id: int,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Single Brand Kit return karega.
    """

    return brand_kit_service.get_brand_kit(
        db=db,
        brand_kit_id=brand_kit_id,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.put(
    "/{brand_kit_id}",
    response_model=BrandKitResponse,
)
def update_brand_kit(
    brand_kit_id: int,
    brand_data: BrandKitUpdate,
    request: Request,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Existing Brand Kit update karega.
    """

    return brand_kit_service.update_brand_kit(
        db=db,
        brand_kit_id=brand_kit_id,
        organization_id=organization_id,
        brand_data=brand_data,
        current_user=current_user,
        request=request,
    )


@router.delete(
    "/{brand_kit_id}",
)
def delete_brand_kit(
    brand_kit_id: int,
    request: Request,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Brand Kit delete karega.
    """

    return brand_kit_service.delete_brand_kit(
        db=db,
        brand_kit_id=brand_kit_id,
        organization_id=organization_id,
        current_user=current_user,
        request=request,
    )