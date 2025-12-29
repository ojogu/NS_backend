import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.util.log import setup_logger
from src.v1.base.exception import AlreadyExistsError, NotFoundError, ServerError
from src.v1.model import Course, Department, Level, Role_Enum, User
from src.v1.schema.courses import CreateCourse
from src.v1.schema.user import UserCourse

logger = setup_logger(__name__, "courses_service.log")

# link courses to dept and level, have an endpoint where student/lecturers register courses based on level.
# seed courses for 100l, lecturers register courses to teach, student register courses only based on their level and department


class LevelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_all_level(self):
        try:
            stmt = await self.db.execute(select(Level))
            all_levels = (
                stmt.scalars().all()
            )  # a list of Level objects: [Level(), Level(), ...]
            # Use .all() (without .scalars()) to get a list of tuple rows, where each tuple contains the columns selected. Since you are selecting the entire Level entity, each tuple will contain a single Level object.
            logger.info("Successfully fetched all levels.")
            return all_levels
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching all levels: {e}")
            raise ServerError()
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching all levels: {e}")
            raise ServerError()

    async def check_if_level_exist_by_id(self, level_id: uuid.UUID):
        try:
            stmt = await self.db.execute(select(Level).where(Level.id == level_id))
            level = stmt.scalar_one_or_none()
            if level:
                logger.info(f"Level {level.name} found with ID {level_id}.")
            else:
                logger.info(f"Level with ID {level_id} not found.")
            return level
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking level existence by ID {level_id}: {e}"
            )
            raise ServerError()
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while checking level existence by ID {level_id}: {e}"
            )
            raise ServerError()

    async def fetch_all_courses_for_a_level(self):
        try:
            stmt = await self.db.execute(
                select(Course).options(selectinload(Course.level))
            )
            courses = stmt.scalars().all()
            logger.info(
                f"Successfully fetched {len(courses)} courses with their levels."
            )
            return courses
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching all courses for levels: {e}")
            raise ServerError()
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while fetching all courses for levels: {e}"
            )
            raise ServerError()

    async def check_if_course_exist_for_a_level_by_course_code(
        self, level_id: uuid.UUID, course_code: str
    ):
        try:
            stmt = await self.db.execute(
                select(Course)
                .options(selectinload(Course.level))
                .where(Course.level_id == level_id)
                .where(Course.code.ilike(course_code))
            )
            course = stmt.scalar_one_or_none()
            if course:
                logger.info(
                    f"Course {course.name}, {course.code} found for Level {course.level.name}."
                )
            else:
                logger.info(f"Course {course_code} not found for level {level_id}.")
            return course
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking course existence for level {level_id} by code {course_code}: {e}"
            )
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while checking course existence for level {level_id} by code {course_code}: {e}")
        #     raise ServerError()

    async def check_if_course_exist_for_a_level_by_course_name(
        self, level_id: uuid.UUID, course_name: str
    ):
        try:
            stmt = await self.db.execute(
                select(Course)
                .options(selectinload(Course.level))
                .where(Course.level_id == level_id)
                .where(Course.name.ilike(course_name))
            )
            course = stmt.scalar_one_or_none()
            if course:
                logger.info(
                    f"Course {course.name}, {course.code} found for Level {course.level.name}."
                )
            else:
                logger.info(f"Course {course_name} not found for level {level_id}.")
            return course
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking course existence for level {level_id} by name {course_name}: {e}"
            )
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while checking course existence for level {level_id} by name {course_name}: {e}")
        #     raise ServerError()


class DeptService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_all_courses_for_a_dept(self, dept_id: uuid.UUID):
        stmt = await self.db.execute(
            select(Course)
            .options(selectinload(Course.department), selectinload(Course.level))
            .where(Course.department_id == dept_id)
        )
        course = stmt.scalars().all()
        return course

    async def fetch_all_dept(self):
        stmt = await self.db.execute(select(Department))
        department = stmt.scalars().all()
        return department

    async def create_dept(self):
        pass

    async def check_if_dept_exist_by_name(self, dept_name: str):
        stmt = await self.db.execute(
            select(Department).where(Department.name.ilike(dept_name))
        )
        department = stmt.scalar_one_or_none()
        return department

    async def check_if_dept_exist_by_id(self, dept_id: uuid.UUID):
        stmt = await self.db.execute(select(Department).where(Department.id == dept_id))
        department = stmt.scalar_one_or_none()
        return department

    async def check_if_course_exist_for_a_dept_by_course_code(
        self, dept_id: uuid.UUID, course_code: str
    ):
        try:
            stmt = await self.db.execute(
                select(Course)
                .options(selectinload(Course.department))
                .where(Course.department_id == dept_id)
                .where(Course.code.ilike(course_code))
            )
            course = stmt.scalar_one_or_none()
            if course:
                logger.info(
                    f"Course {course.name}, {course.code} found for Dept {course.department.name}."
                )
            else:
                logger.info(f"Course {course_code} not found for dept {dept_id}.")
            return course
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking course existence for dept {dept_id} by code {course_code}: {e}"
            )
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while checking course existence for dept {dept_id} by code {course_code}: {e}")
        #     raise ServerError()

    async def check_if_course_exist_for_a_dept_by_course_name(
        self, dept_id: uuid.UUID, course_name: str
    ):
        try:
            stmt = await self.db.execute(
                select(Course)
                .options(selectinload(Course.department))
                .where(Course.department_id == dept_id)
                .where(Course.name.ilike(course_name))
            )
            course = stmt.scalar_one_or_none()
            if course:
                logger.info(
                    f"Course {course.name}, {course.code} found for Dept {course.department.name}."
                )
            else:
                logger.info(f"Course {course_name} not found for dept {dept_id}.")
            return course
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking course existence for dept {dept_id} by name {course_name}: {e}"
            )
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while checking course existence for dept {dept_id} by name {course_name}: {e}")
        #     raise ServerError()


class CourseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.level = LevelService(self.db)
        self.dept = DeptService(self.db)

    async def create_course(self, course_data: CreateCourse):
        try:
            logger.info(
                f"Attempting to create course with name '{course_data.name}' and code '{course_data.code}' for department {course_data.department_id} and level {course_data.level_id}."
            )
            # ideally, only admin can create course (later update)

            # check if dept and level exist
            dept = await self.dept.check_if_dept_exist_by_id(course_data.department_id)
            if not dept:
                raise NotFoundError(f"{course_data.department_id} does not exist")

            level = await self.level.check_if_level_exist_by_id(course_data.level_id)
            if not level:
                raise NotFoundError(f"{course_data.level_id} does not exist")

            # check if the course exist in  dept and level
            course_exist_by_code_dept = (
                await self.dept.check_if_course_exist_for_a_dept_by_course_code(
                    course_data.department_id, course_data.code
                )
            )
            course_exist_by_code_level = (
                await self.level.check_if_course_exist_for_a_level_by_course_code(
                    course_data.level_id, course_data.code
                )
            )
            course_exist_by_name_dept = (
                await self.dept.check_if_course_exist_for_a_dept_by_course_name(
                    course_data.department_id, course_data.name
                )
            )
            course_exist_by_name_level = (
                await self.level.check_if_course_exist_for_a_level_by_course_name(
                    course_data.level_id, course_data.name
                )
            )

            course_exist = (
                course_exist_by_code_dept and course_exist_by_code_level
            ) or (course_exist_by_name_dept and course_exist_by_name_level)

            if course_exist:
                logger.warning(
                    f"Course creation failed: Course with name '{course_data.name}' or code '{course_data.code}' already exists for department {course_data.department_id} and level {course_data.level_id}."
                )
                raise AlreadyExistsError(
                    f"{course_exist.name} already exist for {course_exist.department.name}"
                )

            new_course = Course(
                name=course_data.name,
                code=course_data.code,
                department=dept,
                level=level,
            )
            self.db.add(new_course)
            await self.db.commit()
            await self.db.refresh(new_course)
            logger.info(
                f"Successfully created course '{new_course.name}' with code '{new_course.code}' for department {new_course.department.name} and level {new_course.level.name}."
            )
            return new_course
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while creating course with name '{course_data.name}' and code '{course_data.code}': {e}"
            )
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while creating course with name '{course_data.name}' and code '{course_data.code}': {e}")
        #     raise ServerError()

    async def check_course_dept(self, course_id: uuid.UUID):
        try:
            stmt = await self.db.execute(
                select(Course)
                .options(selectinload(Course.department))
                .where(Course.id == course_id)
            )
            course = stmt.scalar_one_or_none()
            if course:
                logger.info(
                    f"Course {course.name} ({course.code}) found with ID {course_id} in department {course.department.name}."
                )
            else:
                logger.info(f"Course with ID {course_id} not found.")
            return course
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking course existence by ID {course_id}: {e}"
            )
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while checking course existence by ID {course_id}: {e}")
        #     raise ServerError()

    async def fetch_all_student_taking_course(self, data: UserCourse):
        try:
            logger.info(f"Fetching course with ID {data.course_id}.")
            # fetch the course, with the lecturer, query to get all student and course sharing the same level
            # lecturer and course should share the same level(join)
            stmt = await self.db.execute(
                select(Course)
                .options(
                    # selectinload(Course.user),
                    selectinload(Course.level),
                    selectinload(Course.department),
                )
                .where(Course.id == data.course_id)
            )
            course = stmt.scalar_one_or_none()
            if not course:
                raise NotFoundError(f"{data.course_id} does not exist")
            logger.info(
                f"Course '{course.name}' found with ID {data.course_id} at level {course.level.name}."
            )
            logger.info(f"Fetching all students for level {course.level.name}.")
            stmt = await self.db.execute(
                select(User)
                .options(selectinload(User.level), selectinload(User.department))
                .where(User.role == Role_Enum.STUDENT, course.level_id == User.level_id)
            )
            students = stmt.scalars().all()
            logger.info(
                f"Successfully fetched {len(students)} students for course {course.name}."
            )
            return students
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while fetching students for course {data.course_id}: {e}",
                exc_info=True,
            )
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while fetching students for course {data.course_id}: {e}")
        #     raise ServerError()

    async def fetch_all_lecturers_taking_course(self, data: UserCourse):
        try:
            logger.info(f"Fetching course with ID {data.course_id}.")
            stmt = await self.db.execute(
                select(Course)
                .options(
                    # selectinload(Course.user),
                    selectinload(Course.level),
                    selectinload(Course.department),
                )
                .where(Course.id == data.course_id)
            )
            course = stmt.scalar_one_or_none()
            if not course:
                raise NotFoundError(f"{data.course_id} does not exist")
            logger.info(
                f"Course '{course.name}' found with ID {data.course_id} for department {course.department.name}."
            )
            logger.info(f"Fetching all lecturer for level {course.level.name}.")
            stmt = await self.db.execute(
                select(User).join(
                    User.courses
                )
                .options(
                selectinload(User.level),
                selectinload(User.department))
                .where(User.role == Role_Enum.LECTURER)
            )
            students = stmt.scalars().all()
            logger.info(
                f"Successfully fetched {len(students)} students for course {course.name}."
            )
            return students
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while fetching students for course {data.course_id}: {e}",
                exc_info=True,
            )
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while fetching students for course {data.course_id}: {e}")
        #     raise ServerError()

    # return dept
    # return courses for a dept
    # return level
