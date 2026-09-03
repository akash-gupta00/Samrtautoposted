from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanService:

    def list_plans(self, db: Session):
        return (
            db.query(Plan)
            .filter(Plan.is_active.is_(True))
            .order_by(Plan.price.asc())
            .all()
        )

    def get_plan(self, db: Session, plan_id: int):
        plan = (
            db.query(Plan)
            .filter(Plan.id == plan_id)
            .first()
        )

        if not plan:
            raise HTTPException(
                status_code=404,
                detail="Plan not found",
            )

        return plan

    def create_plan(
        self,
        db: Session,
        plan_data: PlanCreate,
    ):
        existing_plan = (
            db.query(Plan)
            .filter(Plan.name == plan_data.name)
            .first()
        )

        if existing_plan:
            raise HTTPException(
                status_code=400,
                detail="Plan with this name already exists",
            )

        plan = Plan(
            **plan_data.model_dump()
        )

        db.add(plan)
        db.commit()
        db.refresh(plan)

        return plan

    def update_plan(
        self,
        db: Session,
        plan_id: int,
        plan_data: PlanUpdate,
    ):
        plan = self.get_plan(
            db=db,
            plan_id=plan_id,
        )

        update_data = plan_data.model_dump(
            exclude_unset=True,
        )

        if "name" in update_data:
            duplicate_plan = (
                db.query(Plan)
                .filter(
                    Plan.name == update_data["name"],
                    Plan.id != plan_id,
                )
                .first()
            )

            if duplicate_plan:
                raise HTTPException(
                    status_code=400,
                    detail="Plan with this name already exists",
                )

        for field, value in update_data.items():
            setattr(plan, field, value)

        db.commit()
        db.refresh(plan)

        return plan

    def delete_plan(
        self,
        db: Session,
        plan_id: int,
    ):
        plan = self.get_plan(
            db=db,
            plan_id=plan_id,
        )

        plan.is_active = False

        db.commit()
        db.refresh(plan)

        return {
            "success": True,
            "message": "Plan deactivated successfully",
        }