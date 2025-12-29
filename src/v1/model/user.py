from typing import Optional
import uuid
from src.v1.base.model import BaseModel
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String,  Enum as SqlEnum, Integer, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from sqlalchemy.dialects.postgresql import UUID
from enum import StrEnum, IntEnum
# from .courses import Department


# Association table for many-to-many relationship between User and Course
user_course_association = Table('user_course', BaseModel.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('course_id', UUID(as_uuid=True), ForeignKey('courses.id'), primary_key=True),
    Column('registered_at', DateTime(timezone=True), default=datetime.now(timezone.utc))
)


class Role_Enum(StrEnum):
    STUDENT = "student"
    LECTURER = "lecturer"
    
class Level_Enum(IntEnum):
    LEVEL_100 = 100
    LEVEL_200 = 200
    LEVEL_300 = 300
    LEVEL_400 = 400
    LEVEL_500 = 500


class User(BaseModel):
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False) 
    password: Mapped[str] = mapped_column(String, nullable=False) 
    school_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True) 
    # is_verified: Mapped[bool] = mapped_column(Boolean, default=False) #email verification, set to true
    role: Mapped[Role_Enum] = mapped_column(
        SqlEnum(Role_Enum, name="role_enum"),  nullable=False)
    
    level_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("levels.id"), nullable=True)
    level: Mapped[Optional["Level"]] = relationship("Level", uselist=False, backref=backref("user"))
    
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    department: Mapped[Optional["Department"]] = relationship("Department", uselist=False, backref=backref("user")) # type: ignore  # noqa: F821
    
    courses: Mapped[List["Course"]] = relationship("Course", secondary=user_course_association, backref=backref("user")) #   # noqa: F821
    
    
    # @property
    # def level(self):
    #     # Access the 'name' attribute from the related Level object
    #     if self.level_rel:
    #         return self.level_rel.name
    #     return None
    
    # @level.setter
    # def level(self, value):
    #     # You can ignore the assignment if this property is purely computed:
    #     pass

class Level(BaseModel):
    name: Mapped[Level_Enum] = mapped_column(
        SqlEnum(Level_Enum, name="level_enum"),  nullable=False)
