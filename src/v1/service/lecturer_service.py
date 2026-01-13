from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, date, time
from dateutil.rrule import rrulestr
from typing import List

from src.util.log import setup_logger
from src.v1.base.exception import AlreadyExistsError, AuthorizationError, NotFoundError, ServerError
from src.v1.model import Role_Enum, User, TimeTable, Course
from src.v1.schema.user import UserCourse
from src.v1.schema.timetable import LecturerTimeTableResponse, ClassSchedule
from src.v1.service.courses import CourseService

logger = setup_logger(__name__, "lecturer_service.log")


class LecturerService:
    def __init__(self, db: AsyncSession, course_service: CourseService, user_service):
        self.db = db
        self.course = course_service
        self.user_service = user_service

    async def fetch_all_lecturers(self):
        try:
            stmt = await self.db.execute(
                select(User)
                .options(selectinload(User.department))
                .where(User.role == Role_Enum.LECTURER)
            )
            lecturers = stmt.scalars().all()
            logger.info(f"Successfully fetched {len(lecturers)} lecturers.")
            return lecturers
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching all lecturers: {e}")
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while fetching all lecturers: {e}")
        #     raise ServerError()

    async def link_lecturer_to_course(self, user_data: UserCourse):
        try:
            logger.info(
                f"Attempting to link lecturer {user_data.user_id} to course {user_data.course_id}."
            )
            # lecturers and course must have the same department

            # check if role is lect
            user = await self.user_service.check_if_user_exist_by_id(user_data.user_id)
            if not user:
                logger.warning(f"User {user_data.user_id} not found.")
                raise NotFoundError()
            if user.role != Role_Enum.LECTURER:
                logger.warning(f"User {user.id} is not a lecturer.")
                raise AuthorizationError(
                    f"{user.id} does not have permission to link to course"
                )

            # check if lecturer is already attached to this course
            stmt = await self.db.execute(
                select(User).options(selectinload(User.courses)).where(User.id == user_data.user_id)
            )
            user_with_courses = stmt.scalar_one()
            
            course_ids = [course.id for course in user_with_courses.courses]
            if user_data.course_id in course_ids:
                logger.warning(f"Lecturer {user_data.user_id} is already attached to course {user_data.course_id}.")
                raise AlreadyExistsError("Lecturer is already assigned to this course")

            # check if both the course and user are in the same dept
            course = await self.course.check_course_dept(user_data.course_id)
            if not course:
                logger.warning(f"Course {user_data.course_id} not found.")
                raise NotFoundError()
            if course.department.id != user.department.id:
                logger.warning(
                    f"Course {course.code} and user {user.id} are not in the same department."
                )
                raise AuthorizationError(f"{user.id} cannot register this course")

            # add more checks if needed
            
            user.courses.append(course)
            self.db.add(user)
            await self.db.commit()
            logger.info(
                f"Successfully linked lecturer {user.first_name} to course {course.name}."
            )
            return True
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while linking lecturer {user_data.user_id} to course {user_data.course_id}: {e}",
                exc_info=True,
            )
            await self.db.rollback()
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while linking lecturer {lect_id} to course {course_id.course_id}: {e}")
        #     await self.db.rollback()
        #     raise ServerError()

    async def fetch_lecturer_timetable(self, lecturer_id: str):
        try:
            # First get the lecturer and their courses
            lecturer_stmt = await self.db.execute(
                select(User)
                .options(
                    selectinload(User.courses).options(
                        selectinload(Course.level),
                        selectinload(Course.department)
                    )
                )
                .where(User.id == lecturer_id, User.role == Role_Enum.LECTURER)
            )
            lecturer = lecturer_stmt.scalar_one_or_none()
            if not lecturer:
                logger.warning(f"Lecturer with id {lecturer_id} not found.")
                return []

            course_ids = [course.id for course in lecturer.courses]

            if not course_ids:
                logger.info(f"No courses found for lecturer {lecturer_id}.")
                return []

            # Get timetables for these courses
            timetable_stmt = await self.db.execute(
                select(TimeTable)
                .options(
                selectinload(TimeTable.course).
                options(
                selectinload(Course.level),
                selectinload(Course.department)),
        
                selectinload(TimeTable.venue),
                selectinload(TimeTable.semester)
                )
                .where(TimeTable.course_id.in_(course_ids))
            )
            timetables = timetable_stmt.scalars().all()

            logger.info(f"Successfully fetched {len(timetables)} timetable entries for lecturer {lecturer_id}.")

            # Parse timetables and generate schedule
            parsed_timetables = []
            for timetable in timetables:
                schedule = self._parse_rrule_to_schedule(timetable)
                response = LecturerTimeTableResponse(
                    course_code=timetable.course.code,
                    course_name=timetable.course.name,
                    venue_name=timetable.venue.name,
                    start_time=timetable.start_time,
                    duration_minutes=timetable.duration_minutes,
                    semester_name=timetable.semester.name,
                    school_session=timetable.semester.school_session,
                    schedule_count=len(schedule),
                    schedule=schedule
                )
                parsed_timetables.append(response)

            return parsed_timetables
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching lecturer timetable for {lecturer_id}: {e}")
            raise ServerError()
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while fetching lecturer timetable for {lecturer_id}: {e}"
            )
            raise ServerError()

    async def fetch_lecturer_courses(self, lecturer_id: str)-> List:
        """Fetch all courses assigned to a specific lecturer."""
        try:
            # Get the lecturer and their courses
            lecturer_stmt = await self.db.execute(
                select(User)
                .options(
                    selectinload(User.courses).options(
                        selectinload(Course.level),
                        selectinload(Course.department)
                    )
                )
                .where(User.id == lecturer_id, User.role == Role_Enum.LECTURER)
            )
            lecturer = lecturer_stmt.scalar_one_or_none()
            if not lecturer:
                logger.warning(f"Lecturer with id {lecturer_id} not found.")
                return []

            courses = lecturer.courses
            logger.info(f"Successfully fetched {len(courses)} courses for lecturer {lecturer_id}.")
            return courses
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching lecturer courses for {lecturer_id}: {e}")
            raise ServerError()
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while fetching lecturer courses for {lecturer_id}: {e}"
            )
            raise ServerError()

    def _parse_rrule_to_schedule(self, timetable) -> List[ClassSchedule]:
        """Parse rrule string and generate next class schedule occurrences."""
        try:
            # Parse the rrule
            rule = rrulestr(timetable.rrule)

            # Get current date and semester end date
            today = date.today()
            semester_end = timetable.semester.end_date

            # Generate next 15 occurrences within the semester
            occurrences = []
            for occurrence_dt in rule:
                if len(occurrences) >= 15:  # Limit to next 15 classes
                    break

                occurrence_date = occurrence_dt.date()

                # Skip past dates and dates outside semester
                if occurrence_date < today or occurrence_date > semester_end:
                    continue

                # Calculate end time
                start_datetime = datetime.combine(occurrence_date, timetable.start_time)
                end_datetime = start_datetime + timedelta(minutes=timetable.duration_minutes)
                end_time = end_datetime.time()

                schedule = ClassSchedule(
                    date=occurrence_date,
                    start_time=timetable.start_time,
                    end_time=end_time
                )
                occurrences.append(schedule)

            return occurrences
        except Exception as e:
            logger.error(f"Error parsing rrule {timetable.rrule}: {e}")
            return []
