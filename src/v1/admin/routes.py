import uuid
from fastapi import Depends, APIRouter, status

from src.v1.auth.authorization import RoleCheck
from src.v1.model.user import Role_Enum
from src.v1.schema.user import UserResponse
from .schema import Admin, CreateVenue, CreateTimeTable, CreateSemester, CreateDepartment
from src.v1.controllers.util import get_admin_service, get_current_user
from .service import AdminService
from src.util.response import success_response
from src.v1.schema.courses import CreateCourse
from src.v1.schema.user import CreateUser, CreateStudent
admin_router = APIRouter(prefix="/admin")


#Venue endpoints
@admin_router.post("/venue", tags=["Venues"])
async def create_venue(data: CreateVenue, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    new_venue = await admin_service.create_venue(data)
    return success_response(
        status_code=status.HTTP_201_CREATED,
        data = CreateVenue.model_validate(new_venue).model_dump()
    ) 
    
@admin_router.get("/venue", tags=["Venues"])
async def fetch_all_venue(admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    new_venue = await admin_service.fetch_all_venues()
    return success_response(
        status_code=status.HTTP_200_OK,
        data = [CreateVenue.model_validate(venue).model_dump() for venue in new_venue]
    )
@admin_router.get("/venue/{venue_id}", tags=["Venues"])
async def fetch_one_venue(venue_id: uuid.UUID,
admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    venue = await admin_service.fetch_venue_by_id(venue_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        data = CreateVenue.model_validate(venue).model_dump()
    )

@admin_router.put("/venue/{venue_id}", tags=["Venues"])
async def update_venue(venue_id: uuid.UUID, data: CreateVenue, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    updated_venue = await admin_service.update_venue(venue_id, data)
    return success_response(
        status_code=status.HTTP_200_OK,
        data = CreateVenue.model_validate(updated_venue).model_dump()
    )

@admin_router.delete("/venue/{venue_id}", tags=["Venues"])
async def delete_venue(venue_id: uuid.UUID, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    await admin_service.delete_venue(venue_id)
    return success_response(
        status_code=status.HTTP_204_NO_CONTENT,
        message="Venue deleted successfully"
    )



#semester endpoints
@admin_router.post("/semester", tags=["Semesters"])
async def create_semester(data: CreateSemester, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    new_semester = await admin_service.create_semester(data)
    return success_response(
        status_code=status.HTTP_201_CREATED,
        data = CreateSemester.model_validate(new_semester).model_dump()
    )

@admin_router.get("/semester", tags=["Semesters"])
async def fetch_all_semesters(admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    semesters = await admin_service.fetch_all_semesters()
    return success_response(
        status_code=status.HTTP_200_OK,
        data = [CreateSemester.model_validate(semester).model_dump() for semester in semesters]
    )

@admin_router.get("/semester/{semester_id}", tags=["Semesters"])
async def fetch_one_semester(semester_id: uuid.UUID,
admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    semester = await admin_service.fetch_semester_by_id(semester_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        data = CreateSemester.model_validate(semester).model_dump()
    )

@admin_router.put("/semester/{semester_id}", tags=["Semesters"])
async def update_semester(semester_id: uuid.UUID, data: CreateSemester, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    updated_semester = await admin_service.update_semester(semester_id, data)
    return success_response(
        status_code=status.HTTP_200_OK,
        data = CreateSemester.model_validate(updated_semester).model_dump()
    )

@admin_router.delete("/semester/{semester_id}", tags=["Semesters"])
async def delete_semester(semester_id: uuid.UUID, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    await admin_service.delete_semester(semester_id)
    return success_response(
        status_code=status.HTTP_204_NO_CONTENT,
        message="Semester deleted successfully"
    )

#timetable endpoints
@admin_router.post("/timetable", tags=["Timetables"])
async def create_timetable(data: CreateTimeTable, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    new_timetable = await admin_service.create_timetable(data)
    return success_response(
        status_code=status.HTTP_201_CREATED,
        data = CreateTimeTable.model_validate(new_timetable).model_dump()
    )
    
@admin_router.get("/timetable", tags=["Timetables"])
async def fetch_all_timetables(admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    timetables = await admin_service.fetch_all_timetables()
    return success_response(
        status_code=status.HTTP_200_OK,
        data = [CreateTimeTable.model_validate(timetable, from_attributes=True).model_dump() for timetable in timetables]
    )

@admin_router.get("/timetable/{timetable_id}", tags=["Timetables"])
async def fetch_one_timetable(timetable_id: uuid.UUID,
admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    timetable = await admin_service.fetch_timetable_by_id(timetable_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        data = CreateTimeTable.model_validate(timetable, from_attributes=True).model_dump()
    )

@admin_router.put("/timetable/{timetable_id}", tags=["Timetables"])
async def update_timetable(timetable_id: uuid.UUID, data: CreateTimeTable, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    updated_timetable = await admin_service.update_timetable(timetable_id, data)
    return success_response(
        status_code=status.HTTP_200_OK,
        data = CreateTimeTable.model_validate(updated_timetable, from_attributes=True).model_dump()
    )

@admin_router.delete("/timetable/{timetable_id}", tags=["Timetables"])
async def delete_timetable(timetable_id: uuid.UUID, admin_service:AdminService = Depends(get_admin_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    await admin_service.delete_timetable(timetable_id)
    return success_response(
        status_code=status.HTTP_204_NO_CONTENT,
        message="Timetable deleted successfully"
    )

@admin_router.post("/register", tags=["Admin"])
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
