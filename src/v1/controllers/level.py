import uuid

from fastapi import APIRouter, Depends, status

from src.util.log import setup_logger
from src.util.response import success_response
from src.v1.schema.courses import CreateLevel, LevelResponse
from src.v1.service.level_service import LevelService
from src.v1.auth.authorization import RoleCheck
from src.v1.model.user import Role_Enum

from .util import get_level_service, get_current_user

logger = setup_logger(__name__, "level_route.log")

level_router = APIRouter()


@level_router.get("/levels", tags=["Levels"])
async def fetch_all_levels(level_service: LevelService = Depends(get_level_service)):
    levels = await level_service.fetch_all_level()
    lev = []
    for level in levels:
        level_value = LevelResponse.model_validate(level).model_dump()
        lev.append(level_value)
    return success_response(status_code=status.HTTP_200_OK, data=lev)


@level_router.post("/levels", tags=["Levels"])
async def create_level(
    data: CreateLevel,
    level_service: LevelService = Depends(get_level_service),
    user=Depends(get_current_user),
    role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    new_level = await level_service.create_level(data.name)
    level_value = LevelResponse.model_validate(new_level).model_dump()
    return success_response(status_code=status.HTTP_201_CREATED, data=level_value)


@level_router.get("/levels/{level_id}", tags=["Levels"])
async def fetch_one_level(
    level_id: uuid.UUID,
    level_service: LevelService = Depends(get_level_service),
    user=Depends(get_current_user),
    role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER, Role_Enum.STUDENT]))
):
    level = await level_service.check_if_level_exist_by_id(level_id)
    level_value = LevelResponse.model_validate(level).model_dump()
    return success_response(status_code=status.HTTP_200_OK, data=level_value)


@level_router.put("/levels/{level_id}", tags=["Levels"])
async def update_level(
    level_id: uuid.UUID,
    data: CreateLevel,
    level_service: LevelService = Depends(get_level_service),
    user=Depends(get_current_user),
    role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    updated_level = await level_service.update_level(level_id, data.name)
    level_value = LevelResponse.model_validate(updated_level).model_dump()
    return success_response(status_code=status.HTTP_200_OK, data=level_value)


@level_router.delete("/levels/{level_id}", tags=["Levels"])
async def delete_level(
    level_id: uuid.UUID,
    level_service: LevelService = Depends(get_level_service),
    user=Depends(get_current_user),
    role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    await level_service.delete_level(level_id)
    return success_response(
        status_code=status.HTTP_204_NO_CONTENT,
        message="Level deleted successfully"
    )
