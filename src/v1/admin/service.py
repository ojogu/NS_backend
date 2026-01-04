import uuid
from datetime import date, datetime, time, timedelta, timezone

from dateutil.rrule import rrulestr
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.util.log import setup_logger
from src.v1.auth.service import password_hash
from src.v1.base.exception import (
    AlreadyExistsError,
    NotFoundError,
    ServerError,
)
from src.v1.model import Role_Enum, TimeTable, TimeTableException, User, Venue, Semester
from src.v1.service.courses import CourseService, DeptService
from src.v1.service.user import UserService

from .schema import Admin, CreateTimeTable, CreateVenue, CreateSemester

logger = setup_logger(__name__, "admin_service.log")


class VenueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_if_venue_exist_by_name(self, venue_name: str):
        try:
            stmt = await self.db.execute(
                select(Venue).where(func.lower(Venue.name) == venue_name.lower())
            )
            return stmt.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking venue existence by name '{venue_name}': {e}"
            )
            raise ServerError()

    async def check_if_venue_exist_by_id(self, venue_id):
        try:
            stmt = await self.db.execute(select(Venue).where(Venue.id == venue_id))
            return stmt.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking venue existence by id '{venue_id}': {e}"
            )
            raise ServerError()

    async def fetch_venue_by_id(self, venue_id):
        try:
            venue = await self.check_if_venue_exist_by_id(venue_id)
            if not venue:
                raise NotFoundError()
            return venue
        except SQLAlchemyError as e:
            logger.error(f"Error while fetching venue data: {e}")
            raise ServerError()

    async def fetch_all_venues(self):
        try:
            stmt = await self.db.execute(select(Venue))
            venue = stmt.scalars().all()
            if not venue:
                return []
            return venue
        except SQLAlchemyError as e:
            logger.error(f"errors fetching venues: {e}")
            raise ServerError()

    async def create_venue(self, venue_data: CreateVenue):
        try:
            logger.info(
                f"Attempting to create venue with name: {venue_data.name}"
            )

            # Check if venue exists by name
            existing_venue = await self.check_if_venue_exist_by_name(venue_data.name)
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

    async def update_venue(self, venue_id, venue_data: CreateVenue):
        try:
            venue = await self.fetch_venue_by_id(venue_id)
            if not venue:
                raise NotFoundError()

            venue.name = venue_data.name

            await self.db.commit()
            await self.db.refresh(venue)
            logger.info(f"Venue {venue.name} updated successfully.")
            return venue
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating venue {venue_id}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def delete_venue(self, venue_id):
        try:
            venue = await self.fetch_venue_by_id(venue_id)
            if not venue:
                raise NotFoundError()

            await self.db.delete(venue)
            await self.db.commit()
            logger.info(f"Venue {venue.name} deleted successfully.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting venue {venue_id}: {e}")
            await self.db.rollback()
            raise ServerError()


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


