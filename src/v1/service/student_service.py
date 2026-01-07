from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, date, time
from dateutil.rrule import rrulestr
from typing import List

from src.util.log import setup_logger
from src.v1.base.exception import ServerError
from src.v1.model import Role_Enum, User, TimeTable, Course
from src.v1.schema.timetable import StudentTimeTableResponse, ClassSchedule

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

    async def fetch_student_timetable(self, student_id: str):
        try:
            # First get the student to find their level and department
            student_stmt = await self.db.execute(
                select(User)
                .options(selectinload(User.level), selectinload(User.department))
                .where(User.id == student_id, User.role == Role_Enum.STUDENT)
            )
            student = student_stmt.scalar_one_or_none()
            if not student:
                logger.warning(f"Student with id {student_id} not found.")
                return []

            # Get courses for the student's level and department
            course_stmt = await self.db.execute(
            select(Course).options(
                selectinload(Course.level),
                selectinload(Course.department)
            )
                .where(Course.level_id == student.level_id, Course.department_id == student.department_id)
            )
            courses = course_stmt.scalars().all()
            course_ids = [course.id for course in courses]

            if not course_ids:
                logger.info(f"No courses found for student {student_id}.")
                return []

            # Get timetables for these courses
            timetable_stmt = await self.db.execute(
            select(TimeTable)
                .options(
                    # 1. Load the course and its nested relations
                    selectinload(TimeTable.course).options(
                        selectinload(Course.level),
                        selectinload(Course.department)
                    ),
                    # 2. Load venue and semester (Directly from TimeTable)
                    selectinload(TimeTable.venue),
                    selectinload(TimeTable.semester)
                )
                .where(TimeTable.course_id.in_(course_ids))
            )
            timetables = timetable_stmt.scalars().all()

            logger.info(f"Successfully fetched {len(timetables)} timetable entries for student {student_id}.")

            # Parse timetables and generate schedule
            parsed_timetables = []
            for timetable in timetables:
                schedule = self._parse_rrule_to_schedule(timetable)
                response = StudentTimeTableResponse(
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
            logger.error(f"Database error while fetching student timetable for {student_id}: {e}")
            raise ServerError()
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while fetching student timetable for {student_id}: {e}"
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
