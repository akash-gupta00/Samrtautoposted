# Post model import kar rahe hain.
# Iska use posts table par database query chalane ke liye hoga.
from app.models.post import Post

# Media model import kar rahe hain.
# Iska use media attach karne ke liye hoga.
from app.models.media import Media


# Repository class sirf database operations handle karegi.
class PostRepository:

    # ============================================
    # Create Post
    # ============================================

    # New post database me save karega.
    def create(self, db, post):

        # Database session me object add kar rahe hain.
        db.add(post)

        # Database me save kar rahe hain.
        db.commit()

        # Latest values reload kar rahe hain.
        db.refresh(post)

        # Created post return kar rahe hain.
        return post

    # ============================================
    # List Posts
    # ============================================

    # Organization ke saare posts la rahe hain.
    def list_by_organization(self, db, organization_id: int):

        return db.query(Post).filter(
            Post.organization_id == organization_id
        ).all()

    # ============================================
    # Get Single Post
    # ============================================

    # ID ke basis par post nikal rahe hain.
    def get_by_id(self, db, post_id: int):

        return db.query(Post).filter(
            Post.id == post_id
        ).first()

    # ============================================
    # Update Post
    # ============================================

    # Existing post update kar rahe hain.
    def update(self, db, post, post_data):

        # Title update.
        if post_data.title is not None:
            post.title = post_data.title

        # Caption update.
        if post_data.caption is not None:
            post.caption = post_data.caption

        # Schedule time update.
        if post_data.scheduled_at is not None:
            post.scheduled_at = post_data.scheduled_at

        # Changes save kar rahe hain.
        db.commit()

        # Latest data reload kar rahe hain.
        db.refresh(post)

        return post

    # ============================================
    # Delete Post
    # ============================================

    # Post delete kar rahe hain.
    def delete(self, db, post):

        db.delete(post)

        db.commit()

    # ============================================
    # Attach Media To Post
    # ============================================

    # Ek ya multiple media ko post ke saath attach kar rahe hain.
    def attach_media(self, db, post, media_ids: list[int]):

        # Media ids ke basis par records nikal rahe hain.
        media_items = db.query(Media).filter(
            Media.id.in_(media_ids)
        ).all()

        # Har media ko post ke saath attach kar rahe hain.
        for media in media_items:
            post.media.append(media)

        # Database me save kar rahe hain.
        db.commit()

        # Latest data reload kar rahe hain.
        db.refresh(post)

        return post