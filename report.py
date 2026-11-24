"""
report.py — روابط البحث عن الوظائف والدورات، وتقرير Markdown باللغة المختارة.
"""
from typing import Dict
from urllib.parse import urlencode

from file_reader import MAX_CV_CHARS
from i18n import CITIES, city_name, city_search, t


def _google_site_search(site: str, title: str, location: str) -> str:
    return "https://www.google.com/search?" + urlencode({"q": f'site:{site} "{title}" {location}'})


def job_links(job_title: str, city: str, lang: str = "ar") -> Dict[str, str]:
    city_en = city_search(city) if city in CITIES else None
    location = f"{city_en}, Saudi Arabia" if city_en else "Saudi Arabia"
    return {
        "LinkedIn": "https://www.linkedin.com/jobs/search/?" + urlencode({"keywords": job_title, "location": location}),
        "Indeed": "https://sa.indeed.com/jobs?" + urlencode({"q": job_title, "l": city_en or ""}),
        "Bayt": _google_site_search("bayt.com", job_title, city_en or "Saudi Arabia"),
        "Tanqeeb": _google_site_search("saudi.tanqeeb.com", job_title, city_en or "Saudi Arabia"),
        str(t(lang, "jadarat")): "https://jadarat.sa/",
    }


def course_links(course_name: str) -> Dict[str, str]:
    return {
        "Coursera": "https://www.coursera.org/search?" + urlencode({"query": course_name}),
        "Udemy": "https://www.udemy.com/courses/search/?" + urlencode({"q": course_name}),
        "LinkedIn Learning": "https://www.linkedin.com/learning/search?" + urlencode({"keywords": course_name}),
    }


def build_markdown_report(r) -> str:
    """r: AnalysisResult من pipeline.py"""
    L = lambda key, **kw: str(t(r.lang, key, **kw))  # noqa: E731
    prio, level = t(r.lang, "priority"), t(r.lang, "level")
    c, g = r.candidate, r.skill_gap
    lines = [
        f"# 📋 {L('r_title')}",
        "",
        f"## 👤 {L('r_info')}",
        f"- **{L('m_name')}:** {c.name}",
        f"- **{L('current_title')}:** {c.current_title}",
        f"- **{L('field')}:** {c.field}",
        f"- **{L('education')}:** {c.education}",
        f"- **{L('m_years')}:** {c.experience_years:g}",
        f"- **{L('skills')}:** {', '.join(c.extracted_skills)}",
        "",
        f"> {c.summary}",
        "",
        f"## 🔍 {L('gap_heading')}",
    ]
    lines += [f"- **{s.skill}** — {prio[s.priority]}: {s.reason}" for s in g.missing_skills]
    lines += ["", f"**{L('tips_heading')}:**"] + [f"- {tip}" for tip in g.recommendations_to_improve]

    lines += ["", f"## 💼 {L('jobs_heading', city=city_name(r.city, r.lang))}", f"_{L('jobs_note')}_", ""]
    for j in r.jobs.jobs:
        links = " · ".join(f"[{k}]({v})" for k, v in job_links(j.job_title, r.city, r.lang).items())
        title = j.job_title if r.lang == "en" else f"{j.job_title} — {j.job_title_local}"
        lines += [
            f"### {title} ({j.match_percentage}% {L('match')})",
            j.why_fit,
            f"- {L('employers')} {', '.join(j.example_employers)}",
            f"- {L('r_search')} {links}",
            "",
        ]

    lines += [f"## 📚 {L('courses_heading')}"]
    for co in r.courses.courses:
        links = " · ".join(f"[{k}]({v})" for k, v in course_links(co.course_name).items())
        lines.append(f"- **{co.course_name}** ({level[co.level]}) — {L('covers')} {co.target_skill} — {links}")

    imp = r.improved_cv
    lines += ["", f"## ✨ {L('summary_label')}", "", imp.improved_summary, ""]
    lines += [f"**{L('bullets_heading')}:**"] + [f"- {p}" for p in imp.improved_bullet_points]
    lines += ["", f"**{L('ats_heading')}:**"] + [f"- {tip}" for tip in imp.ats_tips]

    if r.truncated:
        lines += ["", f"_{L('r_truncated', n=f'{MAX_CV_CHARS:,}')}_"]
    return "\n".join(lines)
