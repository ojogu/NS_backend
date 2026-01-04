import uuid

from sqlalchemy import select, or_
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

    async def create_dept(self, dept_name: str):
        try:
            existing_dept = await self.check_if_dept_exist_by_name(dept_name)
            if existing_dept:
                raise AlreadyExistsError(f"Department '{dept_name}' already exists")

            new_dept = Department(name=dept_name)
            self.db.add(new_dept)
            await self.db.commit()
            await self.db.refresh(new_dept)
            logger.info(f"Department {dept_name} created successfully.")
            return new_dept
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating department {dept_name}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def update_dept(self, dept_id: uuid.UUID, dept_name: str):
        try:
            dept = await self.check_if_dept_exist_by_id(dept_id)
            if not dept:
                raise NotFoundError(f"Department with ID {dept_id} not found")

            existing_dept = await self.check_if_dept_exist_by_name(dept_name)
            if existing_dept and existing_dept.id != dept_id:
                raise AlreadyExistsError(f"Department '{dept_name}' already exists")

            dept.name = dept_name
            await self.db.commit()
            await self.db.refresh(dept)
            logger.info(f"Department {dept_name} updated successfully.")
            return dept
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating department {dept_id}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def delete_dept(self, dept_id: uuid.UUID):
        try:
            dept = await self.check_if_dept_exist_by_id(dept_id)
            if not dept:
                raise NotFoundError(f"Department with ID {dept_id} not found")

            await self.db.delete(dept)
            await self.db.commit()
            logger.info(f"Department {dept.name} deleted successfully.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting department {dept_id}: {e}")
            await self.db.rollback()
            raise ServerError()

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
        self.dept = DeptService(self.db)

    async def check_if_course_exists(self, name:str, code:str):
        try:
            stmt = select(Course).options(
                selectinload(Course.department), selectinload(Course.level)
            ).where(
                or_(
                    Course.code.ilike(code),
                    Course.name.ilike(name)
                )
            )
            existing_course = (await self.db.execute(stmt)).scalar_one_or_none()
            return existing_course
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking course existence: {e}"
            )
            raise ServerError()

    async def check_if_course_exists_by_id(self, course_id: uuid.UUID):
        try:
            stmt = await self.db.execute(
                select(Course)
                .options(selectinload(Course.department), selectinload(Course.level))
                .where(Course.id == course_id)
            )
            course = stmt.scalar_one_or_none()
            if course:
                logger.info(
                    f"Course {course.name} ({course.code}) found with ID {course_id}."
                )
            else:
                logger.info(f"Course with ID {course_id} not found.")
            return course
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking course existence by ID {course_id}: {e}"
            )
            raise ServerError()
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while checking course existence by ID {course_id}: {e}"
            )
            raise ServerError()

    async def create_course(self, course_data: CreateCourse):
        try:
            logger.info(
                f"Attempting to create course with name '{course_data.name}' and code '{course_data.code}' for department {course_data.department_id} and level {course_data.level_id}."
            )
            # ideally, only admin can create course (later update)

            # Check if department exists
            dept_exists = await self.dept.check_if_dept_exist_by_id(course_data.department_id)
            if not dept_exists:
                raise NotFoundError(f"Department with ID {course_data.department_id} not found")

            # Check if level exists
            stmt = await self.db.execute(select(Level).where(Level.id == course_data.level_id))
            level_exists = stmt.scalar_one_or_none()
            if not level_exists:
                raise NotFoundError(f"Level with ID {course_data.level_id} not found")

            existing_course = await self.check_if_course_exists(course_data.name, course_data.code)
            if existing_course:
                logger.warning(
                    f"Course creation failed: Course with name '{course_data.name}' or code '{course_data.code}' already exists."
                )
                raise AlreadyExistsError(
                    f"Course with code '{course_data.code}' or name '{course_data.name}' already exists"
                )

            new_course = Course(
                name=course_data.name,
                code=course_data.code,
                department_id=course_data.department_id,
                level_id=course_data.level_id,
            )
            self.db.add(new_course)
            await self.db.commit()
            await self.db.refresh(new_course)

            logger.info(f"course data: {new_course.to_dict()}")

            logger.info(
                f"Successfully created course '{new_course.name}' with code '{new_course.code}' for department {course_data.department_id} and level {course_data.level_id}."
            )
            #Article on handling relationships during writes. 
            return new_course
            # course_dict = new_course.to_dict()
            # logger.info(f'new course data:{new_course.to_dict()} ')
            # logger.info(f'department data:{new_course.department.to_dict()} ')
            # logger.info(f'level data:{new_course.level.to_dict()} ')
            # if new_course.department:
            #     course_dict['department'] = new_course.department.to_dict()
            # if new_course.level:
            #     course_dict['level'] = new_course.level.to_dict()
            # logger.info(f"course dict: {course_dict}")
            # return course_dict
        
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while creating course with name '{course_data.name}' and code '{course_data.code}': {e}"
            )
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred while creating course with name '{course_data.name}' and code '{course_data.code}': {e}")
        #     raise ServerError()

    async def update_course(self, course_id: uuid.UUID, course_data: CreateCourse):
        try:
            course = await self.check_if_course_exists_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course with ID {course_id} not found")

            # Check if department exists
            dept_exists = await self.dept.check_if_dept_exist_by_id(course_data.department_id)
            if not dept_exists:
                raise NotFoundError(f"Department with ID {course_data.department_id} not found")

            # Check if level exists
            stmt = await self.db.execute(select(Level).where(Level.id == course_data.level_id))
            level_exists = stmt.scalar_one_or_none()
            if not level_exists:
                raise NotFoundError(f"Level with ID {course_data.level_id} not found")

            # Check if another course exists with the same name or code
            existing_course = await self.check_if_course_exists(course_data.name, course_data.code)
            if existing_course and existing_course.id != course_id:
                raise AlreadyExistsError(
                    f"Course with code '{course_data.code}' or name '{course_data.name}' already exists"
                )

            course.name = course_data.name
            course.code = course_data.code
            course.department_id = course_data.department_id
            course.level_id = course_data.level_id

            await self.db.commit()
            await self.db.refresh(course)
            logger.info(f"Course {course.name} updated successfully.")
            return course
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating course {course_id}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def delete_course(self, course_id: uuid.UUID):
        try:
            course = await self.check_if_course_exists_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course with ID {course_id} not found")

            await self.db.delete(course)
            await self.db.commit()
            logger.info(f"Course {course.name} deleted successfully.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting course {course_id}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def fetch_all_courses(self):
        try:
            stmt = await self.db.execute(
                select(Course).options(selectinload(Course.department), selectinload(Course.level))
            )
            courses = stmt.scalars().all()
            logger.info(f"Successfully fetched {len(courses)} courses.")
            return courses
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching all courses: {e}")
            raise ServerError()

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
