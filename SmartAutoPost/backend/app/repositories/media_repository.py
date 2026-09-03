# SQLAlchemy Session import kar rahe hain.
# Database operations ke liye use hota hai.
from sqlalchemy.orm import Session


# Media model import kar rahe hain.
# Is model me media table define hai.
from app.models.media import Media


# MediaRepository class bana rahe hain.
# Is class ka kaam sirf database operations karna hai.
class MediaRepository:


    # Constructor.
    # Database session receive karega.
    def __init__(self, db: Session):

        # Database session store kar rahe hain.
        self.db = db


    # Naya media record database me save karne ka function.
    def create_media(
        self,
        filename: str,
        file_url: str,
        file_type: str,
        organization_id: int,
    ):

        # Media object create kar rahe hain.
        media = Media(

            # File name save kar rahe hain.
            filename=filename,

            # File path save kar rahe hain.
            file_url=file_url,

            # File type save kar rahe hain.
            file_type=file_type,

            # Organization id save kar rahe hain.
            organization_id=organization_id,
        )


        # Object database session me add kar rahe hain.
        self.db.add(media)


        # Database me permanently save kar rahe hain.
        self.db.commit()


        # Latest values database se refresh kar rahe hain.
        self.db.refresh(media)


        # Saved object return kar rahe hain.
        return media
    
    # Organization ke saare media records list karne wala function.
    def list_by_organization(self, organization_id: int):

        # Media table se organization_id ke basis par records nikal rahe hain.
        return self.db.query(Media).filter(
            Media.organization_id == organization_id
        ).all()
        
        

       # Media id se single media record find karne wala function.
    def get_by_id(self, media_id: int):

        # Media table se id ke basis par record nikal rahe hain.
        return self.db.query(Media).filter(
            Media.id == media_id
        ).first()


    # Media record delete karne wala function.
    def delete(self, media):

        # Media record database se delete kar rahe hain.
        self.db.delete(media)

        # Delete operation save kar rahe hain.
        self.db.commit()