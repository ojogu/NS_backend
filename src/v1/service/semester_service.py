import uuid
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.log import setup_logger
from src.v1.base.exception import (
    AlreadyExistsError,
    NotFoundError,
    ServerError,
)
from src.v1.model import Semester

from src.v1.admin.schema import CreateSemester

logger = setup_logger(__name__, "semester_service.log")


class SemesterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_if_semester_exist_by_session(self, session: str, semester_name: str = None):
        try:
            query = select(Semester).where(Semester.school_session == session)
            if semester_name:
                query = query.where(Semester.name == semester_name)
            stmt = await self.db.execute(query)
            return stmt.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking semester existence by session '{session}' and name '{semester_name}': {e}"
            )
            raise ServerError()

    async def check_if_semester_exist_by_id(self, semester_id):
        try:
            stmt = await self.db.execute(select(Semester).where(Semester.id == semester_id))
            return stmt.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking semester existence by id '{semester_id}': {e}"
            )
            raise ServerError()

    async def fetch_semester_by_id(self, semester_id):
        try:
            semester = await self.check_if_semester_exist_by_id(semester_id)
            if not semester:
                raise NotFoundError()
            return semester
        except SQLAlchemyError as e:
            logger.error(f"Error while fetching semester data: {e}")
            raise ServerError()

    async def fetch_all_semesters(self):
        try:
            stmt = await self.db.execute(select(Semester))
            semesters = stmt.scalars().all()
            if not semesters:
                return []
            return semesters
        except SQLAlchemyError as e:
            logger.error(f"errors fetching semesters: {e}")
            raise ServerError()

    async def create_semester(self, semester_data: CreateSemester):
        try:
            logger.info(
                f"Attempting to create semester with session: {semester_data.school_session}"
            )

            # Check if semester exists by session and name
            existing_semester = await self.check_if_semester_exist_by_session(semester_data.school_session, semester_data.name)
            if existing_semester:
                logger.warning(f"Semester with session '{semester_data.school_session}' and name '{semester_data.name}' already exists.")
                raise AlreadyExistsError(
                    f"Semester with session '{semester_data.school_session}' and name '{semester_data.name}' already exists"
                )

            # Create new semester
            new_semester = Semester(
                name=semester_data.name,
                school_session=semester_data.school_session,
                start_date=semester_data.start_date,
                end_date=semester_data.end_date,
            )

            self.db.add(new_semester)
            await self.db.commit()
            await self.db.refresh(new_semester)
            logger.info(
                f"Semester {new_semester.school_session} created successfully with id {new_semester.id}."
            )
            return new_semester

        except AlreadyExistsError:
            logger.error(f"Failed to create semester: {semester_data.school_session} already exists")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating semester {semester_data.school_session}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def update_semester(self, semester_id, semester_data: CreateSemester):
        try:
            semester = await self.fetch_semester_by_id(semester_id)
            if not semester:
                raise NotFoundError()

            semester.name = semester_data.name
            semester.school_session = semester_data.school_session
            semester.start_date = semester_data.start_date
            semester.end_date = semester_data.end_date

            await self.db.commit()
            await self.db.refresh(semester)
            logger.info(f"Semester {semester.school_session} updated successfully.")
            return semester
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating semester {semester_id}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def delete_semester(self, semester_id):
        try:
            semester = await self.fetch_semester_by_id(semester_id)
            if not semester:
                raise NotFoundError()

            await self.db.delete(semester)
            await self.db.commit()
            logger.info(f"Semester {semester.school_session} deleted successfully.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting semester {semester_id}: {e}")
            await self.db.rollback()
            raise ServerError()