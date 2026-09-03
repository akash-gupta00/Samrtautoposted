# Python logging configuration ke liye fileConfig import kar rahe hain.
# Alembic migration logs ko configure karne ke liye use hota hai.
from logging.config import fileConfig

# SQLAlchemy se engine_from_config import kar rahe hain.
# Ye alembic.ini ke database URL se engine banata hai.
from sqlalchemy import engine_from_config

# SQLAlchemy pool import kar rahe hain.
# NullPool ka use migration ke time simple connection ke liye hoga.
from sqlalchemy import pool

# Alembic context import kar rahe hain.
# Ye migration environment ko control karta hai.
from alembic import context

# Project ka Base import kar rahe hain.
# Base ke andar sabhi SQLAlchemy models ki metadata hoti hai.
from app.database.base import Base

# User model import kar rahe hain.
# Is import se Alembic ko users table ka structure pata chalega.
from app.models.user import User


# Alembic Config object le rahe hain.
# Ye alembic.ini file ki settings ko access karta hai.
config = context.config


# Agar config file available hai to logging setup karenge.
# Isse Alembic migration logs terminal me proper dikhte hain.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Alembic ko SQLAlchemy models ki metadata de rahe hain.
# Autogenerate migration isi metadata se database changes detect karega.
target_metadata = Base.metadata


# Offline mode me migration run karne wala function.
# Offline mode me database se direct connection nahi banta.
def run_migrations_offline() -> None:

    # alembic.ini se database URL read kar rahe hain.
    url = config.get_main_option("sqlalchemy.url")

    # Migration context configure kar rahe hain.
    context.configure(
        url=url,

        # Models ki metadata provide kar rahe hain.
        target_metadata=target_metadata,

        # SQL values ko literal string ke form me generate karega.
        literal_binds=True,

        # SQL parameter style define kar rahe hain.
        dialect_opts={"paramstyle": "named"},
    )

    # Migration transaction start kar rahe hain.
    with context.begin_transaction():

        # Migration commands run kar rahe hain.
        context.run_migrations()


# Online mode me migration run karne wala function.
# Ye real database connection ke saath migration run karta hai.
def run_migrations_online() -> None:

    # alembic.ini settings se database engine create kar rahe hain.
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),

        # sqlalchemy. prefix wali settings use karega.
        prefix="sqlalchemy.",

        # Migration ke time connection pool disable/simple rakha gaya hai.
        poolclass=pool.NullPool,
    )

    # Database connection open kar rahe hain.
    with connectable.connect() as connection:

        # Migration context ko database connection aur metadata ke saath configure kar rahe hain.
        context.configure(
            connection=connection,

            # Models ki metadata yahan pass kar rahe hain.
            target_metadata=target_metadata,
        )

        # Migration transaction start kar rahe hain.
        with context.begin_transaction():

            # Migration commands run kar rahe hain.
            context.run_migrations()


# Agar Alembic offline mode me run ho raha hai to offline migration chalegi.
if context.is_offline_mode():
    run_migrations_offline()

# Warna normal online migration chalegi.
else:
    run_migrations_online()