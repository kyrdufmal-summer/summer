# Chapter 08 Course 독립 실습 — 학습 대화에서 재구성한 참고 구현
# 주의: 로컬 courses.py 원본을 직접 읽은 파일이 아니므로 제출 전 대조 필요.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from psycopg.rows import dict_row
from common.db import get_connection

app = FastAPI()

# 응답할 강의 정보 형식
class CourseResponse(BaseModel):
    id: int       # DB 고유번호
    title: str    # 강의명
    level: int    # 강의 난이도

# PUT: 제목과 난이도 모두 필요
class CourseUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    level: int = Field(ge=1, le=5)

# PATCH: 생략은 가능하지만 명시적 null은 허용하지 않음
class CoursePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    level: int | None = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def reject_explicit_null(self):
        # 실제 요청에 들어온 필드만 검사
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self

# GET: DB에 저장된 실제 강의 반환
@app.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: int):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, title, level FROM public.courses WHERE id = %s",
                (course_id,),
            )
            course = cur.fetchone()
            if course is None:
                raise HTTPException(status_code=404, detail="Course not found")
            return course

# PUT: 강의 제목과 난이도를 모두 UPDATE
@app.put("/courses/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, course: CourseUpdate):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE public.courses
                SET title = %s, level = %s
                WHERE id = %s
                RETURNING id, title, level
                """,
                (course.title, course.level, course_id),
            )
            updated = cur.fetchone()
            if updated is None:
                raise HTTPException(status_code=404, detail="Course not found")
            return updated

# PATCH: 요청한 필드만 UPDATE, 빈 요청은 400
@app.patch("/courses/{course_id}", response_model=CourseResponse)
def patch_course(course_id: int, course: CoursePatch):
    changes = course.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="At least one field is required")

    # SQL 컬럼명은 사용자 입력을 직접 사용하지 않고 화이트리스트에서 선택
    allowed_fields = {"title": "title", "level": "level"}
    set_parts = []
    values = []
    for field, value in changes.items():
        column = allowed_fields[field]
        set_parts.append(f"{column} = %s")
        values.append(value)
    values.append(course_id)

    sql = f"""
        UPDATE public.courses
        SET {', '.join(set_parts)}
        WHERE id = %s
        RETURNING id, title, level
    """
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, values)
            updated = cur.fetchone()
            if updated is None:
                raise HTTPException(status_code=404, detail="Course not found")
            return updated
