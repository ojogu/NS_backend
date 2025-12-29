from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator, ValidationError, EmailStr
import uuid
from datetime import datetime
from src.v1.model.user import Role_Enum, Level_Enum

class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)
        
class UserBaseSchema(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    school_id: str
    role: Optional[Role_Enum] = None
    department:str
    
    

class CreateUser(UserBaseSchema):
    password: str
    model_config = ConfigDict(from_attributes=True)


class CreateStudent(UserBaseSchema):
    password: str
    # Override the role field to default/force it to STUDENT for this endpoint
    role: Role_Enum = Field(default=Role_Enum.STUDENT, Literal=True) # Forces it to be STUDENT
    level: Level_Enum
    model_config = ConfigDict(from_attributes=True)
    
    @model_validator(mode='after')
    def validate_student_level(self) -> 'CreateStudent':
        if self.level is None: 
            raise ValueError("Level must be provided for students.")
        return self

class Level(BaseModel):
    id: uuid.UUID
    name: Level_Enum
    
    model_config = ConfigDict(from_attributes=True)
    
class UserResponse(UserBaseSchema):
    department:DepartmentResponse
    id: uuid.UUID
    level: Optional[Level] = None # Make level optional
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


UserResponseList = List[UserResponse]


class UserCourse(BaseModel):
    user_id: Optional[uuid.UUID] = Field(default=None)
    course_id: uuid.UUID