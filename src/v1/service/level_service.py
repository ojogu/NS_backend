import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.log import setup_logger
from src.v1.base.exception import AlreadyExistsError, NotFoundError, ServerError
from src.v1.model import Level
from src.v1.model.user import Level_Enum

logger = setup_logger(__name__, "level_service.log")


class LevelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_all_level(self):
        try:
            stmt = await self.db.execute(select(Level))
            all_levels = stmt.scalars().all()
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

    async def check_if_level_exist_by_name(self, level_name: Level_Enum):
        try:
            stmt = await self.db.execute(select(Level).where(Level.name == level_name))
            level = stmt.scalar_one_or_none()
            if level:
                logger.info(f"Level {level_name} found.")
            else:
                logger.info(f"Level {level_name} not found.")
            return level
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while checking level existence by name {level_name}: {e}"
            )
            raise ServerError()
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while checking level existence by name {level_name}: {e}"
            )
            raise ServerError()

    async def create_level(self, level_name: Level_Enum):
        try:
            existing_level = await self.check_if_level_exist_by_name(level_name)
            if existing_level:
                raise AlreadyExistsError(f"Level '{level_name}' already exists")

            new_level = Level(name=level_name)
            self.db.add(new_level)
            await self.db.commit()
            await self.db.refresh(new_level)
            logger.info(f"Level {level_name} created successfully.")
            return new_level
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating level {level_name}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def update_level(self, level_id: uuid.UUID, level_name: Level_Enum):
        try:
            level = await self.check_if_level_exist_by_id(level_id)
            if not level:
                raise NotFoundError(f"Level with ID {level_id} not found")

            existing_level = await self.check_if_level_exist_by_name(level_name)
            if existing_level and existing_level.id != level_id:
                raise AlreadyExistsError(f"Level '{level_name}' already exists")

            level.name = level_name
            await self.db.commit()
            await self.db.refresh(level)
            logger.info(f"Level {level_name} updated successfully.")
            return level
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating level {level_id}: {e}")
            await self.db.rollback()
            raise ServerError()

    async def delete_level(self, level_id: uuid.UUID):
        try:
            level = await self.check_if_level_exist_by_id(level_id)
            if not level:
                raise NotFoundError(f"Level with ID {level_id} not found")

            await self.db.delete(level)
            await self.db.commit()
            logger.info(f"Level {level.name} deleted successfully.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting level {level_id}: {e}")
            await self.db.rollback()
            raise ServerError()
