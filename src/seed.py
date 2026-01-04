import asyncio
from datetime import date
from src.util.db import engine, Base, async_session
from src.v1.model.user import Level, Level_Enum
from src.v1.model.timetable import Department, Semester, Semester_Enum

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

        # Seed Semesters
        semesters = [
            # Semester(
            #     name=Semester_Enum.FIRST_SEMESTER,
            #     school_session="2024/2025",
            #     start_date=date(2024, 9, 1),
            #     end_date=date(2024, 12, 31),
            # ),
            Semester(
                name=Semester_Enum.SECOND_SEMESTER,
                school_session="2025/2026",
                start_date=date(2025, 9, 1),
                end_date=date(2026, 4, 30),
            ),
        ]
        session.add_all(semesters)
        await session.commit()

        print("Levels, Departments, and Semesters seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
