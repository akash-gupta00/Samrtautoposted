# APIRouter use kar rahe hain.
# Isse Scheduler APIs banengi.
from fastapi import APIRouter

# Dependency injection ke liye.
from fastapi import Depends

# Database session import kar rahe hain.
from sqlalchemy.orm import Session

# Current logged-in user dependency import kar rahe hain.
# Ye JWT token verify karke user return karegi.
from app.dependencies.auth import get_current_user
# Database dependency.
from app.database.session import get_db

# Scheduler schema import kar rahe hain.
from app.schemas.post_schedule import (
    PostScheduleCreate,
    PostScheduleResponse,
)

# Scheduler service import kar rahe hain.
from app.services.post_schedule_service import (
    PostScheduleService,
)


# Router create kar rahe hain.
router = APIRouter(
    prefix="/post-schedules",
    tags=["Post Schedules"],
)

# Service object bana rahe hain.
schedule_service = PostScheduleService()


# ============================================
# Create Schedule API
# ============================================

@router.post(
    "/",
    response_model=PostScheduleResponse,
)
def create_schedule(

    # Request body.
    data: PostScheduleCreate,

    # Database session.
    db: Session = Depends(get_db),

    # Login user.
    current_user=Depends(get_current_user),
):

    # Service call kar rahe hain.
    return schedule_service.create_schedule(
        db,
        data,
        current_user,
    )


# ============================================
# Process Pending Schedules
# ============================================

@router.post("/process")
def process_pending_schedules(

    # Database session.
    db: Session = Depends(get_db),

):

    # Pending schedules publish kar rahe hain.
    return schedule_service.process_pending_schedules(db)