from datetime import datetime

from app.models.publish_log import PublishLog
from app.models.social_account import SocialAccount

from app.services.publish_service import PublishService


class PublisherService:
    """
    Scheduler (post_scheduler.py) ye service call karta hai jab
    kisi post ka scheduled time aa jaata hai.

    PEHLE ye hamesha sirf ek "facebook" wale social account ko
    dhoondh ke usी par publish karne ki koshish karta tha -- chahe
    post Instagram ya LinkedIn ke liye banaya gaya ho. Ab post
    me jo social_account_id save hai, usी account (jo bhi platform
    ho) par sahi se publish hota hai.
    """

    def __init__(self):
        self.publish_service = PublishService()

    def publish_post(self, db, post):

        try:
            if not post.social_account_id:
                return {
                    "success": False,
                    "error": "Is post ke sath koi social account attach nahi hai",
                }

            social_account = (
                db.query(SocialAccount)
                .filter(
                    SocialAccount.id == post.social_account_id,
                    SocialAccount.is_active == True,
                )
                .first()
            )

            if not social_account:
                return {
                    "success": False,
                    "platform": None,
                    "error": "Connected social account nahi mila ya inactive hai",
                }

            result = self.publish_service.publish_to_platform(
                post=post,
                social_account=social_account,
            )

            publish_log = PublishLog(
                post_id=post.id,
                platform=result.get("platform", social_account.provider),
                platform_post_id=result.get("platform_post_id"),
                status="published" if result.get("success") else "failed",
                response=str(result),
            )

            db.add(publish_log)

            if result.get("success"):
                post.status = "published"
                post.published_at = datetime.now()
            else:
                post.status = "failed"

            db.commit()
            db.refresh(post)

            return result

        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "platform": None,
                "error": str(e),
            }
