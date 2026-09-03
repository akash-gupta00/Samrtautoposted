# SocialAccount model import kar rahe hain.
from app.models.social_account import SocialAccount


# Social account database operations ke liye repository class.
class SocialAccountRepository:

    # New social account create karega.
    def create(self, db, account_data):

        # Data ko database session me add kar rahe hain.
        db.add(account_data)

        # Database me save kar rahe hain.
        db.commit()

        # Latest saved values reload kar rahe hain.
        db.refresh(account_data)

        # Created account return kar rahe hain.
        return account_data

    # Organization ke social accounts list karega.
    def list_by_organization(self, db, organization_id: int):

        # Organization id ke basis par accounts nikal rahe hain.
        return db.query(SocialAccount).filter(
            SocialAccount.organization_id == organization_id
        ).all()

    # Account id se social account find karega.
    def get_by_id(self, db, account_id: int):

        # Account id ke basis par single account return karega.
        return db.query(SocialAccount).filter(
            SocialAccount.id == account_id
        ).first()

    # Social account delete karega.
    def delete(self, db, account):

        # Account ko delete kar rahe hain.
        db.delete(account)

        # Delete database me save kar rahe hain.
        db.commit()