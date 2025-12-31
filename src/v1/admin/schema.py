from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import uuid
from datetime import datetime, date
from typing import List, Optional, Union
from dateutil.rrule import rrule, rrulestr, DAILY, WEEKLY, MONTHLY, YEARLY

from src.v1.model.user import Role_Enum

class Admin(BaseModel):
    email:EmailStr
    password:str
    id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    # role: Role_Enum = Role_Enum.ADMIN.value
    
    model_config = ConfigDict(from_attributes=True)
    
class CreateVenue(BaseModel):
    name:str
    id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)



# Mapping frontend strings to dateutil's integer constants
FREQ_MAP = {
    "daily": DAILY,      # 3
    "weekly": WEEKLY,    # 2
    "monthly": MONTHLY,  # 1
    "yearly": YEARLY     # 0
}

class RecurrenceSchema(BaseModel):
    # --- CORE FIELDS ---
    dt_start: datetime      # The anchor date/time: when the first event happens
    frequency: str          # The unit of repetition: 'daily', 'weekly', etc.
    interval: int = 1       # How often the frequency repeats (e.g., every 2 weeks)
    
    # --- STOP CONDITIONS (Use one or the other) ---
    count: Optional[int] = None      # Stop after exactly N occurrences
    until: Optional[datetime] = None # Stop at this specific date/time
    
    # --- REFINEMENTS ---
    by_weekday: Optional[List[str]] = None  # Specific days (e.g., ["MO", "WE"])
    by_month_day: Optional[List[int]] = None # Day of month (e.g., 15 for the 15th)

    @field_validator('frequency')
    def validate_frequency(cls, v):
        """Ensures the frontend sends a frequency we actually support."""
        if v.lower() not in FREQ_MAP:
            raise ValueError("Frequency must be daily, weekly, monthly, or yearly")
        return v.lower()

    def to_rrule(self):
        """
        Converts the Pydantic data into a live python-dateutil object.
        This is where the 'math' happens.
        """
        # Convert string days (MO, TU) into dateutil weekday objects
        weekday_map = None
        if self.by_weekday:
            from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU
            days_lookup = {
                "MO": MO, "TU": TU, "WE": WE, "TH": TH, 
                "FR": FR, "SA": SA, "SU": SU
            }
            # Maps ["MO", "FR"] -> [MO, FR] objects
            weekday_map = [days_lookup[d.upper()] for d in self.by_weekday]

        return rrule(
            freq=FREQ_MAP[self.frequency], # Set the frequency constant
            dtstart=self.dt_start,          # Set the starting anchor
            interval=self.interval,         # Set the gap between events
            count=self.count,               # Set the limit (if any)
            until=self.until,               # Set the end date (if any)
            byweekday=weekday_map,          # Apply day filters (if any)
            bymonthday=self.by_month_day    # Apply month day filters (if any)
        )

    def to_rrule_string(self) -> str:
        """
        Returns the standard RFC 5545 string. 
        Example: 'FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE'
        """
        return str(self.to_rrule())

class CreateTimeTable(BaseModel):
    course_id: uuid.UUID
    venue_id: uuid.UUID
    start_time: datetime
    duration_minutes: int
    rrule: Union[str, RecurrenceSchema]
    semester_start_date: date
    semester_end_date: date

    @field_validator('rrule', mode='before')
    @classmethod
    def validate_rrule(cls, v):
        if isinstance(v, RecurrenceSchema):
            return v.to_rrule_string()
        elif isinstance(v, str):
            return v
        else:
            raise ValueError("rrule must be str or RecurrenceSchema")

    model_config = ConfigDict(from_attributes=True)
