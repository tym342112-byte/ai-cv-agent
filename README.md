# وكيل تطوير السيرة الذاتية الذكي — AI CV Agent

تطبيق ويب يحلل السيرة الذاتية بخمسة وكلاء ذكيين مبنيين بـ **LangChain** و **OpenAI**، ويعرض الفجوة المهارية، والوظائف المناسبة في مدينتك، والدورات المقترحة، وصياغة احترافية للسيرة — بواجهة **Streamlit** باللغتين العربية والإنجليزية.

المشروع النهائي لمقرر أساسيات LangChain — الكلية التطبيقية، جامعة الأمير مساعد بن عبدالرحمن · دبلوم الذكاء الاصطناعي التوليدي · إشراف د. محمد الشهري · 1448هـ.

## المزايا

| الميزة | الوصف |
|---|---|
| قراءة الملفات | PDF و Word (بما فيها الجداول)، مع إصلاح النص العربي المعكوس والحروف المتصلة |
| خمسة وكلاء | استخراج البيانات · الفجوة المهارية · الوظائف · الدورات · تحسين السيرة |
| ثلاث مراحل متوازية | تشغيل الوكلاء بالتوازي لتقليل وقت الانتظار |
| الحد من الهلوسة | قواعد صارمة في التعليمات + تحقق بعد النموذج يحذف ما لا يوجد في السيرة |
| روابط جاهزة | LinkedIn · Indeed · Bayt · Tanqeeb · جدارات · Coursera · Udemy |
| فحص النظام | صفحة داخل الواجهة تشغّل 10 اختبارات بضغطة زر |
| عدّاد الزوار | الكلي وزوار اليوم |

## الملفات

| الملف | الدور |
|---|---|
| `app.py` | واجهة Streamlit (نقطة التشغيل) |
| `agents.py` | النموذج اللغوي والوكلاء الخمسة (Prompt Templates + LCEL) |
| `pipeline.py` | سير العمل على ثلاث مراحل + التحقق من المخرجات |
| `schemas.py` | هياكل المخرجات (Pydantic) |
| `file_reader.py` | قراءة PDF و Word وتنظيف النص |
| `report.py` | روابط البحث وتقرير Markdown |
| `i18n.py` | نصوص اللغتين |
| `checks.py` · `sample_data.py` | اختبارات صفحة «فحص النظام» |
| `assets.py` | شعار الكلية |
| `visitors.py` | عدّاد الزوار |
| `LCH_PROJECT.ipynb` | نسخة Google Colab من المشروع |

## التشغيل محلياً

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # ثم ضع مفتاح OpenAI
streamlit run app.py
```

## النشر على Streamlit Community Cloud

1. ادخل [share.streamlit.io](https://share.streamlit.io) بحساب GitHub.
2. **Create app** ← اختر هذا المستودع، والفرع `main`، والملف `app.py`.
3. من **Advanced settings → Secrets** أضف:
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```
4. **Deploy**.

> لا توجد أي مفاتيح داخل الكود ولا خانة للمفتاح في الواجهة؛ التطبيق يقرأ المفتاح من Secrets فقط.

---

**English:** A bilingual (Arabic/English) Streamlit app that analyzes a CV with five LangChain agents (OpenAI gpt-4o-mini): skill gap, job matches with search links, course recommendations and an ATS-friendly rewrite. Run with `streamlit run app.py` after setting `OPENAI_API_KEY` in `.streamlit/secrets.toml`.
