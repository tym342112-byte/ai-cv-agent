"""
schemas.py — هياكل البيانات (Pydantic) التي يلتزم بها النموذج في مخرجاته.
الأوصاف محايدة لغوياً؛ لغة المخرجات تُحدد في تعليمات الوكلاء.
"""
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator


class CandidateInfo(BaseModel):
    name: str = Field(description="Candidate's full name copied exactly as written in the CV (same words, same order), or 'N/A'")
    current_title: str = Field(description="Current or closest job title, in the output language")
    field: str = Field(description="General professional field, e.g. data analysis, accounting, nursing")
    education: str = Field(description="Highest degree and major, or 'N/A'")
    summary: str = Field(description="2-3 sentence summary of the CV")
    extracted_skills: List[str] = Field(description="Technical and soft skills explicitly mentioned in the CV only, "
                                                     "copied exactly as written in the CV (same language and spelling)")
    experience_years: float = Field(description="Total years of actual work experience; 0 for fresh graduates")

    @field_validator("experience_years")
    @classmethod
    def _clamp_years(cls, v: float) -> float:
        return round(min(max(v, 0.0), 60.0), 1)


class MissingSkill(BaseModel):
    skill: str = Field(description="Missing skill name (technical terms in English)")
    priority: Literal["high", "medium", "low"] = Field(description="Learning priority")
    reason: str = Field(description="One sentence on why this skill matters for this candidate in the Saudi market")


class SkillGap(BaseModel):
    missing_skills: List[MissingSkill] = Field(description="3 to 6 missing skills ordered by priority")
    recommendations_to_improve: List[str] = Field(description="Short practical tips to close the gap")


class JobMatch(BaseModel):
    job_title: str = Field(description="Job title in English exactly as used in job ads (short, searchable)")
    job_title_local: str = Field(description="The same job title in the output language")
    match_percentage: int = Field(description="Realistic match percentage between 0 and 100")
    why_fit: str = Field(description="One sentence on why this job fits the candidate")
    example_employers: List[str] = Field(
        description="2-3 types or examples of employers that usually hire for this title in the city "
                    "(guidance only, not confirmed openings)"
    )

    @field_validator("match_percentage")
    @classmethod
    def _clamp_pct(cls, v: int) -> int:
        return int(min(max(v, 0), 100))


class JobRecommendations(BaseModel):
    jobs: List[JobMatch]


class Course(BaseModel):
    course_name: str = Field(description="Short English course topic usable as a search query")
    target_skill: str = Field(description="The missing skill this course covers")
    level: Literal["beginner", "intermediate", "advanced"] = Field(description="Suitable level for the candidate")


class CourseRecommendations(BaseModel):
    courses: List[Course]


class ImprovedCV(BaseModel):
    improved_summary: str = Field(description="New professional summary, in the SAME language as the original CV")
    improved_bullet_points: List[str] = Field(
        description="Rewritten experience bullets (strong verb + task + result), same language as the "
                    "original CV, no invented numbers"
    )
    ats_tips: List[str] = Field(description="Tips to improve compatibility with applicant tracking systems (ATS)")
