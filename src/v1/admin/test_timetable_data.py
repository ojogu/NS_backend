import uuid
from datetime import datetime, date
from src.v1.admin.schema import CreateTimeTable, RecurrenceSchema

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

# Sample semester dates
semester_start_date_sample = date(2023, 9, 1)
semester_end_date_sample = date(2023, 12, 31)

# Create instance with RecurrenceSchema
timetable_with_recurrence = CreateTimeTable(
    course_id=course_id_sample,
    venue_id=venue_id_sample,
    start_time=start_time_sample,
    duration_minutes=duration_minutes_sample,
    rrule=recurrence_sample,
    semester_start_date=semester_start_date_sample,
    semester_end_date=semester_end_date_sample
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
    semester_start_date=date(2023, 9, 1),
    semester_end_date=date(2023, 12, 31)
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
        "semester_start_date": "2023-09-01",
        "semester_end_date": "2023-12-31"
    },
    {
        "course_id": str(uuid.uuid4()),
        "venue_id": str(uuid.uuid4()),
        "start_time": "2023-09-02T10:00:00",
        "duration_minutes": 90,
        "rrule": "FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,TH",
        "semester_start_date": "2023-09-01",
        "semester_end_date": "2023-12-31"
    }
]

print("\nSample data as dictionaries:")
for i, data in enumerate(sample_data_dicts, 1):
    print(f"Sample {i}: {data}")
