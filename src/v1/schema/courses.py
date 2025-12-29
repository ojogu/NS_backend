from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict
from src.v1.model.user import Role_Enum, Level_Enum
from src.v1.schema.user import DepartmentResponse


class BaseResponse(BaseModel):
    id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class LevelResponse(BaseResponse):
    name: Level_Enum
    
    model_config = ConfigDict(from_attributes=True)

class DeptResponse(BaseResponse):
    name: str
    
    model_config = ConfigDict(from_attributes=True)


class CreateCourse(BaseModel):
    name:str
    code:str
    department_id: uuid.UUID
    level_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)


class CourseResponse(BaseModel):
    id: uuid.UUID
    name:str
    code:str
    department: DeptResponse
    level: LevelResponse
     
    model_config = ConfigDict(from_attributes=True)
    
