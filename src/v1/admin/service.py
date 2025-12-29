from src.v1.model import Schedule, Venue, ScheduleException, Department, Level, Role_Enum, User
from .schema import CreateVenue, CreateTimeTable
import uuid

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


from src.v1.base.exception import (
    AlreadyExistsError,
    AuthorizationError,
    InvalidEmailPassword,
    NotFoundError,
    ServerError,
)


from src.v1.service.courses import CourseService
from src.v1.service.lecturer_service import LecturerService
from src.v1.service.student_service import StudentService

from src.util.log import setup_logger

logger = setup_logger(__name__, "admin_service.log")

class AdminService():
    def __init__(self, db:AsyncSession):
        self.db = db
    
    def add_course_to_a_department_level():
        pass 
    
    async def check_if_venue_exist_by_name(self, venue_data: CreateVenue):
        try:
            stmt = await self.db.execute(select(Venue).where(
                    func.lower(Venue.name) == venue_data.name.lower()
                )
            )
            return stmt.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking venue existence by name '{venue_data.name}': {e}")
            raise ServerError()

    async def check_if_venue_exist_by_id(self, venue_data: CreateVenue):
        try:
            stmt = await self.db.execute(select(Venue).where(
                    Venue.id == venue_data.venue_id
                )
            )
            return stmt.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking venue existence by id '{venue_data.venue_id}': {e}")
            raise ServerError()
    
    async def create_venue(self, venue_data: CreateVenue):
        try:
            logger.info(f"Attempting to create venue with name: {venue_data.name} and id: {venue_data.venue_id}")

            # Check if venue exists by id
            existing_venue = await self.check_if_venue_exist_by_id(venue_data)
            if existing_venue:
                logger.warning(f"Venue with id {venue_data.venue_id} already exists.")
                raise AlreadyExistsError(f"Venue with id {venue_data.venue_id} already exists")

            # Check if venue exists by name
            existing_venue = await self.check_if_venue_exist_by_name(venue_data)
            if existing_venue:
                logger.warning(f"Venue with name '{venue_data.name}' already exists.")
                raise AlreadyExistsError(f"Venue with name '{venue_data.name}' already exists")

            # Create new venue
            new_venue = Venue(
                name=venue_data.name
            )

            self.db.add(new_venue)
            await self.db.commit()
            await self.db.refresh(new_venue)
            logger.info(f"Venue {new_venue.name} created successfully with id {new_venue.id}.")
            return new_venue

        except AlreadyExistsError:
            logger.error(f"Failed to create venue: {venue_data.name} already exists")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating venue {venue_data.name}: {e}")
            await self.db.rollback()
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"Unexpected error while creating venue {venue_data.name}: {e}")
        #     await self.db.rollback()
        #     raise ServerError()
    
    def create_timetable(timetable_data: CreateTimeTable):
        #the creation logic is mostly dealing with conflict check
        pass 
    
    def assign_course_to_lecturer():
        pass