class TimeTableService:
    def __init__(self, db: AsyncSession, venue_service: VenueService, course_service: CourseService, semester_service: SemesterService):
        self.db = db
        self.venue_service = venue_service
        self.course_service = course_service
        self.semester_service = semester_service
        
    @staticmethod
    def make_aware_range(start_date, end_date):
        """Converts date objects to aware datetimes at the very start and end of the day."""
        # Use time.min for the start (00:00:00)
        aware_start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        logger.info(f"Created timezone aware start datetime: {aware_start}")
        # Use time.max for the end (23:59:59.999)
        aware_end = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        logger.info(f"Created timezone aware end datetime: {aware_end}")
    
        return aware_start, aware_end
    
    # @staticmethod
    # def parse_time_str(time_str):
    #     return time.fromisoformat(time_str)
    
    async def generate_dates_from_rrule(self, rrule_str: str, start_date: date, end_date: date, start_time:time) -> list[datetime]:
        #convert date object to datetime/timezone aware object
        semester_start_datetime, semester_end_datetime = TimeTableService.make_aware_range(start_date, end_date)
        rrule_obj = rrulestr(rrule_str)
        
        # #parse time string to time object
        # course_start_time = TimeTableService.parse_time_str(start_time)
        
        #create the anchor dt (add the course time)
        anchor_dt = datetime.combine(semester_start_datetime, start_time, tzinfo=timezone.utc)
        
        #replace anchor to use the anchor_dt
        rrule_obj = rrule_obj.replace(dtstart=anchor_dt)
        logger.info(f"new rrule: {rrule_obj}")
        
        #search window (usually the whole semester)
        final_dates = list(rrule_obj.between(semester_start_datetime, semester_end_datetime, inc=True))
        logger.info(f"Generated dates from rrule: start_date={start_date}, end_date={end_date}, dates={final_dates[:5]}")
        return final_dates

    
    async def check_for_conflicts(self, venue_id:uuid.UUID, new_dates:list, start_time:time, duration_minutes:int):
        # Fetch existing timetables for the venue with related semester data
        existing_stmt = await self.db.execute(
            select(TimeTable).options(selectinload(TimeTable.semester)).where(TimeTable.venue_id == venue_id)
        )
        existing_schedules = existing_stmt.scalars().all()

        #parse time string to time object
        # course_start_time = TimeTableService.parse_time_str(start_time)
        
        for new_date in new_dates:
            new_start = datetime.combine(new_date, start_time)
            new_end = new_start + timedelta(minutes=duration_minutes)

            for existing in existing_schedules:
                start_date, end_date = TimeTableService.make_aware_range(existing.semester.start_date, existing.semester.end_date,)
                existing_rrule = rrulestr(existing.rrule)
                
                logger.info(f"existing rrule:{existing_rrule}")
                logger.info(f"existing start date:{start_date}")
                logger.info(f"existing end date:{end_date}")
                existing_dates = list(
                    existing_rrule.between(
                        start_date,
                        end_date,
                        inc=True,
                    )
                )

                # Check for exceptions
                for existing_date in existing_dates:
                    exception_stmt = await self.db.execute(
                        select(TimeTableException).where(
                            TimeTableException.schedule_id == existing.id,
                            TimeTableException.exception_date == existing_date,
                        )
                    )
                    exception = exception_stmt.scalar_one_or_none()
                    if exception and exception.is_cancelled:
                        continue  # Skip cancelled dates

                    existing_start = datetime.combine(
                        existing_date, existing.start_time.time()
                    )
                    existing_end = existing_start + timedelta(minutes=existing.duration_minutes)

                    # Check for time overlap
                    if (new_start < existing_end) and (new_end > existing_start):
                        raise AlreadyExistsError(
                            f"TimeTable conflict with existing timetable on {existing_date.strftime('%Y-%m-%d')}."
                        )

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
            rrule_str = timetable_data.rrule.to_rrule_string()
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


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(self.db)
        self.course_service = CourseService(self.db)
        self.dept = DeptService(self.db)
        self.venue_service = VenueService(self.db)
        self.semester_service = SemesterService(self.db)
        self.timetable_service = TimeTableService(self.db, self.venue_service, self.course_service, self.semester_service)

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

    # Delegate methods for VenueService
    async def check_if_venue_exist_by_name(self, venue_name: str):
        return await self.venue_service.check_if_venue_exist_by_name(venue_name)

    async def check_if_venue_exist_by_id(self, venue_id):
        return await self.venue_service.check_if_venue_exist_by_id(venue_id)

    async def fetch_venue_by_id(self, venue_id):
        return await self.venue_service.fetch_venue_by_id(venue_id)

    async def fetch_all_venues(self):
        return await self.venue_service.fetch_all_venues()

    async def create_venue(self, venue_data: CreateVenue):
        return await self.venue_service.create_venue(venue_data)

    async def update_venue(self, venue_id, venue_data: CreateVenue):
        return await self.venue_service.update_venue(venue_id, venue_data)

    async def delete_venue(self, venue_id):
        return await self.venue_service.delete_venue(venue_id)

    # Delegate methods for SemesterService
    async def check_if_semester_exist_by_session(self, session: str):
        return await self.semester_service.check_if_semester_exist_by_session(session)

    async def check_if_semester_exist_by_id(self, semester_id):
        return await self.semester_service.check_if_semester_exist_by_id(semester_id)

    async def fetch_semester_by_id(self, semester_id):
        return await self.semester_service.fetch_semester_by_id(semester_id)

    async def fetch_all_semesters(self):
        return await self.semester_service.fetch_all_semesters()

    async def create_semester(self, semester_data: CreateSemester):
        return await self.semester_service.create_semester(semester_data)

    async def update_semester(self, semester_id, semester_data: CreateSemester):
        return await self.semester_service.update_semester(semester_id, semester_data)

    async def delete_semester(self, semester_id):
        return await self.semester_service.delete_semester(semester_id)

    # Delegate methods for TimeTableService
    async def create_timetable(self, timetable_data: CreateTimeTable):
        return await self.timetable_service.create_timetable(timetable_data)

    async def fetch_all_timetables(self):
        return await self.timetable_service.fetch_all_timetables()

    async def fetch_timetable_by_id(self, timetable_id):
        return await self.timetable_service.fetch_timetable_by_id(timetable_id)

    async def update_timetable(self, timetable_id, timetable_data: CreateTimeTable):
        return await self.timetable_service.update_timetable(timetable_id, timetable_data)

    async def delete_timetable(self, timetable_id):
        return await self.timetable_service.delete_timetable(timetable_id)

    # Delegate methods for CourseService
    async def check_if_course_exists(self, name: str, code: str):
        return await self.course_service.check_if_course_exists(name, code)

    async def check_if_course_exists_by_id(self, course_id: uuid.UUID):
        return await self.course_service.check_if_course_exists_by_id(course_id)

    async def create_course(self, course_data):
        return await self.course_service.create_course(course_data)

    async def update_course(self, course_id: uuid.UUID, course_data):
        return await self.course_service.update_course(course_id, course_data)

    async def delete_course(self, course_id: uuid.UUID):
        return await self.course_service.delete_course(course_id)

    async def fetch_all_courses(self):
        return await self.course_service.fetch_all_courses()

    # Delegate methods for DeptService
    async def fetch_all_courses_for_a_dept(self, dept_id: uuid.UUID):
        return await self.dept.fetch_all_courses_for_a_dept(dept_id)

    async def fetch_all_dept(self):
        return await self.dept.fetch_all_dept()

    async def create_dept(self, dept_name: str):
        return await self.dept.create_dept(dept_name)

    async def update_dept(self, dept_id: uuid.UUID, dept_name: str):
        return await self.dept.update_dept(dept_id, dept_name)

    async def delete_dept(self, dept_id: uuid.UUID):
        return await self.dept.delete_dept(dept_id)

    async def check_if_dept_exist_by_name(self, dept_name: str):
        return await self.dept.check_if_dept_exist_by_name(dept_name)

    async def check_if_dept_exist_by_id(self, dept_id: uuid.UUID):
        return await self.dept.check_if_dept_exist_by_id(dept_id)

    # Delegate methods for UserService
    async def check_if_user_exist_by_email(self, email: str):
        return await self.user_service.check_if_user_exist_by_email(email)

    async def check_if_user_exist_by_id(self, user_id: uuid.UUID):
        return await self.user_service.check_if_user_exist_by_id(user_id)

    async def check_if_user_exist_by_school_id(self, school_id: str):
        return await self.user_service.check_if_user_exist_by_school_id(school_id)

    async def create_user(self, user_data):
        return await self.user_service.create_user(user_data)

    async def update_user(self, user_id: uuid.UUID, user_data):
        return await self.user_service.update_user(user_id, user_data)

    async def delete_user(self, user_id: uuid.UUID):
        return await self.user_service.delete_user(user_id)

    async def fetch_all_users(self):
        return await self.user_service.fetch_all_users()

    async def fetch_all_lecturers(self):
        return await self.user_service.fetch_all_lecturers()

    async def fetch_all_students(self):
        return await self.user_service.fetch_all_students()

    def add_course_to_a_department_level():
        pass

    def assign_course_to_lecturer():
        pass
