# Operating system related kaam ke liye os import kar rahe hain.
# Folder create karne aur file path banane ke liye use hoga.
import os


# Unique filename generate karne ke liye uuid import kar rahe hain.
# Isse same naam ki files overwrite nahi hongi.
import uuid


# FastAPI ka HTTPException import kar rahe hain.
# Error response bhejne ke liye use hota hai.
from fastapi import HTTPException


# MediaRepository import kar rahe hain.
# Database me media save karne ke liye use hoga.
from app.repositories.media_repository import MediaRepository


# MediaService class business logic handle karegi.
class MediaService:


    # Constructor.
    # Database session receive karega.
    def __init__(self, db):

        # Database session ko class me store kar rahe hain.
        self.db = db

        # Repository object create kar rahe hain.
        self.repository = MediaRepository(db)


    # Media upload handle karne wala function.
    def upload_media(self, file, organization_id: int):

        # Upload folder ka path define kar rahe hain.
        upload_dir = "uploads/media"

        # Agar folder exist nahi karta to create kar denge.
        os.makedirs(upload_dir, exist_ok=True)

        # Allowed file types define kar rahe hain.
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
            "video/mp4",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]

        # Check kar rahe hain ki uploaded file allowed type ki hai ya nahi.
        if file.content_type not in allowed_types:

            # Agar file type allowed nahi hai to error bhejenge.
            raise HTTPException(
                status_code=400,
                detail="File type not allowed"
            )

        # Original file extension nikal rahe hain.
        file_extension = file.filename.split(".")[-1]

        # Unique filename generate kar rahe hain.
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Final file path bana rahe hain.
        file_path = os.path.join(upload_dir, unique_filename)

        # File ko local storage me save kar rahe hain.
        with open(file_path, "wb") as buffer:

            # Uploaded file ka content read kar rahe hain.
            content = file.file.read()

            # File content ko disk par write kar rahe hain.
            buffer.write(content)

        # file_path jaisa "uploads/media/xxx.jpg" ek bare OS path
        # hai -- browser/external APIs (Facebook/Instagram/LinkedIn)
        # isko URL ki tarah access nahi kar sakte. URL-style path
        # banate hain ("/uploads/media/xxx.jpg"), jo main.py me
        # mounted StaticFiles route se match karta hai.
        url_path = "/" + file_path.replace("\\", "/")

        # Database me media record save kar rahe hain.
        media = self.repository.create_media(
            filename=file.filename,
            file_url=url_path,
            file_type=file.content_type,
            organization_id=organization_id,
        )

        # Saved media record return kar rahe hain.
        return media
    
        # Organization ke media list karne wala function.
    def list_media(self, organization_id: int):

        # Repository se organization ke saare media records la rahe hain.
        return self.repository.list_by_organization(
            organization_id
        )
        
        # Media delete karne wala function.
    def delete_media(self, media_id: int):

        # Media id se media record find kar rahe hain.
        media = self.repository.get_by_id(media_id)

        # Agar media nahi mila to error return karenge.
        if not media:
            raise HTTPException(
                status_code=404,
                detail="Media not found"
            )

        # Database se media record delete kar rahe hain.
        self.repository.delete(media)

        # Success response return kar rahe hain.
        return {
            "message": "Media deleted successfully"
        }