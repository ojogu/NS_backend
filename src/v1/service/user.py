import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.util.log import setup_logger
from src.v1.auth.schema import Login
from src.v1.auth.service import verify_password
from src.v1.base.exception import (
    AlreadyExistsError,
    AuthorizationError,
    InvalidEmailPassword,
    NotFoundError,
    ServerError,
)
from src.v1.model import Department, Level, Role_Enum, User
from src.v1.schema.user import CreateStudent, CreateUser
from src.v1.service.courses import CourseService
from src.v1.service.lecturer_service import LecturerService
from src.v1.service.student_service import StudentService
from src.v1.auth.service import password_hash

logger = setup_logger(__name__, "user_service.log")


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.course = CourseService(self.db)
        self.lecturer = LecturerService(self.db, self.course, self)
        self.student = StudentService(self.db)

    async def create_user(self, user_data: CreateUser | CreateStudent ):
        try:
            # user_data = CreateUser(user_data)
            logger.info(
                f"Attempting to create user with email: {user_data.email} and school_id: {user_data.school_id}"
            )
            user = await self.check_if_user_exist_by_email(
                user_data.email
            ) or await self.check_if_user_exist_by_school_id(user_data.school_id)

            if user:
                logger.warning(f"User with ID {user.id} already exists.")
                raise AlreadyExistsError(f"User with ID {user.id} already exist")

            password = password_hash(user_data.password)
            user_data.password = password

            # seed department, fetch the department, link users to dept both lecturer and student(link level too)
            #
            stmt = await self.db.execute(
                select(Department).where(Department.name.ilike(user_data.department))
            )
            dept = stmt.scalar_one_or_none()
            if not dept:
                raise NotFoundError(f"{user_data.department} not found")

            # link student to level
            level = None
            if user_data.role == Role_Enum.STUDENT and user_data.level is not None:
                # seed the level in the db, query the level table based on student level, link to users
                stmt = await self.db.execute(
                    select(Level).where(Level.name == user_data.level)
                )
                level = stmt.scalar_one_or_none()
                if not level:
                    raise NotFoundError(f"{user_data.level} not found")

            new_user = User(
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                password=user_data.password,
                school_id=user_data.school_id,
                role=user_data.role,
                level=level,
                department=dept,
            )

            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            logger.info(f"User {new_user.id} created successfully.")
            return new_user
        except SQLAlchemyError as e:
            logger.error(f"Error creating user: {e}")
            await self.db.rollback()
            raise ServerError()

    async def authenticate_user(self, user_data: Login):
        try:
            logger.info(
                f"Attempting to authenticate user with email={user_data.email} or school_id={user_data.school_id}"
            )

            user = None

            # Try email first if provided
            if user_data.email:
                user = await self.check_if_user_exist_by_email(user_data.email)
                # logger.debug(f"user found: {user.email}")

            # If not found yet, try school_id
            if not user and user_data.school_id:
                logger.debug("user not found with email, using school id")
                user = await self.check_if_user_exist_by_school_id(user_data.school_id)
                # logger.debug(f"user found with school id: {user.school_id}")

            # Handle not found
            if not user:
                identifier = user_data.email or user_data.school_id
                logger.warning(
                    f"Authentication failed: User with identifier '{identifier}' does not exist."
                )
                raise NotFoundError(
                    f"User with identifier '{identifier}' does not exist."
                )

            # verify password
            if not verify_password(user_data.password, user.password):
                logger.warning(
                    f"Authentication failed: Invalid password for user {user.id}."
                )
                raise InvalidEmailPassword()

            # do further authentication

            # prepare jwt payload
            jwt_payload = {"user_id": str(user.id), "role": user.role.value}
            logger.info(f"Authentication successful for user {user.id}.")
            return jwt_payload
        except SQLAlchemyError as e:
            logger.error(f"Database error during authentication: {e}")
            raise ServerError()
        # except Exception as e:
        #     logger.error(f"An unexpected error occurred during authentication: {e}")
        #     raise ServerError()

    async def check_if_user_exist_by_email(self, email: str):
        try:
            logger.debug(f"Checking if user exists with email: {email}")
            stmt = await self.db.execute(
                select(User)
                .options(selectinload(User.department))
                .where(User.email.ilike(email))
            )
            user = stmt.scalar_one_or_none()
            if user:
                logger.debug(f"User with email {email} found.")
            else:
                logger.debug(f"User with email {email} not found.")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error checking if user exists by email {email}: {e}")
            raise ServerError()

    async def check_if_user_exist_by_id(self, id: uuid.UUID):
        try:
            logger.debug(f"Checking if user exists with id: {id}")
            stmt = await self.db.execute(
                select(User)
                .options(
                    selectinload(User.courses),
                    selectinload(User.department),
                    selectinload(User.level),
                    # selectinload(User.level),
                )
                .where(User.id == id)
            )
            user = stmt.scalar_one_or_none()
            if user:
                logger.debug(f"User with id {id} found.")
            else:
                logger.debug(f"User with id {id} not found.")
            return user
        except SQLAlchemyError as e:
            logger.error(
                f"Error checking if user exists by id {id}: {e}", exc_info=True
            )
            raise ServerError()

    async def check_if_user_exist_by_school_id(self, school_id: str):
        try:
            logger.debug(f"Checking if user exists with school ID: {school_id}")
            stmt = await self.db.execute(
                select(User).where(User.school_id.ilike(school_id))
            )
            user = stmt.scalar_one_or_none()
            if user:
                logger.debug(f"User with school ID {school_id} found.")
            else:
                logger.debug(f"User with school ID {school_id} not found.")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error checking if user exists by school ID {school_id}: {e}")
            raise ServerError()

    async def fetch_all_lecturers(self):
        return await self.lecturer.fetch_all_lecturers()

    async def fetch_all_students(self):
        return await self.student.fetch_all_students()

    async def link_lecturer_to_course(self, user_data):
        return await self.lecturer.link_lecturer_to_course(user_data)

    async def update_user(self, user_id: uuid.UUID, user_data: CreateUser | CreateStudent):
        try:
            user = await self.check_if_user_exist_by_id(user_id)
            if not user:
                raise NotFoundError(f"User with ID {user_id} not found")

            # Check for email/school_id conflicts
            existing_email = await self.check_if_user_exist_by_email(user_data.email)
            if existing_email and existing_email.id != user_id:
                raise AlreadyExistsError(f"Email {user_data.email} already exists")

            existing_school_id = await self.check_if_user_exist_by_school_id(user_data.school_id)
            if existing_school_id and existing_school_id.id != user_id:
                raise AlreadyExistsError(f"School ID {user_data.school_id} already exists")

            # Update fields
            user.email = user_data.email
            user.first_name = user_data.first_name
            user.last_name = user_data.last_name
            user.school_id = user_data.school_id
            user.role = user_data.role

            # Update department
            stmt = await self.db.execute(
                select(Department).where(Department.name.ilike(user_data.department))
            )
            dept = stmt.scalar_one_or_none()
            if not dept:
                raise NotFoundError(f"Department {user_data.department} not found")
            user.department = dept

            # Update level if student
            if user_data.role == Role_Enum.STUDENT and hasattr(user_data, 'level') and user_data.level:
                stmt = await self.db.execute(
                    select(Level).where(Level.name == user_data.level)
                )
                level = stmt.scalar_one_or_none()
                if not level:
                    raise NotFoundError(f"Level {user_data.level} not found")
                user.level = level

            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"User {user_id} updated successfully.")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating user {user_id}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def delete_user(self, user_id: uuid.UUID):
        try:
            user = await self.check_if_user_exist_by_id(user_id)
            if not user:
                raise NotFoundError(f"User with ID {user_id} not found")

            await self.db.delete(user)
            await self.db.commit()
            logger.info(f"User {user_id} deleted successfully.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting user {user_id}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def fetch_all_users(self):
        try:
            stmt = await self.db.execute(
                select(User).options(
                    selectinload(User.department),
                    selectinload(User.level),
                    selectinload(User.courses)
                )
            )
            users = stmt.scalars().all()
            logger.info(f"Successfully fetched {len(users)} users.")
            return users
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching all users: {e}")
            raise ServerError()
