from fastapi import APIRouter, Depends, status
from pydantic import EmailStr

from src.util.log import setup_logger
from src.util.response import success_response
from src.v1.auth.service import AccessTokenBearer
from src.v1.schema.user import UserCourse, UserResponse, CreateUser, CreateStudent
from src.v1.service.user import UserService
from src.v1.auth.authorization import RoleCheck
from src.v1.model.user import Role_Enum

from .util import get_user_service, get_current_user

logger = setup_logger(__name__, "user_route.log")

# def get_user_service(db: AsyncSession = Depends(get_session)):
#     return UserService(db=db)

user_router = APIRouter()

# /path_param route MUST come BEFORE /query/{param}


@user_router.get("/lecturers", tags=["Lecturers"])
async def fetch_all_lecturers(user_service: UserService = Depends(get_user_service)):
    users = await user_service.fetch_all_lecturers()
    user_list = []
    for user in users:
        # logger.info(f"loop: {level}")
        user_value = UserResponse.model_validate(user).model_dump(exclude="password")
        # logger.info(level_value)
        user_list.append(user_value)
    return success_response(status_code=status.HTTP_200_OK, data=user_list)


@user_router.get("/students", tags=["Students"])
async def fetch_all_students(user_service: UserService = Depends(get_user_service)):
    users = await user_service.fetch_all_students()
    user_list = []
    for user in users:
        # logger.info(f"loop: {level}")
        user_value = UserResponse.model_validate(user).model_dump(exclude="password")
        # logger.info(level_value)
        user_list.append(user_value)
    return success_response(status_code=status.HTTP_200_OK, data=user_list)


@user_router.get("/lecturers/{email}", tags=["Lecturers"])
async def fetch_lecturer_by_email(
    email: EmailStr, user_service: UserService = Depends(get_user_service)
):
    user = await user_service.check_if_user_exist_by_email(email)
    validated_data = UserResponse.model_validate(user).model_dump(exclude="password")
    return success_response(status_code=status.HTTP_201_CREATED, data=validated_data)


@user_router.get("/lecturers/{school_id}", tags=["Lecturers"])
async def fetch_lecturer_by_school_id(
    school_id: str, user_service: UserService = Depends(get_user_service)
):
    user = await user_service.check_if_user_exist_by_school_id(school_id)
    validated_data = UserResponse.model_validate(user).model_dump(exclude="password")
    return success_response(status_code=status.HTTP_200_OK, data=validated_data)


@user_router.get("/students/{email}", tags=["Students"])
async def fetch_student_by_email(
    email: EmailStr, user_service: UserService = Depends(get_user_service)
):
    user = await user_service.check_if_user_exist_by_email(email)
    validated_data = UserResponse.model_validate(user).model_dump(exclude="password")
    return success_response(status_code=status.HTTP_200_OK, data=validated_data)


@user_router.get("/students/{school_id}", tags=["Students"])
async def fetch_student_by_school_id(
    school_id: str, user_service: UserService = Depends(get_user_service)
):
    user = await user_service.check_if_user_exist_by_school_id(school_id)
    validated_data = UserResponse.model_validate(user).model_dump(exclude="password")
    return success_response(status_code=status.HTTP_200_OK, data=validated_data)


@user_router.post("/lecturers/courses", tags=["Lecturers"])
async def link_lecturers_to_courses(
    user_data: UserCourse,
    user_service: UserService = Depends(get_user_service),
    token_details: dict = Depends(AccessTokenBearer()),
):
    user_id = token_details["user"]["user_id"]
    validated_data = UserCourse.model_validate(
        {"user_id": user_id, "course_id": user_data.course_id}
    )
    logger.info(f"data: {validated_data.user_id}, {validated_data.course_id}")
    link = await user_service.link_lecturer_to_course(validated_data)
    if link:
        return {"successful"}

# CRUD for users
@user_router.post("/user", tags=["Users"])
async def create_user(data: CreateUser | CreateStudent,
user_service: UserService = Depends(get_user_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    new_user = await user_service.create_user(data)
    user_value = UserResponse.model_validate(new_user).model_dump(exclude="password")
    return success_response(status_code=status.HTTP_201_CREATED, data=user_value)

@user_router.get("/user", tags=["Users"])
async def fetch_all_users(user_service: UserService = Depends(get_user_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    users = await user_service.fetch_all_users()
    user_list = []
    for u in users:
        user_value = UserResponse.model_validate(u).model_dump(exclude="password")
        user_list.append(user_value)
    return success_response(status_code=status.HTTP_200_OK, data=user_list)

@user_router.get("/user/{user_id}", tags=["Users"])
async def fetch_one_user(user_id: str,
user_service: UserService = Depends(get_user_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    u = await user_service.check_if_user_exist_by_id(user_id)
    user_value = UserResponse.model_validate(u).model_dump(exclude="password")
    return success_response(status_code=status.HTTP_200_OK, data=user_value)

@user_router.put("/user/{user_id}", tags=["Users"])
async def update_user(user_id: str, data: CreateUser | CreateStudent,
user_service: UserService = Depends(get_user_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    updated_user = await user_service.update_user(user_id, data)
    user_value = UserResponse.model_validate(updated_user).model_dump(exclude="password")
    return success_response(status_code=status.HTTP_200_OK, data=user_value)

@user_router.delete("/user/{user_id}", tags=["Users"])
async def delete_user(user_id: str,
user_service: UserService = Depends(get_user_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    await user_service.delete_user(user_id)
    return success_response(
        status_code=status.HTTP_204_NO_CONTENT,
        message="User deleted successfully"
    )
