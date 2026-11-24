"""
checks.py — فحص النظام: اختبارات تُشغَّل من داخل الواجهة (صفحة "فحص النظام").
كل اختبار يعيد تفاصيل نجاحه، أو يرمي استثناءً عند الفشل، أو SkipCheck عند التخطي.
"""
import io
import time
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import agents
import file_reader
import i18n
import pipeline
import report
import sample_data
import schemas


class SkipCheck(Exception):
    pass


@dataclass
class CheckResult:
    key: str
    status: str      # pass / fail / skip
    detail: str
    seconds: float


def _i18n(lang, **_):
    missing = set(i18n.TEXT["ar"]) ^ set(i18n.TEXT["en"])
    assert not missing, f"missing keys: {sorted(missing)}"
    return i18n.t(lang, "chk_d_i18n", n=len(i18n.TEXT["ar"]))


def _schemas(lang, **_):
    job = schemas.JobMatch(job_title="x", job_title_local="x", match_percentage=150, why_fit="x", example_employers=[])
    cand = schemas.CandidateInfo(name="x", current_title="x", field="x", education="x", summary="x",
                                 extracted_skills=[], experience_years=-2)
    assert job.match_percentage == 100 and cand.experience_years == 0
    return i18n.t(lang, "chk_d_schemas")


def _word(lang, **_):
    import docx
    d = docx.Document()
    d.add_paragraph(sample_data.SAMPLE_CV_TEXT)
    table = d.add_table(rows=1, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Tableau", "Statistics"
    buf = io.BytesIO()
    d.save(buf)
    text = file_reader.extract_text(buf.getvalue(), "sample.DOCX")
    assert "Tableau | Statistics" in text
    return i18n.t(lang, "chk_d_word", n=len(text))


def _pdf(lang, **_):
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), sample_data.SAMPLE_CV_TEXT.replace("—", "-"), fontsize=11)
    data = doc.tobytes()
    doc.close()
    text = file_reader.extract_text(data, "sample.pdf")
    assert "Power BI" in text
    return i18n.t(lang, "chk_d_pdf", n=len(text))


def _unsupported(lang, **_):
    try:
        file_reader.extract_text(b"...", "cv.txt")
    except file_reader.CVProcessingError as e:
        assert e.code == "err_unsupported"
        return i18n.t(lang, "chk_d_unsupported")
    raise AssertionError("no error raised")


def _links(lang, **_):
    links = {**report.job_links("Data Analyst", "riyadh", lang), **report.course_links("Apache Spark")}
    assert all(u.startswith("https://") for u in links.values())
    return i18n.t(lang, "chk_d_links", n=len(links))


def _agents(lang, api_key=None, model=None, **_):
    chains = agents.build_chains(agents.build_llm(api_key=api_key or "sk-test", model=model), lang)
    assert len(chains) == 5
    return i18n.t(lang, "chk_d_agents", n=len(chains))


def _pipeline(lang, **_):
    """يشغّل سير العمل كاملاً بنموذج تجريبي (بدون إنترنت) للتأكد من ترابط المراحل."""
    fake = sample_data.sample_objects(lang)

    class FakeChain:
        def __init__(self, name):
            self.name = name

        def invoke(self, _inputs):
            return fake[self.name]

    original = agents.build_chains
    agents.build_chains = lambda _llm, _lang: {k: FakeChain(k) for k in fake}
    try:
        result = pipeline.analyze_cv(sample_data.SAMPLE_CV_TEXT, lang=lang, llm=object())
    finally:
        agents.build_chains = original
    assert result.jobs.jobs[0].match_percentage >= result.jobs.jobs[-1].match_percentage
    assert report.build_markdown_report(result)
    return i18n.t(lang, "chk_d_pipeline")


