from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.util.log import setup_logger
from src.v1.base.exception import AuthorizationError, NotFoundError, ServerError
from src.v1.model import Role_Enum, User, TimeTable, Course
from src.v1.schema.user import UserCourse
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
                    selectinload(TimeTable.course).selectinload(Course.level).selectinload(Course.department),
                    selectinload(TimeTable.venue),
                    selectinload(TimeTable.semester)
                )
                .where(TimeTable.course_id.in_(course_ids))
            )
            timetables = timetable_stmt.scalars().all()

            logger.info(f"Successfully fetched {len(timetables)} timetable entries for lecturer {lecturer_id}.")
            return timetables
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching lecturer timetable for {lecturer_id}: {e}")
            raise ServerError()
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while fetching lecturer timetable for {lecturer_id}: {e}"
            )
            raise ServerError()
