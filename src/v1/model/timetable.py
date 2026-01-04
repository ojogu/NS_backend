import uuid
from datetime import date, datetime, time
from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy import Date as SqlDate
from sqlalchemy import Time as SqlTime
from sqlalchemy import DateTime as SQLdatetime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from src.v1.base.model import BaseModel


class Semester_Enum(StrEnum):
    FIRST_SEMESTER = "first_semester"
    SECOND_SEMESTER = "second_semester"


class Department(BaseModel):
    name: Mapped[str] = mapped_column(String, nullable=False)


class Course(BaseModel):
    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id"), nullable=False
    )
    department: Mapped["Department"] = relationship(
        "Department", backref="courses", lazy="joined"
    )
    level_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("levels.id"), nullable=False)
    level: Mapped["Level"] = relationship(  # noqa: F821
        "Level", backref=backref("courses"), lazy="joined"
    )  
    # users: Mapped[List["User"]] = relationship("User", secondary=user_course_association, back_populates="courses")


class Venue(BaseModel):
    name: Mapped[str] = mapped_column(String, nullable=False)


class Semester(BaseModel):
    name: Mapped[Semester_Enum] = mapped_column(
        SqlEnum(Semester_Enum, name="semester_enum"), nullable=False
    )
    school_session: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    start_date: Mapped[date] = mapped_column(SqlDate, nullable=False)
    end_date: Mapped[date] = mapped_column(SqlDate, nullable=False)


class TimeTable(BaseModel):
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id"), nullable=False
    )
    venue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("venues.id"), nullable=False)
    semester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("semesters.id"), nullable=False
    )
    start_time: Mapped[time] = mapped_column(
        SqlTime, nullable=False
    )  # when the class is starting
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # how long the class will last
    rrule: Mapped[str] = mapped_column(String, nullable=False)

    # relationships
    course: Mapped["Course"] = relationship("Course", backref=backref("timetables"), lazy="joined")
    venue: Mapped["Venue"] = relationship("Venue", backref=backref("timetables"), lazy="joined")
    semester: Mapped["Semester"] = relationship(
        "Semester", backref=backref("timetables"), lazy="joined"
    )


class TimeTableException(BaseModel):
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("time_tables.id"), nullable=False
    )
    exception_date: Mapped[datetime] = mapped_column(
        SQLdatetime(timezone=True), nullable=False
    )
    is_cancelled: Mapped[bool] = mapped_column(Boolean)
    is_reschedule: Mapped[bool] = mapped_column(Boolean)
    new_venue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("venues.id"))

    # relationships
    timetable: Mapped["TimeTable"] = relationship(
        "TimeTable", backref=backref("schedule_exception"), lazy="joined"
    )
    venue: Mapped["Venue"] = relationship(
        "Venue", backref=backref("schedule_exception"), lazy="joined"
    )
