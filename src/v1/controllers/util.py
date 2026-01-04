#shared servicde Dependency

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.util.db import get_session
from src.v1.auth.service import AccessTokenBearer
from src.v1.service.courses import CourseService, DeptService
from src.v1.service.level_service import LevelService
from src.v1.service.user import UserService
from src.v1.admin.service import AdminService

async def get_course_service(db: AsyncSession = Depends(get_session)):
    return CourseService(db=db)

async def get_level_service(db: AsyncSession = Depends(get_session)):
    return LevelService(db=db)

async def get_admin_service(db: AsyncSession = Depends(get_session)):
    return AdminService(db=db)

async def get_dept_service(db: AsyncSession = Depends(get_session)):
    return DeptService(db=db)

async def get_user_service(db: AsyncSession = Depends(get_session)):
    return UserService(db=db)

def get_access_token():
    access_token_bearer = AccessTokenBearer()
    return access_token_bearer

async def get_current_user(user_details:dict = Depends(AccessTokenBearer()),
user_service: UserService = Depends(get_user_service)
):
    user_id = user_details["user"]["user_id"]
    user = await user_service.check_if_user_exist_by_id(user_id)
    return user
