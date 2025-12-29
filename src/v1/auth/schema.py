from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import  BaseModel, ConfigDict, EmailStr, field_validator, ValidationError, model_validator
import uuid
class Login(BaseModel):
    email: Optional[EmailStr] = None
    school_id: Optional[str] = None
    password: str
    
    model_config = ConfigDict(from_attributes=True)
    
    #field validator
    @model_validator(mode="after")
    def check_at_least_one(cls, values):
        if not values.email and not values.school_id:
            raise ValueError("Either email or school_id must be provided")
        return values


class Token(BaseModel):
    user: Dict[str, Any]
    exp: datetime
    jti: str 
    refresh: bool
