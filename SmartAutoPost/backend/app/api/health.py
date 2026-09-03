# FastAPI se APIRouter import kar rahe hain.
# APIRouter ka use APIs ko group/organize karne ke liye hota hai.
from fastapi import APIRouter


# router object bana rahe hain.
# Is router ke andar health related APIs rakhenge.
router = APIRouter()


# Ye health check API hai.
# Jab user /health endpoint hit karega, ye function chalega.
@router.get("/health")
def health_check():
    # Server sahi chal raha hai ya nahi, iska response bhej rahe hain.
    return {
        "status": "ok",
        "message": "SmartAutoPost backend is running",
    }