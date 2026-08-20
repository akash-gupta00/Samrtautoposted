# SQLAlchemy se create_engine import kar rahe hain.
# create_engine database ke saath connection engine banata hai.
from sqlalchemy import create_engine

# SQLAlchemy se sessionmaker import kar rahe hain.
# sessionmaker database session create karne ke liye use hota hai.
from sqlalchemy.orm import sessionmaker

# Apne project ki settings import kar rahe hain.
# Isse DATABASE_URL config.py se milega.
from app.core.config import settings


# Database engine bana rahe hain.
# Engine ka kaam Python application aur PostgreSQL ke beech connection manage karna hai.
engine = create_engine(settings.DATABASE_URL)


# SessionLocal database session factory hai.
# Har API request ke time ek naya database session banega.
SessionLocal = sessionmaker(
    autocommit=False,  # Har query ke baad auto commit nahi hoga.
    autoflush=False,   # SQLAlchemy automatic flush nahi karega.
    bind=engine        # Is session ko upar wale engine se connect kar rahe hain.
)


# Ye function database session provide karega.
# FastAPI dependencies me iska use hoga.
def get_db():

    # Naya database session create kar rahe hain.
    db = SessionLocal()

    try:
        # API ko database session return kar rahe hain.
        yield db

    finally:
        # Request complete hone ke baad database session close kar rahe hain.
        db.close()