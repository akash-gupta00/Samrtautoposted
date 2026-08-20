from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate
from app.services.plan_service import PlanService


router = APIRouter(
    prefix="/plans",
    tags=["Plans"],
)

plan_service = PlanService()


@router.get(
    "/",
    response_model=list[PlanResponse],
)
def list_plans(
    db: Session = Depends(get_db),
):
    return plan_service.list_plans(db)


@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    return plan_service.get_plan(
        db=db,
        plan_id=plan_id,
    )


@router.post(
    "/",
    response_model=PlanResponse,
)
def create_plan(
    plan_data: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return plan_service.create_plan(
        db=db,
        plan_data=plan_data,
    )


@router.put(
    "/{plan_id}",
    response_model=PlanResponse,
)
def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return plan_service.update_plan(
        db=db,
        plan_id=plan_id,
        plan_data=plan_data,
    )


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return plan_service.delete_plan(
        db=db,
        plan_id=plan_id,
    )