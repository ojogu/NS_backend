import uuid
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.log import setup_logger
from src.v1.base.exception import (
    AlreadyExistsError,
    NotFoundError,
    ServerError,
)
from src.v1.model import Venue

from src.v1.admin.schema import CreateVenue

logger = setup_logger(__name__, "venue_service.log")


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