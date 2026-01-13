from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.log import setup_logger
from src.v1.auth.service import password_hash
from src.v1.base.exception import (
    AlreadyExistsError,
    ServerError,
)
from src.v1.model import Role_Enum, User

from .schema import Admin

logger = setup_logger(__name__, "admin_service.log")


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_admin(self, user_data: Admin):
        try:
            logger.info(f"Attempting to create admin with email: {user_data.email}")

            # Check if user exists by email
            stmt = await self.db.execute(
                select(User).where(func.lower(User.email) == user_data.email.lower())
            )
            existing_user = stmt.scalar_one_or_none()
            if existing_user:
                logger.warning(f"User with email '{user_data.email}' already exists.")
                raise AlreadyExistsError(
                    f"User with email '{user_data.email}' already exists"
                )

            # Hash the password
            hashed_password = password_hash(user_data.password)

            # Create new admin user
            new_admin = User(
                email=user_data.email,
                password=hashed_password,
                role=Role_Enum.ADMIN,
            )

            self.db.add(new_admin)
            await self.db.commit()
            await self.db.refresh(new_admin)
            logger.info(
                f"Admin {new_admin.email} created successfully with id {new_admin.id}."
            )
            return new_admin

        except AlreadyExistsError:
            logger.error(f"Failed to create admin: {user_data.email} already exists")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating admin {user_data.email}: {e}")
            await self.db.rollback()
            raise ServerError()
