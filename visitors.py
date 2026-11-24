"""
visitors.py — عدّاد الزوار: يحفظ العدد في ملف JSON ويزيده مرة واحدة لكل جلسة.
القفل (Lock) يمنع تلف الملف إذا دخل أكثر من زائر في نفس اللحظة.
"""
import json
import os
import threading
from datetime import date

VISITORS_PATH = os.environ.get("CV_AGENT_VISITORS", "visitors.json")
_LOCK = threading.Lock()


def _read() -> dict:
    try:
        with open(VISITORS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def register_visit() -> dict:
    """يزيد العداد الكلي وعداد اليوم، ويعيد {"total", "today"}."""
    today = date.today().isoformat()
    with _LOCK:
        data = _read()
        data["total"] = int(data.get("total", 0)) + 1
        days = data.get("days", {})
        days[today] = int(days.get(today, 0)) + 1
        data["days"] = dict(sorted(days.items())[-60:])  # آخر 60 يوماً فقط
        tmp = VISITORS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, VISITORS_PATH)  # كتابة آمنة
    return {"total": data["total"], "today": days[today]}


def get_counts() -> dict:
    data = _read()
    return {"total": int(data.get("total", 0)),
            "today": int(data.get("days", {}).get(date.today().isoformat(), 0))}
