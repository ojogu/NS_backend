from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.util.log import setup_logger
from src.v1.base.exception import ServerError
from src.v1.model import Role_Enum, User

logger = setup_logger(__name__, "student_service.log")


class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_all_students(self):
        try:
            stmt = await self.db.execute(
                select(User)
                .options(selectinload(User.department), selectinload(User.level))
                .where(User.role == Role_Enum.STUDENT)
            )
            students = stmt.scalars().all()
            logger.info(f"Successfully fetched {len(students)} students.")
            return students
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching all students: {e}")
            raise ServerError()
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while fetching all students: {e}"
            )
            raise ServerError()
