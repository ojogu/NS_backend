from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime, date

class CreateVenue(BaseModel):
    name:str
    venue_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class CreateTimeTable(BaseModel):
    course_id: uuid.UUID
    venue_id: uuid.UUID
    start_time: datetime
    duration_minutes: int
    rrule: str
    semester_start_date: date
    semester_end_date: date

    model_config = ConfigDict(from_attributes=True)
