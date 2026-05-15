from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
async def get_summary():
    return {
        "total_jobs": 0,
        "avg_salary": 0,
        "top_skills": [],
        "city_distribution": {},
        "salary_distribution": {},
    }


@router.get("/salary-distribution")
async def get_salary_distribution():
    return {
        "labels": ["0-10K", "10-20K", "20-30K", "30-40K", "40K+"],
        "data": [0, 0, 0, 0, 0],
    }


@router.get("/education-distribution")
async def get_education_distribution():
    return {
        "labels": ["大专", "本科", "硕士", "博士", "不限"],
        "data": [0, 0, 0, 0, 0],
    }


@router.get("/skill-wordcloud")
async def get_skill_wordcloud():
    return {"words": []}
