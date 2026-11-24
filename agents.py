"""
agents.py — النموذج اللغوي والوكلاء الخمسة (Prompt Templates + LCEL Chains).
"""
import os
from typing import Dict, Optional

from schemas import CandidateInfo, CourseRecommendations, ImprovedCV, JobRecommendations, SkillGap

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

LANG_RULE = {
    "ar": "Write every descriptive field (summaries, reasons, tips, local titles) in correct, simple Modern Standard "
          "Arabic (فصحى) — no dialect, no invented or misspelled words, no literal word-by-word translation. "
          "Keep technical terms, tools, frameworks and certifications in English (Latin script). "
          "Never translate or transliterate names of people, companies or universities: copy them exactly as written.",
    "en": "Write every descriptive field (summaries, reasons, tips, local titles) in clear, professional English. "
          "Copy names of people, companies and universities exactly as written in the CV.",
}

# قواعد ضد الهلوسة تُضاف لكل الوكلاء
GROUNDING = (
    " STRICT RULES: Use ONLY facts stated in the provided text; never guess. "
    "If something is not stated (name, degree, dates, company), write 'N/A'. "
    "Never invent companies, employers, degrees, dates, numbers, certificates or achievements. "
    "The CV may be in Arabic and may contain extraction noise; if a passage is unreadable, ignore it instead of "
    "guessing what it says."
)

# كل وكيل: (تعليمات النظام، رسالة المستخدم)
PROMPTS = {
    "candidate": (
        "You are an expert HR analyst. Analyze the CV and extract the requested data precisely. "
        "extracted_skills must contain only skills explicitly written in the CV. Compute years of experience from "
        "actual employment dates written in the CV, excluding years of study; if no dates are given, use 0. "
        "The summary must only restate what the CV says. {lang_rule}",
        "CV text:\n<cv>\n{cv_text}\n</cv>",
    ),
    "gap": (
        "You are a career advisor specialized in the Saudi labor market. Based on the candidate's field, "
        "title, experience and current skills, identify the in-demand skills they lack, ordered by priority. "
        "Never list a skill they already have. Base every reason on the candidate's stated field and title. {lang_rule}",
        "Field: {field}\nCurrent title: {title}\nYears of experience: {experience}\nCurrent skills: {skills}",
    ),
    "jobs": (
        "You are a recruitment expert in the Saudi market. Suggest 4 realistic job titles that fit the "
        "candidate's experience level and skills for work in {city}. Match percentages must be realistic and "
        "reflect missing skills. job_title must be the common English title used in LinkedIn job ads so it "
        "works as a search keyword, and job_title_local must be its accurate, commonly used translation. "
        "example_employers must be sectors or employer types (e.g. banks, government entities), not specific "
        "company names. {lang_rule}",
        "Current title: {title}\nField: {field}\nSkills: {skills}\nYears of experience: {experience}\nLocation: {city}",
    ),
    "courses": (
        "You are an academic advisor. Suggest one course for each high-priority missing skill (maximum 4 courses). "
        "course_name must be a short English phrase that works as a search query on Coursera and Udemy. {lang_rule}",
        "Candidate field: {field}\nYears of experience: {experience}\nMissing skills by priority: {missing_skills}",
    ),
    "improve": (
        "You are a professional CV writer. Rewrite the personal summary and experience bullet points to be "
        "professional and achievement-oriented (strong verb + task + result). Write improved_summary and "
        "improved_bullet_points in the SAME language as the original CV. Never invent numbers or achievements; "
        "when a number is needed, write [X] for the candidate to fill in. For ats_tips only: {lang_rule}",
        "Original CV text:\n<cv>\n{cv_text}\n</cv>",
    ),
}

SCHEMAS = {
    "candidate": CandidateInfo,
    "gap": SkillGap,
    "jobs": JobRecommendations,
    "courses": CourseRecommendations,
    "improve": ImprovedCV,
}


def build_llm(api_key: Optional[str] = None, model: Optional[str] = None):
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model or DEFAULT_MODEL,
        temperature=0,
        api_key=api_key or os.environ.get("OPENAI_API_KEY"),
        seed=7,          # نتائج ثابتة قدر الإمكان لنفس السيرة
        timeout=90,
        max_retries=3,
    )


def build_chains(llm, lang: str = "ar") -> Dict[str, object]:
    """يبني الوكلاء الخمسة: Prompt | LLM مع مخرجات منظمة (Pydantic)."""
    from langchain_core.prompts import ChatPromptTemplate

    rule = LANG_RULE.get(lang, LANG_RULE["ar"])
    return {
        name: ChatPromptTemplate.from_messages([("system", system.replace("{lang_rule}", rule)), ("human", human)])
        | llm.with_structured_output(SCHEMAS[name])
        for name, (system, human) in ((n, (sys_ + GROUNDING, hum)) for n, (sys_, hum) in PROMPTS.items())
    }
