import uuid
from datetime import date, datetime, time, timedelta, timezone

from dateutil.rrule import rrulestr
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.util.log import setup_logger
from src.v1.base.exception import (
    AlreadyExistsError,
    NotFoundError,
    ServerError,
)
from src.v1.model import TimeTable, TimeTableException
from src.v1.service.courses import CourseService

from src.v1.admin.schema import CreateTimeTable
from .venue_service import VenueService
from .semester_service import SemesterService
from .lecturer_service import LecturerService

logger = setup_logger(__name__, "timetable_service.log")


class TimeTableService:
    def __init__(self, db: AsyncSession, venue_service: VenueService, course_service: CourseService, semester_service: SemesterService, lecturer_service: LecturerService):
        self.db = db
        self.venue_service = venue_service
        self.course_service = course_service
        self.semester_service = semester_service
        self.lecturer_service = lecturer_service
        
    @staticmethod
    def make_aware(start, end=None):
        """Converts date or datetime objects to timezone-aware datetimes.

        If end is None, converts a single date/datetime to aware.
        For dates, creates datetime at start of day.
        For datetimes, makes them timezone-aware if naive.

        If end is provided, converts two date objects to aware datetimes
        at the very start and end of the day.
        """
        if end is None:
            # Single conversion case
            if isinstance(start, datetime):
                if start.tzinfo is None:
                    aware = start.replace(tzinfo=timezone.utc)
                    logger.info(f"Created timezone aware datetime: {aware}")
                    return aware
                else:
                    logger.info(f"Datetime already timezone aware: {start}")
                    return start
            elif isinstance(start, date):
                aware = datetime.combine(start, time.min, tzinfo=timezone.utc)
                logger.info(f"Created timezone aware datetime from date: {aware}")
                return aware
            else:
                raise ValueError("Input must be a date or datetime object")
        else:
            # Range conversion case (original functionality)
            # Use time.min for the start of the day(00:00:00)
            aware_start = datetime.combine(start, time.min, tzinfo=timezone.utc)
            logger.info(f"Created timezone aware start datetime: {aware_start}")
            # Use time.max for the end of the day(23:59:59.999)
            aware_end = datetime.combine(end, time.max, tzinfo=timezone.utc)
            logger.info(f"Created timezone aware end datetime: {aware_end}")

            return aware_start, aware_end
    
    async def generate_dates_from_rrule(self, rrule_str: str, start_date: date, end_date: date, start_time:time) -> list[datetime]:
        logger.debug("calling the function: generate dates from rrule")
        #convert date object to datetime/timezone aware object
        semester_start_datetime, semester_end_datetime = TimeTableService.make_aware(start_date, end_date)
        rrule_obj = rrulestr(rrule_str)
        logger.debug("calling the make aware function from : generate dates from rrule function")
        # #parse time string to time object
        # course_start_time = TimeTableService.parse_time_str(start_time)
        
        #create the anchor dt (add the course time to the semester start to get the course start time)
        anchor_dt = datetime.combine(semester_start_datetime, start_time, tzinfo=timezone.utc)
        
        #replace anchor to use the anchor_dt
        rrule_obj = rrule_obj.replace(dtstart=anchor_dt)
        logger.info(f"new rrule: {rrule_obj}")
        
        #search window (usually the whole semester)
        final_dates = list(rrule_obj.between(semester_start_datetime, semester_end_datetime, inc=True))
        logger.info(f"Generated dates from rrule: start_date={start_date}, end_date={end_date}, dates count={len(final_dates)}")
        return final_dates

    async def _check_lecturer_conflict(self, lecturer_id, start_time, end_time, exclude_course_id=None ):
        #exclude course id is the course we are trying to reschedule
        
        """
        Check if lecturer has other classes during this time.
        """
        conflicts = []
        
        #fetch all courses thaught by a lecturer
        lecturer_courses = await self.lecturer_service.fetch_lecturer_courses()
        
        for courses in lecturer_courses:
            #skip the course we are trying to reschedule
            if exclude_course_id and courses.id == exclude_course_id:
                continue
       
    async def check_student_conflict():
        pass 
    async def check_venue_conflict():
        pass 
    async def check_for_conflicts(self, venue_id: uuid.UUID, new_dates: list, start_time: time, duration_minutes: int):
    #algorithm
    #  Fetch all existing schedules for the venue
    # For each new date, calculate start_time and end_time
    # For each existing schedule, parse its rrule to get its recurring dates
    # For each date in the existing schedule, check if it's cancelled → skip if cancelled
    # Check for time overlap conflict
        try:
            logger.debug(f"Checking for conflicts: venue_id={venue_id}, new_dates_count={len(new_dates)}, start_time={start_time}, duration_minutes={duration_minutes}")

            # Input validation
            if not isinstance(venue_id, uuid.UUID):
                raise ValueError("venue_id must be a valid UUID")
            if not new_dates or not isinstance(new_dates, list):
                raise ValueError("new_dates must be a non-empty list")
            if not isinstance(start_time, time):
                raise ValueError("start_time must be a time object")
            if not isinstance(duration_minutes, int) or duration_minutes <= 0:
                raise ValueError("duration_minutes must be a positive integer")

            # Fetch existing timetables for the venue with related semester data
            logger.debug(f"Fetching existing timetables for venue {venue_id}")
            existing_stmt = await self.db.execute(
                select(TimeTable).options(selectinload(TimeTable.semester)).where(TimeTable.venue_id == venue_id)
            )
            existing_schedules = existing_stmt.scalars().all()
            logger.debug(f"Found {len(existing_schedules)} existing schedules for venue {venue_id}")

            # PRE-LOAD all exceptions for these schedules (ONE query instead of N queries)
            schedule_ids = [schedule.id for schedule in existing_schedules]
            cancelled_dates = set()
            if schedule_ids:
                logger.debug(f"Pre-loading exceptions for {len(schedule_ids)} schedules")
                exceptions_stmt = await self.db.execute(
                    select(TimeTableException).where(
                        TimeTableException.schedule_id.in_(schedule_ids),
                        TimeTableException.is_cancelled
                    )
                )
                exceptions = exceptions_stmt.scalars().all()
                logger.debug(f"Found {len(exceptions)} cancelled exceptions")

                # Create a set of (schedule_id, date) tuples for fast lookup
                cancelled_dates = {
                    (exc.schedule_id, exc.exception_date) for exc in exceptions
                }

            for new_date in new_dates:
                # Validate new_date
                logger.info(f"doing check for {new_date}")
                if not isinstance(new_date, datetime):
                    logger.error(f"Invalid new_date type: {type(new_date)}, expected datetime")
                    raise ValueError("All dates in new_dates must be datetime objects")

                # Loop through the new dates, for each one, calculates when it starts and ends
                new_start = datetime.combine(new_date, start_time)
                new_end = new_start + timedelta(minutes=duration_minutes)
                logger.debug(f"Checking conflicts for new schedule: {new_start} - {new_end} for date {new_date}")

                for existing in existing_schedules:
                    try:
                        start_date, end_date = TimeTableService.make_aware(
                            existing.semester.start_date,
                            existing.semester.end_date
                        )
                        #For each existing schedule, parse its rrule to get its recurring dates
                        existing_rrule = rrulestr(existing.rrule)
                        anchor_dt = TimeTableService.make_aware(existing_rrule._dtstart)
                        existing_rrule = existing_rrule.replace(dtstart=anchor_dt)

                        existing_dates = list(
                            existing_rrule.between(start_date, end_date, inc=True)
                        )
                        logger.debug(f"Generated {len(existing_dates)} existing dates for schedule {existing.id}")

                        for existing_date in existing_dates:
                            # Check if this date is cancelled using the pre-loaded set
                            if (existing.id, existing_date) in cancelled_dates:
                                logger.debug(f"Skipping cancelled date {existing_date} for schedule {existing.id}")
                                continue  # Skip cancelled dates

                            # Validate existing.start_time is time object
                            if not hasattr(existing.start_time, 'hour'):
                                logger.error(f"Invalid start_time for existing schedule {existing.id}: {existing.start_time}")
                                raise ValueError("Existing schedule start_time must be a time object")

                            existing_start = datetime.combine(existing_date, existing.start_time)
                            existing_end = existing_start + timedelta(minutes=existing.duration_minutes)

                            # Check for time overlap
                            if (new_start < existing_end) and (new_end > existing_start):
                                conflict_msg = f"Timetable conflict with existing timetable {existing.id} on {existing_date.strftime('%Y-%m-%d')} from {existing_start.time()} to {existing_end.time()}"
                                logger.warning(conflict_msg)
                                raise AlreadyExistsError(conflict_msg)

                    except ValueError as ve:
                        logger.error(f"ValueError processing existing schedule {existing.id}: {ve}")
                        raise ServerError(f"Invalid data in existing schedule {existing.id}")

            logger.debug("No conflicts found")

        except AlreadyExistsError:
            # Re-raise conflict errors as they are expected
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking for conflicts: {e}")
            raise ServerError("Database error during conflict check")
        except ValueError as ve:
            logger.error(f"Validation error in check_for_conflicts: {ve}")
            raise ServerError(f"Invalid input data: {ve}")
        except Exception as e:
            logger.error(f"Unexpected error in check_for_conflicts: {e}")
            raise ServerError("Unexpected error during conflict check")
                    
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
            venue = await self.venue_service.check_if_venue_exist_by_id(timetable_data.venue_id)
            if not venue:
                logger.warning(
                    f"Timetable creation failed: Venue {timetable_data.venue_id} does not exist."
                )
                raise NotFoundError(f"Venue {timetable_data.venue_id} does not exist")

            # Find the semester
            semester = await self.semester_service.check_if_semester_exist_by_session(timetable_data.semester_session, timetable_data.semester_name)
            if not semester:
                raise NotFoundError("Semester not found")

            # Parse the rrule attrbute, generate rrule str and generate dates within the semester
            rrule_str = timetable_data.rrule_str.to_rrule_string()
            logger.info(rrule_str)
            
        
            new_dates = await self.generate_dates_from_rrule(
                rrule_str,
                semester.start_date,
                semester.end_date,
                timetable_data.start_time
            )
            # logger.info(f"new dates: {new_dates}")

            # Check for conflicts
            await self.check_for_conflicts(
                timetable_data.venue_id,
                new_dates,
                timetable_data.start_time,
                timetable_data.duration_minutes
            )

            # No conflicts, create the new timetable
            new_schedule = TimeTable(
                course_id=timetable_data.course_id,
                venue_id=timetable_data.venue_id,
                semester_id=semester.id,
                start_time=timetable_data.start_time,
                duration_minutes=timetable_data.duration_minutes,
                rrule=rrule_str,
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

    async def fetch_all_timetables(self):
        try:
            stmt = await self.db.execute(
                select(TimeTable).options(selectinload(TimeTable.semester), selectinload(TimeTable.course), selectinload(TimeTable.venue))
            )
            timetables = stmt.scalars().all()
            logger.info(f"Successfully fetched {len(timetables)} timetables.")
            return timetables
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching all timetables: {e}")
            raise ServerError()

    async def fetch_timetable_by_id(self, timetable_id):
        try:
            stmt = await self.db.execute(
                select(TimeTable).options(selectinload(TimeTable.semester), selectinload(TimeTable.course), selectinload(TimeTable.venue)).where(TimeTable.id == timetable_id)
            )
            timetable = stmt.scalar_one_or_none()
            if not timetable:
                raise NotFoundError()
            return timetable
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching timetable {timetable_id}: {e}")
            raise ServerError()

    async def update_timetable(self, timetable_id, timetable_data: CreateTimeTable):
        try:
            timetable = await self.fetch_timetable_by_id(timetable_id)
            if not timetable:
                raise NotFoundError(f"Timetable with ID {timetable_id} not found")

            # Find the semester
            semester = await self.semester_service.check_if_semester_exist_by_session(timetable_data.semester_session, timetable_data.semester_name)
            if not semester:
                raise NotFoundError("Semester not found")

            # Parse the rrule attribute, generate rrule str
            rrule_str = timetable_data.rrule.to_rrule_string()

            timetable.course_id = timetable_data.course_id
            timetable.venue_id = timetable_data.venue_id
            timetable.semester_id = semester.id
            timetable.start_time = timetable_data.start_time
            timetable.duration_minutes = timetable_data.duration_minutes
            timetable.rrule = rrule_str

            await self.db.commit()
            await self.db.refresh(timetable)
            logger.info(f"Timetable {timetable_id} updated successfully.")
            return timetable
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating timetable {timetable_id}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def delete_timetable(self, timetable_id):
        try:
            timetable = await self.fetch_timetable_by_id(timetable_id)
            if not timetable:
                raise NotFoundError(f"Timetable with ID {timetable_id} not found")

            await self.db.delete(timetable)
            await self.db.commit()
            logger.info(f"Timetable {timetable_id} deleted successfully.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting timetable {timetable_id}: {e}")
            await self.db.rollback()
            raise ServerError()