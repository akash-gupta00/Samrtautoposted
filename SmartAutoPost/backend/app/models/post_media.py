from sqlalchemy import Table, Column, Integer, ForeignKey

from app.database.base_class import Base


post_media = Table(
    "post_media",
    Base.metadata,

    Column(
        "post_id",
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True,
    ),

    Column(
        "media_id",
        Integer,
        ForeignKey("media.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)