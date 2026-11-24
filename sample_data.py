"""
sample_data.py — سيرة ونتائج تجريبية باللغتين يستخدمها «فحص النظام»
لاختبار قراءة الملفات وسير العمل بدون مفتاح OpenAI وبدون إنترنت.
"""
from pipeline import AnalysisResult
from schemas import (CandidateInfo, Course, CourseRecommendations, ImprovedCV, JobMatch,
                     JobRecommendations, MissingSkill, SkillGap)

SAMPLE_CV_TEXT = """Data Analyst — 5 years of experience
Experience: Data Analyst at a telecom company (2021 - present), Junior BI Developer (2019 - 2021)
Skills: Python, SQL, Power BI, Excel, Tableau, Statistics, Data Cleaning, Communication
Education: BSc in Information Systems"""

_DATA = {
    "ar": dict(
        candidate=dict(name="مرشح تجريبي", current_title="محلل بيانات", field="تحليل البيانات",
                       education="بكالوريوس نظم المعلومات",
                       summary="محلل بيانات بخبرة خمس سنوات في قطاع الاتصالات، يبني لوحات المؤشرات ويحوّل البيانات إلى قرارات.",
                       skills=["Python", "SQL", "Power BI", "Excel", "Tableau", "الإحصاء", "تنظيف البيانات", "التواصل"],
                       years=5),
        gap=[("Apache Spark", "high", "مطلوبة في أغلب وظائف البيانات الضخمة بالمملكة."),
             ("Cloud (AWS / Azure)", "high", "الجهات تنقل بياناتها للسحابة بشكل متسارع."),
             ("Machine Learning", "medium", "تفتح لك مسار علم البيانات لاحقاً."),
             ("Data Storytelling", "low", "تحسّن عرض نتائجك للإدارة.")],
        tips=["ابدأ بمشروع عملي صغير على Spark باستخدام بيانات مفتوحة.",
              "احصل على شهادة سحابية أساسية مثل AWS Cloud Practitioner.",
              "انشر مشاريعك على GitHub وأضف روابطها في سيرتك."],
        jobs=[("Data Analyst", "محلل بيانات", 85, "خبرتك في Python وSQL وPower BI تغطي أغلب متطلبات هذه الوظيفة.",
               ["البنوك", "شركات الاتصالات", "الجهات الحكومية"]),
              ("Business Intelligence Analyst", "محلل ذكاء أعمال", 78, "بناء لوحات المؤشرات من أبرز نقاط قوتك.",
               ["التجزئة", "الاستشارات", "الطاقة"]),
              ("Junior Data Engineer", "مهندس بيانات مبتدئ", 62, "أساسك في SQL قوي، وتعلّم Spark والسحابة يرفع مطابقتك.",
               ["شركات التقنية", "الاتصالات"])],
        summary="محلل بيانات بخبرة 5 سنوات في قطاع الاتصالات، متخصص في تحويل البيانات إلى رؤى تدعم القرار عبر Python وSQL وPower BI.",
        bullets=["بنيت [X] لوحة مؤشرات في Power BI استخدمتها الإدارة لمتابعة الأداء أسبوعياً.",
                 "أتمتة تقارير شهرية باستخدام Python وفّرت [X] ساعة عمل شهرياً.",
                 "حسّنت جودة البيانات عبر قواعد تنظيف موحدة قللت الأخطاء بنسبة [X]%."],
        ats=["استخدم عناوين أقسام قياسية مثل: الخبرات، المهارات، التعليم.",
             "أضف الكلمات المفتاحية من إعلان الوظيفة كما هي.",
             "تجنب الجداول والصور داخل السيرة عند التقديم الإلكتروني."],
    ),
    "en": dict(
        candidate=dict(name="Demo Candidate", current_title="Data Analyst", field="Data analysis",
                       education="BSc in Information Systems",
                       summary="Data analyst with five years in telecom who builds KPI dashboards and turns data into decisions.",
                       skills=["Python", "SQL", "Power BI", "Excel", "Tableau", "Statistics", "Data Cleaning", "Communication"],
                       years=5),
        gap=[("Apache Spark", "high", "Required in most big-data roles in Saudi Arabia."),
             ("Cloud (AWS / Azure)", "high", "Employers are moving their data to the cloud fast."),
             ("Machine Learning", "medium", "Opens a path into data science later."),
             ("Data Storytelling", "low", "Helps you present findings to management.")],
        tips=["Start a small hands-on Spark project with open data.",
              "Earn an entry-level cloud certificate such as AWS Cloud Practitioner.",
              "Publish your projects on GitHub and link them in your CV."],
        jobs=[("Data Analyst", "Data Analyst", 85, "Your Python, SQL and Power BI experience covers most of this role's requirements.",
               ["Banks", "Telecom companies", "Government entities"]),
              ("Business Intelligence Analyst", "Business Intelligence Analyst", 78,
               "Building KPI dashboards is one of your strongest points.", ["Retail", "Consulting", "Energy"]),
              ("Junior Data Engineer", "Junior Data Engineer", 62,
               "Strong SQL foundation; Spark and cloud skills would raise your match.", ["Tech companies", "Telecom"])],
        summary="Data analyst with 5 years in telecom, turning data into decision-ready insights with Python, SQL and Power BI.",
        bullets=["Built [X] Power BI dashboards that leadership used to track performance weekly.",
                 "Automated monthly reports with Python, saving [X] hours of work per month.",
                 "Improved data quality with standard cleaning rules, cutting errors by [X]%."],
        ats=["Use standard section titles such as Experience, Skills and Education.",
             "Mirror keywords from the job ad exactly.",
             "Avoid tables and images in your CV for online applications."],
    ),
}

_COURSES = [("Apache Spark for Data Engineering", "Apache Spark", "beginner"),
            ("AWS Cloud Practitioner", "Cloud (AWS / Azure)", "beginner"),
            ("Machine Learning Specialization", "Machine Learning", "intermediate")]


def sample_objects(lang: str = "ar") -> dict:
    """يعيد كائنات Pydantic لكل وكيل (تُستخدم أيضاً كبديل للنموذج في فحص النظام)."""
    d = _DATA.get(lang, _DATA["ar"])
    c = d["candidate"]
    return {
        "candidate": CandidateInfo(name=c["name"], current_title=c["current_title"], field=c["field"],
                                   education=c["education"], summary=c["summary"],
                                   extracted_skills=c["skills"], experience_years=c["years"]),
        "gap": SkillGap(missing_skills=[MissingSkill(skill=s, priority=p, reason=r) for s, p, r in d["gap"]],
                        recommendations_to_improve=d["tips"]),
        "jobs": JobRecommendations(jobs=[JobMatch(job_title=t, job_title_local=lt, match_percentage=p, why_fit=w,
                                                  example_employers=e) for t, lt, p, w, e in d["jobs"]]),
        "courses": CourseRecommendations(courses=[Course(course_name=n, target_skill=s, level=lv)
                                                  for n, s, lv in _COURSES]),
        "improve": ImprovedCV(improved_summary=d["summary"], improved_bullet_points=d["bullets"], ats_tips=d["ats"]),
    }


def sample_result(lang: str = "ar", city: str = "riyadh") -> AnalysisResult:
    o = sample_objects(lang)
    return AnalysisResult(o["candidate"], o["gap"], o["jobs"], o["courses"], o["improve"], city, lang, False)
