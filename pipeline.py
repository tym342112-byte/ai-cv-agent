"""
pipeline.py — سير العمل: تشغيل الوكلاء الخمسة على ثلاث مراحل متوازية.
"""
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, List, Optional

import agents
from file_reader import prepare_cv_text
from i18n import CITIES, city_search, t
from schemas import CandidateInfo, CourseRecommendations, ImprovedCV, JobRecommendations, SkillGap


# ---------- تحقق بعد النموذج: نحذف ما لا يسنده نص السيرة (ضد الهلوسة) ----------
def _norm(text: str) -> str:
    """توحيد للمقارنة: حروف صغيرة، أ/إ/آ ← ا، ة ← ه، ى ← ي، بدون رموز."""
    text = text.lower()
    text = re.sub("[أإآ]", "ا", text).replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"[^\w\s+#.]", " ", text)


def _in_text(phrase: str, norm_cv: str) -> bool:
    """العبارة موجودة في السيرة، أو كل كلماتها المهمة (3 أحرف فأكثر) موجودة."""
    p = _norm(phrase).strip()
    if not p:
        return False
    if p in norm_cv:
        return True
    words = [w for w in p.split() if len(w) >= 3]
    return bool(words) and all(w in norm_cv for w in words)


def _numbers_to_placeholder(line: str, cv_numbers: set) -> str:
    """أي رقم في النقاط المحسنة غير موجود في السيرة الأصلية يُستبدل بـ [X]."""
    return re.sub(r"\d+(?:[.,]\d+)?%?", lambda m: m.group(0) if m.group(0).rstrip("%") in cv_numbers else "[X]", line)


_AR_CHARS = re.compile("[\u0600-\u06FF]")


def _is_arabic(text: str) -> bool:
    letters = re.findall(r"[^\W\d_]", text)
    return bool(letters) and len(_AR_CHARS.findall(text)) / len(letters) > 0.3


def _name_as_written(name: str, cv_text: str) -> str:
    """إذا كانت كلمات الاسم موجودة في سطر واحد من السيرة بترتيب مختلف، نأخذه بالترتيب المكتوب في السيرة
    (النموذج أحياناً يبدّل ترتيب الأسماء العربية: سلامه لمياء ← لمياء سلامه)."""
    words = [_norm(w).strip() for w in name.split() if _norm(w).strip()]
    if len(words) < 2:
        return name
    target = sorted(words)
    for line in cv_text.splitlines():
        tokens = line.split()
        norm_tokens = [_norm(t).strip() for t in tokens]
        for i in range(len(tokens) - len(words) + 1):
            if sorted(norm_tokens[i:i + len(words)]) == target:
                return " ".join(re.sub(r"[^\w\-']", "", t) or t for t in tokens[i:i + len(words)])
    return name


def ground_results(cv_text: str, candidate: CandidateInfo, gap: SkillGap, improved: ImprovedCV) -> List[str]:
    """يعدّل المخرجات في مكانها ويعيد قائمة بما حُذف (للمراجعة).
    نتحقق فقط مما كُتب بنفس لغة السيرة، أو بالإنجليزية (المصطلحات التقنية دائماً إنجليزية)؛
    الترجمة العربية لسيرة إنجليزية لا تُحذف لأنها لن تُوجد حرفياً في النص."""
    norm_cv = _norm(cv_text)
    cv_ar = _is_arabic(cv_text)
    removed: List[str] = []

    def checkable(value: str) -> bool:
        return not _is_arabic(value) or cv_ar

    kept = [s for s in candidate.extracted_skills if not checkable(s) or _in_text(s, norm_cv)]
    removed += [s for s in candidate.extracted_skills if s not in kept]
    candidate.extracted_skills = kept

    if candidate.name.strip().upper() != "N/A":
        candidate.name = _name_as_written(candidate.name, cv_text)
    if candidate.name.strip().upper() != "N/A" and checkable(candidate.name) and not _in_text(candidate.name, norm_cv):
        removed.append(candidate.name)
        candidate.name = "N/A"

    have = {_norm(s).strip() for s in candidate.extracted_skills}
    gap.missing_skills = [m for m in gap.missing_skills
                          if _norm(m.skill).strip() not in have and not _in_text(m.skill, norm_cv)]

    cv_numbers = {n.replace(",", ".") for n in re.findall(r"\d+(?:[.,]\d+)?", cv_text)} | \
                 set(re.findall(r"\d+(?:[.,]\d+)?", cv_text))
    improved.improved_bullet_points = [_numbers_to_placeholder(b, cv_numbers) for b in improved.improved_bullet_points]
    improved.improved_summary = _numbers_to_placeholder(improved.improved_summary, cv_numbers)
    return removed


