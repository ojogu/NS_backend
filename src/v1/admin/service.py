from datetime import datetime

from dateutil.rrule import rrulestr
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.log import setup_logger
from src.v1.auth.service import password_hash
from src.v1.base.exception import (
    AlreadyExistsError,
    NotFoundError,
    ServerError,
)
from src.v1.model import Role_Enum, Schedule, ScheduleException, User, Venue
from src.v1.service.courses import CourseService

from .schema import Admin, CreateTimeTable, CreateVenue

logger = setup_logger(__name__, "admin_service.log")


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.course_service = CourseService(self.db)

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

    def add_course_to_a_department_level():
        pass

    async def check_if_venue_exist_by_name(self, venue_data: CreateVenue):
        try:
            stmt = await self.db.execute(
                select(Venue).where(func.lower(Venue.name) == venue_data.name.lower())
            )
            return stmt.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking venue existence by name '{venue_data.name}': {e}"
            )
            raise ServerError()

    async def check_if_venue_exist_by_id(self, venue_data: CreateVenue):
        try:
            stmt = await self.db.execute(select(Venue).where(Venue.id == venue_data.id))
            return stmt.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking venue existence by id '{venue_data.id}': {e}"
            )
            raise ServerError()

    async def create_venue(self, venue_data: CreateVenue):
        try:
            logger.info(
                f"Attempting to create venue with name: {venue_data.name} and id: {venue_data.id}"
            )

            # Check if venue exists by name
            existing_venue = await self.check_if_venue_exist_by_name(venue_data)
            if existing_venue:
                logger.warning(f"Venue with name '{venue_data.name}' already exists.")
                raise AlreadyExistsError(
                    f"Venue with name '{venue_data.name}' already exists"
                )

            # Create new venue
            new_venue = Venue(name=venue_data.name)

            self.db.add(new_venue)
            await self.db.commit()
            await self.db.refresh(new_venue)
            logger.info(
                f"Venue {new_venue.name} created successfully with id {new_venue.id}."
            )
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

    async def create_timetable(self, timetable_data: CreateTimeTable):
        try:
            logger.info(
                f"Attempting to create timetable for course {timetable_data.course_id} in venue {timetable_data.venue_id}."
            )

            # Check if course exists
            course = await self.course_service.check_if_course_exists_by_id(
                timetable_data.course_id
            )
            if not course:
                logger.warning(
                    f"Timetable creation failed: Course {timetable_data.course_id} does not exist."
                )
                raise NotFoundError(f"Course {timetable_data.course_id} does not exist")

            # Check if venue exists
            venue_stmt = await self.db.execute(
                select(Venue).where(Venue.id == timetable_data.venue_id)
            )
            venue = venue_stmt.scalar_one_or_none()
            if not venue:
                logger.warning(
                    f"Timetable creation failed: Venue {timetable_data.venue_id} does not exist."
                )
                raise NotFoundError(f"Venue {timetable_data.venue_id} does not exist")

            # Parse the rrule and generate dates within the semester
            rrule_obj = rrulestr(timetable_data.rrule)
            new_dates = list(
                rrule_obj.between(
                    timetable_data.semester_start_date,
                    timetable_data.semester_end_date,
                    inc=True,
                )
            )

            # Fetch existing schedules for the venue
            existing_stmt = await self.db.execute(
                select(Schedule).where(Schedule.venue_id == timetable_data.venue_id)
            )
            existing_schedules = existing_stmt.scalars().all()

            # Check for conflicts
            for new_date in new_dates:
                new_start = datetime.combine(new_date, timetable_data.start_time)
                new_end = new_start + timetable_data.duration_minutes

                for existing in existing_schedules:
                    existing_rrule = rrulestr(existing.rrules)
                    existing_dates = list(
                        existing_rrule.between(
                            existing.semester_start_date,
                            existing.semester_end_date,
                            inc=True,
                        )
                    )

                    for existing_date in existing_dates:
                        # Check for exceptions
                        exception_stmt = await self.db.execute(
                            select(ScheduleException).where(
                                ScheduleException.schedule_id == existing.id,
                                ScheduleException.exception_date == existing_date,
                            )
                        )
                        exception = exception_stmt.scalar_one_or_none()
                        if exception and exception.is_cancelled:
                            continue  # Skip cancelled dates

                        existing_start = datetime.combine(
                            existing_date, existing.start_time
                        )
                        existing_end = existing_start + existing.duration

                        # Check for time overlap
                        if (new_start < existing_end) and (new_end > existing_start):
                            logger.warning(
                                f"Timetable creation failed: Conflict detected with existing schedule {existing.id} on {existing_date}."
                            )
                            raise AlreadyExistsError(
                                f"Schedule conflict with existing timetable on {existing_date.strftime('%Y-%m-%d')}."
                            )

            # No conflicts, create the new schedule
            new_schedule = Schedule(
                course_id=timetable_data.course_id,
                venue_id=timetable_data.venue_id,
                start_time=timetable_data.start_time,
                duration=timetable_data.duration_minutes,
                rrules=timetable_data.rrule,
                semester_start_date=timetable_data.semester_start_date,
                semester_end_date=timetable_data.semester_end_date,
            )
            self.db.add(new_schedule)
            await self.db.commit()
            await self.db.refresh(new_schedule)
            logger.info(
                f"Successfully created timetable {new_schedule.id} for course {timetable_data.course_id} in venue {timetable_data.venue_id}."
            )
            return new_schedule

        except SQLAlchemyError as e:
            logger.error(f"Database error while creating timetable: {e}")
            await self.db.rollback()
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"Unexpected error while creating timetable: {e}")
        #     await self.db.rollback()
        #     raise ServerError()

    def assign_course_to_lecturer():
        pass
