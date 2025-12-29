import uuid
from src.v1.base.model import BaseModel
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON, Boolean, DateTime as SQLdatetime, ForeignKey, String,  Enum as SqlEnum, Integer, Date as SqlDate
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

# from .user import user_course_association


class Department(BaseModel):
    name:Mapped[str] = mapped_column(String, nullable=False) 
     


class Course(BaseModel):
    name:Mapped[str] = mapped_column(String, nullable=False)
    code:Mapped[str] = mapped_column(String, nullable=False, unique=True)
    department_id:Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id"), nullable=False)
    department:Mapped["Department"] = relationship("Department", backref="courses")
    level_id:Mapped[uuid.UUID] = mapped_column(ForeignKey("levels.id"), nullable=False)
    level:Mapped["Level"] = relationship("Level", backref=backref("courses")) # type: ignore  # noqa: F821
    # users: Mapped[List["User"]] = relationship("User", secondary=user_course_association, back_populates="courses")


class Venue(BaseModel):
    name:Mapped[str] = mapped_column(String, nullable=False)
    

class Schedule(BaseModel):
    course_id:Mapped[uuid.UUID]  = mapped_column(ForeignKey("courses.id"), nullable=False)
    venue_id:Mapped[uuid.UUID]  = mapped_column(ForeignKey("venues.id"), nullable=False)
    start_time:Mapped[datetime] = mapped_column(SQLdatetime(timezone=True), nullable=False) #when the class is starting
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False) #how long the class will last
    rrule:Mapped[str] = mapped_column(String, nullable=False)
    semester_start_date: Mapped[date] = mapped_column(SqlDate)
    semester_end_date: Mapped[date] = mapped_column(SqlDate)
    
    #relationships
    course: Mapped["Course"] = relationship("Course", backref=backref("schedules"))
    venue: Mapped["Venue"] = relationship("Venue", backref=backref("schedules"))

class ScheduleException(BaseModel):
    schedule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schedules.id"), nullable=False)
    exception_date: Mapped[datetime] = mapped_column(SQLdatetime(timezone=True), nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean)
    is_reschedule: Mapped[bool] = mapped_column(Boolean)
    new_venue_id = Mapped[uuid.UUID] = mapped_column(ForeignKey("venue.id"))
    
    #relationships
    schedule: Mapped["Schedule"] = relationship("Schedule", backref=backref("schedule_exception"))
    venue: Mapped["Venue"] = relationship("Venue", backref=backref("schedule_exception"))
    