import uuid
from fastapi import Depends, APIRouter, status

from src.v1.auth.authorization import RoleCheck
from src.v1.model.user import Role_Enum
from src.v1.schema.user import UserResponse
from .schema import Admin, CreateVenue, CreateTimeTable
from src.v1.controllers.util import get_admin_service, get_current_user
from .service import AdminService
from src.util.response import success_response
admin_router = APIRouter(prefix="/admin")


@admin_router.post("/venue")
async def create_venue(data: CreateVenue, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    new_venue = await admin_service.create_venue(data)
    return success_response(
        status_code=status.HTTP_201_CREATED,
        data = CreateVenue.model_validate(new_venue).model_dump()
    ) 
    
@admin_router.get("/venue")
async def fetch_all_venue(admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    new_venue = await admin_service.fetch_all_venues()
    return success_response(
        status_code=status.HTTP_201_CREATED,
        data = [CreateVenue.model_validate(venue).model_dump() for venue in new_venue]
    )
@admin_router.get("/venue/{venue_id}")
async def fetch_one_venue(venue_id: uuid.UUID,
admin_service:AdminService = Depends(get_admin_service),                        
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    venue = await admin_service.fetch_venue_by_id(venue_id)
    return success_response(
        status_code=status.HTTP_201_CREATED,
        data = CreateVenue.model_validate(venue).model_dump()
    ) 
    
@admin_router.post("/timetable")
async def create_timetable(data: CreateTimeTable, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    new_timetable = await admin_service.create_timetable(data)
    return success_response(
        status_code=status.HTTP_201_CREATED,
        data = CreateTimeTable.model_validate(new_timetable).model_dump()
    )


@admin_router.post("/register")
async def admin_register(
    user_data: Admin, user_service: AdminService = Depends(get_admin_service)
):
    # user_data.role = Role_Enum.ADMIN.value
    new_user = await user_service.create_admin(user_data)
    validated_data = Admin.model_validate(new_user).model_dump(exclude="password")
    return success_response(
        message="Admin Created Successfully",
        status_code=status.HTTP_201_CREATED,
        data=validated_data,
    )
