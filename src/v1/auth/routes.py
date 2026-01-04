from datetime import datetime

from fastapi import APIRouter, Depends, status

from src.util.config import config
from src.util.redis_client import set_cache
from src.util.response import success_response
from src.v1.auth.authorization import RoleCheck
from src.v1.controllers.util import get_current_user, get_user_service
from src.v1.model.user import Role_Enum
from src.v1.schema.user import CreateStudent, CreateUser, UserResponse
from src.v1.service.user import UserService

from .schema import Login
from .service import AccessTokenBearer, RefreshTokenBearer, auth_service

auth_router = APIRouter(prefix="/auth")


@auth_router.post("/lecturer-register", tags=["Authentication"])
async def lecturer_register(
    user_data: CreateUser, user_service: UserService = Depends(get_user_service)
):
    user_data.role = Role_Enum.LECTURER
    new_user = await user_service.create_user(user_data)
    validated_data = UserResponse.model_validate(new_user).model_dump()
    return success_response(
        message="Lecturer Created Successfully",
        status_code=status.HTTP_201_CREATED,
        data=validated_data,
    )
    


@auth_router.post("/student-register", tags=["Authentication"])
async def student_register(
    user_data: CreateStudent, user_service: UserService = Depends(get_user_service)
):
    # user_data.role = Role_Enum.STUDENT
    new_user = await user_service.create_user(user_data)
    validated_data = UserResponse.model_validate(new_user).model_dump()
    return success_response(
        message="Student Created Successfully",
        status_code=status.HTTP_201_CREATED,
        data=validated_data,
    )


@auth_router.post("/login", tags=["Authentication"])
async def login(
    user_data: Login, user_service: UserService = Depends(get_user_service)
):
    # tokens = []
    user = await user_service.authenticate_user(user_data)
    access_token = auth_service.create_access_token(user)

    refresh_token = auth_service.create_access_token(
        user_data=user, expiry=config.refresh_token_expiry, refresh=True
    )
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": config.access_token_expiry,
        "user_data": {"user_id": user["user_id"], "role": user["role"]},
    }

    return success_response(
        message="Tokens Successfully Generated",
        status_code=status.HTTP_200_OK,
        data=data,
    )


@auth_router.get("/refresh-token", tags=["Authentication"])
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    # make sure it's not expired
    expiry_timestamp = token_details["exp"]
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = auth_service.create_access_token(
            user_data=token_details["user"]
        )
        return success_response(
            message="Refresh Token Successfully Generated",
            status_code=status.HTTP_200_OK,
            data=new_access_token,
        )


@auth_router.get("/me", tags=["Authentication"])
async def current_user(
    user=Depends(get_current_user)):
    validated_data = UserResponse.model_validate(user).model_dump()
    return success_response(
        message="User Fetched Successfully",
        status_code=status.HTTP_200_OK,
        data=validated_data,
    )


@auth_router.get("/logout", tags=["Authentication"])
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]
    await set_cache(key=str(jti), data="")
    return success_response(
        message="Logged Out Successfully", status_code=status.HTTP_200_OK, data=None
    )
