import uuid
from datetime import datetime
from src.v1.admin.schema import CreateTimeTable, RecurrenceSchema
from src.v1.model.timetable import Semester_Enum

# Sample test data for CreateTimeTable model

# Generate sample UUIDs for course and venue
course_id_sample = uuid.uuid4()
venue_id_sample = uuid.uuid4()

# Sample start time
start_time_sample = datetime(2023, 9, 1, 9, 0)  # September 1, 2023, 9:00 AM

# Sample duration
duration_minutes_sample = 60  # 1 hour

# Sample RecurrenceSchema for rrule
recurrence_sample = RecurrenceSchema(
    dt_start=datetime(2023, 9, 1, 9, 0),
    frequency="weekly",
    interval=1,
    by_weekday=["MO", "WE"]  # Monday and Wednesday
)

# Sample semester session and name
semester_session_sample = "2023/2024"
semester_name_sample = Semester_Enum.FIRST_SEMESTER

# Create instance with RecurrenceSchema
timetable_with_recurrence = CreateTimeTable(
    course_id=course_id_sample,
    venue_id=venue_id_sample,
    start_time=start_time_sample,
    duration_minutes=duration_minutes_sample,
    rrule=recurrence_sample,
    semester_session=semester_session_sample,
    semester_name=semester_name_sample
)

# Sample rrule as string
rrule_string_sample = "FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,WE"

# Create instance with string rrule
timetable_with_string = CreateTimeTable(
    course_id=uuid.uuid4(),
    venue_id=uuid.uuid4(),
    start_time=datetime(2023, 9, 2, 10, 0),  # September 2, 2023, 10:00 AM
    duration_minutes=90,  # 1.5 hours
    rrule=rrule_string_sample,
    semester_session="2023/2024",
    semester_name=Semester_Enum.SECOND_SEMESTER
)

# Print the model dumps for verification
print("Timetable with RecurrenceSchema:")
print(timetable_with_recurrence.model_dump())
print("\nTimetable with string rrule:")
print(timetable_with_string.model_dump())

# Additional sample data as dictionaries for testing
sample_data_dicts = [
    {
        "course_id": str(uuid.uuid4()),
        "venue_id": str(uuid.uuid4()),
        "start_time": "2023-09-01T09:00:00",
        "duration_minutes": 60,
        "rrule": {
            "dt_start": "2023-09-01T09:00:00",
            "frequency": "weekly",
            "interval": 1,
            "by_weekday": ["MO", "WE"]
        },
        "semester_session": "2023/2024",
        "semester_name": "first_semester"
    },
    {
        "course_id": str(uuid.uuid4()),
        "venue_id": str(uuid.uuid4()),
        "start_time": "2023-09-02T10:00:00",
        "duration_minutes": 90,
        "rrule": "FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,TH",
        "semester_session": "2023/2024",
        "semester_name": "second_semester"
    }
]

print("\nSample data as dictionaries:")
for i, data in enumerate(sample_data_dicts, 1):
    print(f"Sample {i}: {data}")