def _arabic(lang, **_):
    """يتأكد أن النص العربي المشوّه يُصلح قبل وصوله للنموذج، وأن المخرجات غير المسنودة تُحذف."""
    logical = ["السيرة الذاتية", "محلل بيانات في شركة ACME منذ 2021", "المهارات: Python و Power BI والتحليل"]
    run = file_reader._LATIN_RUN
    visual = "\n".join(run.sub(lambda m: m.group(0)[::-1], line[::-1]) for line in logical)
    assert file_reader.clean_text(visual) == "\n".join(logical), "reversed Arabic not repaired"
    assert file_reader.clean_text("ﺍﻟﺴﻴﺮﺓ ﺍﻟﺬﺍﺗﻴﺔ") == "السيرة الذاتية", "presentation forms not repaired"
    name_line = "الاسم: لمياء سلامه الرشيدي"  # «لا» المركّبة يجب أن تبقى «لا» بعد العكس
    lig = run.sub(lambda m: m.group(0)[::-1], name_line.replace("لا", "\ufefb")[::-1])
    assert file_reader.clean_text(lig + "\n" + visual) .split("\n")[0] == name_line, "lam-alef broken"
    cand = schemas.CandidateInfo(name="أحمد علي", current_title="x", field="x", education="x", summary="x",
                                 extracted_skills=["Python", "Power BI", "Kubernetes"], experience_years=3)
    gap = schemas.SkillGap(missing_skills=[schemas.MissingSkill(skill="Python", priority="high", reason="x"),
                                           schemas.MissingSkill(skill="Apache Spark", priority="high", reason="x")],
                           recommendations_to_improve=[])
    imp = schemas.ImprovedCV(improved_summary="x", improved_bullet_points=["رفعت الدقة 40% منذ 2021"], ats_tips=[])
    pipeline.ground_results("\n".join(logical), cand, gap, imp)
    assert cand.extracted_skills == ["Python", "Power BI"] and cand.name == "N/A"
    named = schemas.CandidateInfo(name="سلامه لمياء الرشيدي", current_title="x", field="x", education="x",
                                  summary="x", extracted_skills=[], experience_years=0)
    pipeline.ground_results(name_line, named, schemas.SkillGap(missing_skills=[], recommendations_to_improve=[]),
                            schemas.ImprovedCV(improved_summary="", improved_bullet_points=[], ats_tips=[]))
    assert named.name == "لمياء سلامه الرشيدي", "name order not fixed"
    assert [m.skill for m in gap.missing_skills] == ["Apache Spark"]
    assert imp.improved_bullet_points == ["رفعت الدقة [X] منذ 2021"]
    return i18n.t(lang, "chk_d_arabic")


def _openai(lang, api_key=None, model=None, **_):
    if not api_key:
        raise SkipCheck(i18n.t(lang, "chk_d_openai_skip"))
    reply = agents.build_llm(api_key=api_key, model=model).invoke("Reply with one word: ok").content
    return i18n.t(lang, "chk_d_openai", model=model or agents.DEFAULT_MODEL, reply=reply.strip()[:20])


CHECKS: List[Tuple[str, Callable]] = [
    ("i18n", _i18n), ("schemas", _schemas), ("word", _word), ("pdf", _pdf),
    ("unsupported", _unsupported), ("links", _links), ("agents", _agents),
    ("pipeline", _pipeline), ("arabic", _arabic), ("openai", _openai),
]


def run_all(lang: str = "ar", api_key: Optional[str] = None, model: Optional[str] = None,
            on_result: Optional[Callable[[CheckResult], None]] = None) -> List[CheckResult]:
    results = []
    for key, fn in CHECKS:
        start = time.perf_counter()
        try:
            status, detail = "pass", str(fn(lang, api_key=api_key, model=model))
        except SkipCheck as e:
            status, detail = "skip", str(e)
        except Exception as e:  # noqa: BLE001 — نعرض أي فشل للمستخدم
            status, detail = "fail", f"{type(e).__name__}: {e}"
        res = CheckResult(key, status, detail, time.perf_counter() - start)
        results.append(res)
        if on_result:
            on_result(res)
    return results
