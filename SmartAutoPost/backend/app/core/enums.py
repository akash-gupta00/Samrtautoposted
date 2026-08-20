# Enum class import kar rahe hain.
# Iska use fixed values banane ke liye hota hai.
from enum import Enum


# PostStatus naam ka Enum bana rahe hain.
# Isme post ke allowed status rahenge.
class PostStatus(str, Enum):

    # Draft status.
    # Matlab post abhi sirf save hui hai, publish/schedule nahi hui.
    DRAFT = "draft"

    # Scheduled status.
    # Matlab post future time ke liye schedule hai.
    SCHEDULED = "scheduled"

    # Published status.
    # Matlab post publish ho chuki hai.
    PUBLISHED = "published"

    # Failed status.
    # Matlab post publish karte time error aaya.
    FAILED = "failed"