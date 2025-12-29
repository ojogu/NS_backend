import asyncio
from src.util.db import engine, Base, async_session
from src.v1.model.user import Level, Level_Enum
from v1.model.timetable import Department

async def seed_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Seed Levels
        levels = [
            Level(name=Level_Enum.LEVEL_100),
            Level(name=Level_Enum.LEVEL_200),
            Level(name=Level_Enum.LEVEL_300),
            Level(name=Level_Enum.LEVEL_400),
            Level(name=Level_Enum.LEVEL_500),
        ]
        session.add_all(levels)
        await session.commit()

        # Seed Departments
        departments = [
            Department(name="Computer Science"),
            Department(name="Electrical Engineering"),
            Department(name="Civil Engineering"),
            Department(name="Mechanical Engineering"),
        ]
        session.add_all(departments)
        await session.commit()

        print("Levels and Departments seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
