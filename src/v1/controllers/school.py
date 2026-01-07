import uuid

from fastapi import APIRouter, Depends, Query, status

from src.util.log import setup_logger
from src.util.response import success_response
from src.v1.auth.service import AccessTokenBearer
from src.v1.schema.courses import (
    CourseResponse,
    CreateCourse,
    DeptResponse,
    LevelResponse,
)
from src.v1.schema.user import UserCourse, UserResponse
from src.v1.service.courses import CourseService, DeptService
from src.v1.service.level_service import LevelService
from src.v1.auth.authorization import RoleCheck
from src.v1.model.user import Role_Enum

from .util import get_course_service, get_current_user, get_dept_service, get_level_service, get_admin_service

logger = setup_logger(__name__, "courses_route.log")


courses_router = APIRouter()


@courses_router.get("/levels")
async def fetch_levels(level_service: LevelService = Depends(get_level_service)):
    levels = await level_service.fetch_all_level()
    # logger.info(levels)
    lev = []
    for level in levels:
        # logger.info(f"loop: {level}")
        level_value = LevelResponse.model_validate(level).model_dump()
        # logger.info(level_value)
        lev.append(level_value)
    return success_response(status_code=status.HTTP_200_OK, data=lev)


@courses_router.get("/departments")
async def fetch_all_department(dept_service: DeptService = Depends(get_dept_service)):
    departments = await dept_service.fetch_all_dept()
    dept = []

    for department in departments:
        dept_value = DeptResponse.model_validate(department).model_dump()
        dept.append(dept_value)

    return success_response(status_code=status.HTTP_200_OK, data=dept)


@courses_router.get("/departments/courses")
async def fetch_all_course_in_a_department(
    dept_id: uuid.UUID = Query(...),
    dept_service: DeptService = Depends(get_dept_service),
):
    dept = []
    departments = await dept_service.fetch_all_courses_for_a_dept(dept_id)
    if not departments:
        dept = []

    for department in departments:
        # return department.to_dict()
        dept_value = CourseResponse.model_validate(department).model_dump(
            exclude={
                "level": {"created_at", "updated_at"},
                "department": {"created_at", "updated_at"},
            }
        )
        dept.append(dept_value)

    return success_response(status_code=status.HTTP_200_OK, data=dept)


@courses_router.post("/course")
async def create_course(
    course_data: CreateCourse,
    course_service: CourseService = Depends(get_course_service),
    user=Depends(get_current_user),
    role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
    
):
    new_course = await course_service.create_course(course_data)
    # return new_course.to_dict()
    course = CourseResponse.model_validate(new_course).model_dump(
        exclude={
            "level": {"created_at", "updated_at"},
            "department": {"created_at", "updated_at"},
        }
    )
    return success_response(status_code=status.HTTP_201_CREATED, data=course)


@courses_router.get("/course/student/{course_id}")
async def fetch_all_student_taking_course(
    # request: Request,
    course_id: uuid.UUID,
    course_service: CourseService = Depends(get_course_service),
    user=Depends(get_current_user),
):
    validated_data = UserCourse.model_validate(
        {"user_id": user.id, "course_id": course_id}
    )
    logger.debug(f"request body: {validated_data.course_id}, {validated_data.user_id}")
    students = await course_service.fetch_all_student_taking_course(validated_data)
    user_list = []
    for student in students:
        # logger.info(f"loop: {level}")
        user_value = UserResponse.model_validate(student).model_dump(exclude="password")
        # logger.info(level_value)
        user_list.append(user_value)
    return success_response(status_code=status.HTTP_200_OK, data=user_list)


@courses_router.get("/course/lecturers/{course_id}")
async def fetch_all_lecturers_taking_course(
    course_id: uuid.UUID,
    course_service: CourseService = Depends(get_course_service),
    user=Depends(get_current_user),
):
    logger.debug(f"Fetching lecturers for course: {course_id}")
    lecturers = await course_service.fetch_all_lecturers_taking_course(course_id)
    user_list = []
    for lecturer in lecturers:
        user_value = UserResponse.model_validate(lecturer).model_dump(exclude="password")
        user_list.append(user_value)
    return success_response(status_code=status.HTTP_200_OK, data=user_list)


# CRUD for courses
@courses_router.get("/course", tags=["Courses"])
async def fetch_all_courses(course_service: CourseService = Depends(get_course_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    courses = await course_service.fetch_all_courses()
    course_list = []
    for course in courses:
        course_value = CourseResponse.model_validate(course).model_dump(
            exclude={
                "level": {"created_at", "updated_at"},
                "department": {"created_at", "updated_at"},
            }
        )
        course_list.append(course_value)
    return success_response(status_code=status.HTTP_200_OK, data=course_list)

@courses_router.get("/course/{course_id}", tags=["Courses"])
async def fetch_one_course(course_id: uuid.UUID,
course_service: CourseService = Depends(get_course_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    course = await course_service.check_if_course_exists_by_id(course_id)
    course_value = CourseResponse.model_validate(course).model_dump(
        exclude={
            "level": {"created_at", "updated_at"},
            "department": {"created_at", "updated_at"},
        }
    )
    return success_response(status_code=status.HTTP_200_OK, data=course_value)

@courses_router.put("/course/{course_id}", tags=["Courses"])
async def update_course(course_id: uuid.UUID, data: CreateCourse,
course_service: CourseService = Depends(get_course_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    updated_course = await course_service.update_course(course_id, data)
    course_value = CourseResponse.model_validate(updated_course).model_dump(
        exclude={
            "level": {"created_at", "updated_at"},
            "department": {"created_at", "updated_at"},
        }
    )
    return success_response(status_code=status.HTTP_200_OK, data=course_value)

@courses_router.delete("/course/{course_id}", tags=["Courses"])
async def delete_course(course_id: uuid.UUID,
course_service: CourseService = Depends(get_course_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    await course_service.delete_course(course_id)
    return success_response(
        status_code=status.HTTP_204_NO_CONTENT,
        message="Course deleted successfully"
    )

# CRUD for departments
@courses_router.post("/department", tags=["Departments"])
async def create_department(data: dict, dept_service: DeptService = Depends(get_dept_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    new_dept = await dept_service.create_dept(data["name"])
    dept_value = DeptResponse.model_validate(new_dept).model_dump()
    return success_response(status_code=status.HTTP_201_CREATED, data=dept_value)

@courses_router.get("/department/{dept_id}", tags=["Departments"])
async def fetch_one_department(dept_id: uuid.UUID,
dept_service: DeptService = Depends(get_dept_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN, Role_Enum.LECTURER]))
):
    dept = await dept_service.check_if_dept_exist_by_id(dept_id)
    dept_value = DeptResponse.model_validate(dept).model_dump()
    return success_response(status_code=status.HTTP_200_OK, data=dept_value)

@courses_router.put("/department/{dept_id}", tags=["Departments"])
async def update_department(dept_id: uuid.UUID, data: dict,
dept_service: DeptService = Depends(get_dept_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    updated_dept = await dept_service.update_dept(dept_id, data["name"])
    dept_value = DeptResponse.model_validate(updated_dept).model_dump()
    return success_response(status_code=status.HTTP_200_OK, data=dept_value)

@courses_router.delete("/department/{dept_id}", tags=["Departments"])
async def delete_department(dept_id: uuid.UUID,
dept_service: DeptService = Depends(get_dept_service),
user=Depends(get_current_user),
role=Depends(RoleCheck([Role_Enum.ADMIN]))
):
    await dept_service.delete_dept(dept_id)
    return success_response(
        status_code=status.HTTP_204_NO_CONTENT,
        message="Department deleted successfully"
    )
