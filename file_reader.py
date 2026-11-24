"""
file_reader.py — قراءة السيرة الذاتية من PDF أو Word وتنظيف النص.
"""
import io
import os
import re
import unicodedata
from typing import List, Tuple

from i18n import t

SUPPORTED_EXTENSIONS = (".pdf", ".docx")
MIN_CV_CHARS = 100      # أقل من هذا غالباً يعني PDF ممسوح ضوئياً
MAX_CV_CHARS = 15_000   # حد أعلى لطول النص المرسل للنموذج


class CVProcessingError(Exception):
    """خطأ مفهوم للمستخدم. code يطابق مفتاحاً في i18n: err_unsupported / err_corrupt / err_scanned."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail

    def message(self, lang: str) -> str:
        return str(t(lang, self.code))


# ---------- تنظيف النص العربي (أهم سبب للهلوسة: نص عربي مشوّه يصل للنموذج فيخمّن) ----------
_AR = r"\u0600-\u06FF"
_INVISIBLE = re.compile("[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff\u00ad]")
_TASHKEEL = re.compile("[\u064b-\u065f\u0670\u06d6-\u06ed]")
_LATIN_RUN = re.compile(r"[A-Za-z0-9@._+\-/:#%&()]+(?: +[A-Za-z0-9@._+\-/:#%&()]+)*")
_AR_WORD = re.compile(f"[{_AR}]{{2,}}")
_AR_ANY = re.compile("[\u0600-\u06FF\ufb50-\ufdff\ufe70-\ufeff]")
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def _fix_presentation_forms(text: str) -> str:
    """PDF أحياناً يخزن الحروف بأشكالها المتصلة (ﺍﻟﺴﻴﺮﺓ) فيراها النموذج رموزاً غريبة: نعيدها لحروف عادية."""
    return "".join(unicodedata.normalize("NFKC", ch) if "\ufb50" <= ch <= "\ufdff" or "\ufe70" <= ch <= "\ufeff"
                   else ch for ch in text)


def _is_reversed_arabic(text: str) -> bool:
    """بعض ملفات PDF تخرج العربي معكوساً (ةريسلا بدل السيرة). نكشفه من «ال» التعريف: في النص المعكوس تأتي آخر الكلمة."""
    words = _AR_WORD.findall(text)
    starts = sum(w.startswith("ال") for w in words)
    ends = sum(w.endswith("لا") for w in words)
    return ends >= 3 and ends > 2 * max(starts, 1)


def _reverse_line(line: str) -> str:
    """يعكس السطر العربي ثم يعيد الكلمات الإنجليزية والأرقام لاتجاهها الصحيح."""
    if not _AR_ANY.search(line):
        return line
    return _LATIN_RUN.sub(lambda m: m.group(0)[::-1], line[::-1])


def normalize_arabic(text: str) -> str:
    text = _INVISIBLE.sub("", text)
    # الكشف عن النص المعكوس يتم على نسخة مفكوكة الحروف، لكن العكس نفسه يتم قبل فك الحروف المتصلة:
    # حرف «لا» المركّب (ﻻ) رمز واحد، لو فككناه قبل العكس لصار «ال» (سلامه ← سالمه).
    if _is_reversed_arabic(_fix_presentation_forms(text)):
        text = "\n".join(_reverse_line(line) for line in text.split("\n"))
    text = _fix_presentation_forms(text)
    text = _TASHKEEL.sub("", text).replace("ـ", "")   # التشكيل والتطويل
    return text.translate(_AR_DIGITS)                     # ٢٠٢٤ → 2024 حتى يطابق النموذج الأرقام


def clean_text(text: str) -> str:
    """ينظف المسافات الزائدة مع الحفاظ على فواصل الأسطر (مهمة لفهم أقسام السيرة)، ويصلح النص العربي."""
    text = text.replace("\x00", "")
    text = normalize_arabic(text)
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(data: bytes) -> str:
    import fitz  # PyMuPDF

    with fitz.open(stream=data, filetype="pdf") as doc:
        return clean_text("\n".join(page.get_text("text", sort=True) for page in doc))  # sort: ترتيب القراءة الصحيح


def extract_text_from_docx(data: bytes) -> str:
    import docx

    document = docx.Document(io.BytesIO(data))
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:  # كثير من السير مصممة بجداول
        for row in table.rows:
            cells: List[str] = []
            for cell in row.cells:
                txt = cell.text.strip()
                if txt and txt not in cells:  # الخلايا المدمجة تتكرر
                    cells.append(txt)
            if cells:
                parts.append(" | ".join(cells))
    return clean_text("\n".join(parts))


def extract_text(data: bytes, file_name: str) -> str:
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise CVProcessingError("err_unsupported")
    try:
        text = extract_text_from_pdf(data) if ext == ".pdf" else extract_text_from_docx(data)
    except Exception as e:
        raise CVProcessingError("err_corrupt", str(e)) from e
    if len(text) < MIN_CV_CHARS:
        raise CVProcessingError("err_scanned")
    return text


def extract_text_from_path(path: str) -> str:
    with open(path, "rb") as f:
        return extract_text(f.read(), path)


def prepare_cv_text(text: str) -> Tuple[str, bool]:
    """يقص النص الطويل جداً ويعيد (النص، هل تم القص)."""
    if len(text) > MAX_CV_CHARS:
        return text[:MAX_CV_CHARS], True
    return text, False