@dataclass
class AnalysisResult:
    candidate: CandidateInfo
    skill_gap: SkillGap
    jobs: JobRecommendations
    courses: CourseRecommendations
    improved_cv: ImprovedCV
    city: str            # مفتاح المدينة في CITIES
    lang: str = "ar"
    truncated: bool = False


def analyze_cv(
    cv_text: str,
    city: str = "riyadh",
    lang: str = "ar",
    llm=None,
    on_step: Optional[Callable[[str], None]] = None,
) -> AnalysisResult:
    """
    المراحل:
      1) استخراج البيانات  ‖  تحسين السيرة
      2) الفجوة المهارية  ‖  الوظائف
      3) الدورات
    on_step تُستدعى دائماً من الخيط الرئيسي، فهي آمنة مع Streamlit.
    """
    if city not in CITIES:
        city = "riyadh"
    step = on_step or (lambda _msg: None)
    cv_text, truncated = prepare_cv_text(cv_text)
    chains = agents.build_chains(llm or agents.build_llm(), lang)
    city_en = city_search(city)
    city_prompt = f"{city_en}, Saudi Arabia" if city_en else "any city in Saudi Arabia"

    with ThreadPoolExecutor(max_workers=3) as pool:
        step(str(t(lang, "step_1")))
        f_improve = pool.submit(chains["improve"].invoke, {"cv_text": cv_text})
        candidate: CandidateInfo = chains["candidate"].invoke({"cv_text": cv_text})
        # نحذف المهارات والاسم غير الموجودين في السيرة قبل ما تعتمد عليها باقي المراحل
        ground_results(cv_text, candidate, SkillGap(missing_skills=[], recommendations_to_improve=[]),
                       ImprovedCV(improved_summary="", improved_bullet_points=[], ats_tips=[]))

        base = {
            "field": candidate.field,
            "title": candidate.current_title,
            "experience": candidate.experience_years,
            "skills": ", ".join(candidate.extracted_skills) or "N/A",
        }

        step(str(t(lang, "step_2")))
        f_gap = pool.submit(chains["gap"].invoke, base)
        f_jobs = pool.submit(chains["jobs"].invoke, {**base, "city": city_prompt})
        gap: SkillGap = f_gap.result()

        step(str(t(lang, "step_3")))
        missing = ", ".join(f"{s.skill} ({s.priority})" for s in gap.missing_skills) or "none"
        courses: CourseRecommendations = chains["courses"].invoke(
            {"field": candidate.field, "experience": candidate.experience_years, "missing_skills": missing}
        )

        jobs: JobRecommendations = f_jobs.result()
        improved: ImprovedCV = f_improve.result()

    ground_results(cv_text, candidate, gap, improved)
    order = {"high": 0, "medium": 1, "low": 2}
    gap.missing_skills.sort(key=lambda s: order[s.priority])
    jobs.jobs.sort(key=lambda j: j.match_percentage, reverse=True)
    step(str(t(lang, "done")))
    return AnalysisResult(candidate, gap, jobs, courses, improved, city, lang, truncated)
