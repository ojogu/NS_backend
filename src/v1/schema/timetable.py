from datetime import datetime, time, date
from typing import Optional, List
import uuid
from pydantic import BaseModel, ConfigDict

from src.v1.schema.courses import CourseResponse, DeptResponse
from src.v1.model.timetable import Semester_Enum


class VenueResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SemesterResponse(BaseModel):
    id: uuid.UUID
    name: Semester_Enum
    school_session: str
    start_date: date
    end_date: date
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClassSchedule(BaseModel):
    date: date
    start_time: time
    end_time: time

    model_config = ConfigDict(from_attributes=True)


class StudentTimeTableResponse(BaseModel):
    course_code: str
    course_name: str
    venue_name: str
    start_time: time
    duration_minutes: int
    semester_name: Semester_Enum
    school_session: str
    schedule_count: int  # Total number of scheduled classes
    schedule: List[ClassSchedule]  # Next few class occurrences

    model_config = ConfigDict(from_attributes=True)


class LecturerTimeTableResponse(BaseModel):
    course_code: str
    course_name: str
    venue_name: str
    start_time: time
    duration_minutes: int
    semester_name: Semester_Enum
    school_session: str
    schedule_count: int  # Total number of scheduled classes
    schedule: List[ClassSchedule]  # Next few class occurrences

    model_config = ConfigDict(from_attributes=True)
