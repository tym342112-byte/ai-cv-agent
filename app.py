"""
app.py — واجهة Streamlit لوكيل السيرة الذاتية (تصميم Figma مبني على قالب Simple Design System)
الصفحات: التحليل · فحص النظام        التشغيل:  streamlit run app.py
"""
import hashlib
import html
import os

import streamlit as st

import checks
from assets import LOGO_MARK, LOGO_WHITE
import visitors
from agents import DEFAULT_MODEL, build_llm
from file_reader import CVProcessingError, extract_text
from i18n import CITIES, city_name, t
from pipeline import analyze_cv
from report import build_markdown_report, course_links, job_links

# ================= الحالة العامة =================
for key, default in {"lang": "ar", "page": 0}.items():
    st.session_state.setdefault(key, default)
LANG = st.session_state.lang
RTL = LANG == "ar"


def T(key, **kw):
    return t(LANG, key, **kw)


def esc(value) -> str:
    return html.escape(str(value))


def html_block(markup: str):
    st.markdown(markup, unsafe_allow_html=True)


st.set_page_config(page_title=T("page_title"), page_icon="📄", layout="wide", initial_sidebar_state="collapsed")

# ================= التصميم =================
html_block("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Readex+Pro:wght@400;500;600;700&display=swap');
:root{--navy:#0B1B3F;--navy2:#13306B;--blue:#1D4ED8;--blue2:#2563EB;--sky:#38BDF8;--soft:#EFF6FF;
      --soft-line:#BFDBFE;--bg:#E8EEF7;--line:#E2E8F0;--ink:#0F172A;--muted:#64748B;--body:#334155;
      --shadow:0 4px 16px rgba(11,27,63,.06);}
.stApp{background:var(--bg);}
.stApp :is(p,li,h1,h2,h3,h4,label,button,input,textarea,div){font-family:'Readex Pro',sans-serif;}
[data-testid="stHeader"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none;}
.block-container{padding-top:1.2rem;max-width:1400px;}

/* شريط التنقل العلوي */
.st-key-topnav{background:linear-gradient(90deg,var(--navy),var(--navy2));border-radius:16px;padding:10px 20px;
      box-shadow:0 6px 20px rgba(11,27,63,.15);}
.cv-brand{display:flex;align-items:center;gap:12px;}
.cv-logo{width:40px;height:40px;border-radius:11px;background:linear-gradient(135deg,var(--blue2),var(--sky));
      display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;color:#fff;flex-shrink:0;}
.cv-brand b{display:block;font-size:17px;color:#fff;line-height:1.2;}
.cv-brand small{font-size:11px;color:#BFDBFE;}
.st-key-topnav [data-testid="stButtonGroup"]{background:rgba(255,255,255,.07);border-radius:999px;padding:4px;
      width:fit-content;}
.st-key-topnav [data-testid="stButtonGroup"] button{background:transparent;border:none;color:#DBEAFE;
      border-radius:999px;padding:6px 18px;font-weight:500;white-space:nowrap;}
.st-key-topnav [data-testid="stButtonGroup"] button[kind*="Active"],
.st-key-topnav [data-testid="stButtonGroup"] button[aria-checked="true"]{background:#fff!important;
      color:var(--navy)!important;font-weight:600;}
.st-key-nav_lang [data-testid="stButtonGroup"] button[kind*="Active"],
.st-key-nav_lang [data-testid="stButtonGroup"] button[aria-checked="true"]{
      background:linear-gradient(90deg,var(--blue2),#3B82F6)!important;color:#fff!important;}
.st-key-nav_lang{display:flex;justify-content:flex-end;}

/* البانر */
.st-key-hero{position:relative;overflow:hidden;border-radius:22px;padding:36px 40px;margin-top:8px;
      background:linear-gradient(135deg,var(--navy2),var(--blue2));box-shadow:0 10px 30px rgba(11,27,63,.18);}
.st-key-hero::before{content:"";position:absolute;width:300px;height:300px;border-radius:50%;
      background:rgba(56,189,248,.12);inset-inline-end:-80px;top:-140px;}
.cv-tag-hero{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:999px;
      background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.2);color:#E0F2FE;font-size:12px;}
.cv-hero-title{font-size:34px;font-weight:700;color:#fff;margin:12px 0 8px;line-height:1.25;}
.cv-hero-sub{font-size:16px;color:#DBEAFE;margin:0 0 18px;}
.cv-btn-white{display:inline-block;background:#fff;color:var(--navy)!important;font-weight:600;padding:9px 22px;
      border-radius:12px;text-decoration:none!important;}
.cv-steps{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.18);border-radius:18px;padding:20px 22px;}
.cv-steps h4{color:#fff;font-size:15px;font-weight:600;margin:0 0 14px;padding:0;}
.cv-step{display:flex;gap:12px;align-items:flex-start;margin-bottom:12px;}
.cv-step i{width:28px;height:28px;border-radius:50%;background:#fff;color:var(--navy);font-style:normal;
      font-weight:700;font-size:13px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.cv-step b{display:block;color:#fff;font-size:14px;}
.cv-step span{color:#BFDBFE;font-size:12px;}

/* لوحة التحكم والبطاقات */
.st-key-panel,.st-key-chk_header{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px;
      box-shadow:var(--shadow);margin-top:8px;}
[data-testid="stFileUploaderDropzone"]{background:rgba(239,246,255,.6);border:1.5px dashed rgba(37,99,235,.4);
      border-radius:14px;}
[data-testid="stFileUploaderDropzone"] svg{fill:var(--blue);}
.stTextInput input,[data-baseweb="select"]>div{border-radius:10px!important;}
.stButton button[kind="primary"],[data-testid="stBaseButton-primary"]{
      background:linear-gradient(90deg,var(--blue),#3B82F6)!important;border:none!important;border-radius:12px;
      font-weight:600;padding:10px 22px;color:#fff!important;box-shadow:0 6px 14px rgba(29,78,216,.3);}
.stButton button[kind="primary"]:hover{filter:brightness(1.08);}
.stDownloadButton button{width:100%;background:var(--navy)!important;color:#fff!important;border:none!important;
      border-radius:12px;font-weight:600;padding:12px 16px;}

/* التبويبات (نمط Tab من القالب) */
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{font-size:15px;font-weight:500;color:var(--muted);padding:10px 14px;}
.stTabs [aria-selected="true"]{color:var(--blue)!important;font-weight:600;}
.stTabs [data-baseweb="tab-highlight"]{background:var(--blue);height:3px;}

.cv-field{font-size:14px;color:var(--ink);font-weight:500;margin-bottom:6px;}
.cv-card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px;margin-bottom:16px;
      box-shadow:var(--shadow);}
.cv-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:8px 0 20px;}
.cv-grid .cv-card{margin:0;}
.cv-metric{display:flex;gap:14px;align-items:center;padding:18px;}
.cv-ic{width:44px;height:44px;border-radius:12px;background:var(--soft);display:flex;align-items:center;
      justify-content:center;flex-shrink:0;color:var(--blue);}
.cv-ic.accent{background:linear-gradient(135deg,var(--blue),var(--sky));color:#fff;}
.cv-label{font-size:12px;color:var(--muted);margin-bottom:2px;}
.cv-value{font-size:22px;font-weight:700;color:var(--ink);line-height:1.2;}
.cv-value.accent{color:var(--blue);}
.cv-h2{font-size:20px;font-weight:600;color:var(--ink);margin:12px 0 2px;}
.cv-h3{font-size:17px;font-weight:600;color:var(--ink);margin:0;}
.cv-title-row{display:flex;align-items:center;gap:10px;margin-bottom:14px;}
.cv-title-row .cv-ic{width:34px;height:34px;border-radius:10px;}
.cv-note{font-size:13px;color:var(--muted);margin:0 0 14px;}
.cv-sub{font-size:13px;color:var(--muted);}
.cv-text{font-size:14px;color:var(--body);margin:12px 0 6px;line-height:1.6;}
.cv-top{display:flex;gap:16px;align-items:flex-start;justify-content:space-between;}
.cv-match{background:var(--soft);border:1px solid var(--soft-line);border-radius:12px;padding:8px 14px;
      text-align:center;flex-shrink:0;}
.cv-match b{display:block;font-size:20px;color:var(--blue);line-height:1.2;}
.cv-match span{font-size:11px;color:var(--blue);font-weight:500;}
.cv-progress{height:6px;background:var(--line);border-radius:4px;overflow:hidden;margin-top:12px;}
.cv-progress div{height:100%;border-radius:4px;background:linear-gradient(90deg,var(--blue),var(--sky));}
.cv-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;}
.cv-chip{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:10px;
      background:var(--soft);border:1px solid var(--soft-line);color:var(--blue)!important;
      font-size:13px;font-weight:500;text-decoration:none!important;transition:all .15s;}
.cv-chip:hover{background:var(--blue);color:#fff!important;border-color:var(--blue);}
.cv-tag{display:inline-block;padding:4px 10px;border-radius:8px;background:var(--soft);color:var(--blue);
      font-size:13px;margin:0 0 6px 6px;}
.cv-gap-item{display:flex;gap:12px;align-items:flex-start;margin-bottom:14px;}
.cv-gap-item b{font-size:14px;color:var(--ink);display:block;}
/* وسوم القالب (Tag: Danger / Warning / Positive / Brand) */
.cv-badge{padding:4px 10px;border-radius:8px;font-size:12px;font-weight:600;white-space:nowrap;}
.cv-badge.high,.cv-badge.fail{background:#FEE9E7;color:#900B09;}
.cv-badge.medium,.cv-badge.skip{background:#FFF1C2;color:#522504;}
.cv-badge.low,.cv-badge.pass{background:#CFF7D3;color:#02542D;}
.cv-badge.level{background:var(--soft);color:var(--blue);}
.cv-list{margin:0;padding-inline-start:20px;color:var(--body);font-size:14px;line-height:1.7;}
.cv-info{display:flex;gap:12px;align-items:flex-start;background:var(--soft);border:1px solid var(--soft-line);
      border-radius:14px;padding:14px 18px;color:var(--body);font-size:13px;margin-top:16px;}

/* فحص النظام */
.cv-chk-title{font-size:24px;font-weight:700;color:var(--ink);margin:0;}
.cv-mini{background:var(--bg);border-radius:12px;padding:12px 16px;}
.cv-chk-bar{height:6px;border-radius:4px;background:linear-gradient(90deg,var(--blue),#22C55E);margin-top:16px;}
.cv-chk-row{display:flex;align-items:center;gap:16px;padding:16px 0;border-bottom:1px solid var(--line);}
.cv-chk-row:last-child{border-bottom:none;}
.cv-chk-row .st{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;
      flex-shrink:0;}
.cv-chk-row .st.pass{background:#DCFCE7;color:#15803D;}
.cv-chk-row .st.fail{background:#FEE2E2;color:#DC2626;}
.cv-chk-row .st.skip{background:#FEF3C7;color:#B45309;}
.cv-chk-row .tx{flex:1;min-width:0;}
.cv-chk-row .tx b{font-size:15px;color:var(--ink);display:block;}
.cv-chk-row .tm{font-size:12px;color:var(--muted);white-space:nowrap;}
@media (max-width:900px){.cv-grid{grid-template-columns:repeat(2,1fr);}}
/* ===== الحركة: خلفية متحركة + ظهور تدريجي + تفاعل ===== */
.stApp{background:linear-gradient(120deg,#E8EEF7 0%,#DCE7F7 35%,#E8EEF7 60%,#E3E9F8 100%);
      background-size:300% 300%;animation:cvBg 22s ease infinite;}
.stApp::before,.stApp::after{content:"";position:fixed;border-radius:50%;filter:blur(70px);z-index:0;
      pointer-events:none;opacity:.55;}
.stApp::before{width:520px;height:520px;background:radial-gradient(circle,#93C5FD,transparent 70%);
      top:-120px;inset-inline-start:-140px;animation:cvFloatA 26s ease-in-out infinite;}
.stApp::after{width:460px;height:460px;background:radial-gradient(circle,#BAE6FD,transparent 70%);
      bottom:-140px;inset-inline-end:-120px;animation:cvFloatB 30s ease-in-out infinite;}
[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:transparent;position:relative;z-index:1;}
.st-key-hero{background-size:200% 200%!important;animation:cvBg 14s ease infinite,cvRise .6s ease both;}
.st-key-hero::before{animation:cvFloatA 18s ease-in-out infinite;}
.st-key-hero::after{content:"";position:absolute;width:180px;height:180px;border-radius:50%;
      background:rgba(56,189,248,.10);inset-inline-end:280px;bottom:-90px;animation:cvFloatB 16s ease-in-out infinite;}
.st-key-topnav{animation:cvDrop .5s ease both;}
.st-key-panel,.st-key-chk_header,.cv-card,.cv-mini,.cv-info{animation:cvRise .55s ease both;}
.cv-grid .cv-card:nth-child(2){animation-delay:.06s}.cv-grid .cv-card:nth-child(3){animation-delay:.12s}
.cv-grid .cv-card:nth-child(4){animation-delay:.18s}
.cv-card{transition:transform .2s ease,box-shadow .2s ease;}
.cv-card:hover{transform:translateY(-3px);box-shadow:0 12px 28px rgba(11,27,63,.10);}
.cv-progress div{animation:cvGrow 1.1s cubic-bezier(.2,.8,.2,1) both;}
.cv-chk-row{animation:cvRise .4s ease both;}
.cv-logo{animation:cvPulse 3.5s ease-in-out infinite;}
.stButton button[kind="primary"]{transition:transform .15s ease,filter .15s ease;}
.stButton button[kind="primary"]:hover{transform:translateY(-1px);}
@keyframes cvBg{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes cvFloatA{0%,100%{transform:translate(0,0)}50%{transform:translate(60px,40px)}}
@keyframes cvFloatB{0%,100%{transform:translate(0,0)}50%{transform:translate(-50px,-35px)}}
@keyframes cvRise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@keyframes cvDrop{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:none}}
@keyframes cvGrow{from{width:0}}
@keyframes cvPulse{0%,100%{box-shadow:0 0 0 0 rgba(56,189,248,.45)}50%{box-shadow:0 0 0 8px rgba(56,189,248,0)}}
/* ===== لمسات احترافية: شعار الجامعة + تحسينات عامة ===== */
::selection{background:rgba(37,99,235,.18);}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-thumb{background:#C7D4E8;border-radius:10px;
      border:2px solid #E8EEF7}::-webkit-scrollbar-track{background:transparent}
.st-key-topnav{position:sticky;top:10px;z-index:50;backdrop-filter:blur(10px);
      background:linear-gradient(90deg,rgba(11,27,63,.96),rgba(19,48,107,.96))!important;
      border:1px solid rgba(255,255,255,.08);padding:12px 22px!important;}
.cv-uni-logo{height:46px;width:auto;flex-shrink:0;filter:drop-shadow(0 2px 6px rgba(0,0,0,.25));}
.cv-sep{width:1px;height:34px;background:rgba(255,255,255,.18);flex-shrink:0;}
.cv-pmau{font-weight:700;font-size:13px;letter-spacing:1.5px;color:#7DD3FC;background:rgba(56,189,248,.12);
      border:1px solid rgba(125,211,252,.3);padding:4px 10px;border-radius:8px;flex-shrink:0;}
.cv-brand .cv-logo{width:36px;height:36px;font-size:13px;border-radius:10px;}
.cv-hero-tags{display:flex;flex-wrap:wrap;gap:8px;}
.cv-tag-hero.uni{background:rgba(11,27,63,.28);}
.cv-tag-hero.uni b{color:#7DD3FC;letter-spacing:1px;margin-inline-end:4px;}
.cv-hero-title{font-size:38px!important;letter-spacing:-.3px;}
.cv-hero-cta{display:flex;flex-wrap:wrap;align-items:center;gap:10px;}
.cv-btn-white{display:inline-flex!important;align-items:center;gap:8px;box-shadow:0 8px 20px rgba(0,0,0,.18);
      transition:transform .15s ease,box-shadow .15s ease;}
.cv-btn-white:hover{transform:translateY(-2px);box-shadow:0 12px 26px rgba(0,0,0,.24);}
.cv-stat{font-size:12.5px;color:#E0F2FE;padding:7px 12px;border-radius:999px;background:rgba(255,255,255,.08);
      border:1px solid rgba(255,255,255,.14);}
.st-key-panel,.st-key-chk_header{position:relative;overflow:hidden;border-radius:20px!important;}
.st-key-panel::before,.st-key-chk_header::before{content:"";position:absolute;top:0;left:0;right:0;height:4px;
      background:linear-gradient(90deg,var(--sky),var(--blue),var(--navy2));}
[data-testid="stFileUploaderDropzone"]{transition:border-color .15s ease,background .15s ease;}
[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--blue)!important;background:#EFF6FF!important;}
.stTextInput input:focus,[data-baseweb="select"]>div:focus-within{border-color:var(--blue2)!important;
      box-shadow:0 0 0 3px rgba(37,99,235,.15)!important;}
.stTabs [data-baseweb="tab-list"]{background:#fff;border:1px solid var(--line);border-radius:14px;padding:6px;
      gap:4px;box-shadow:var(--shadow);}
.stTabs [data-baseweb="tab"]{border-radius:10px;padding:8px 16px;}
.stTabs [aria-selected="true"]{background:var(--soft);}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none;}
.cv-grid .cv-card{position:relative;overflow:hidden;}
.cv-grid .cv-card::after{content:"";position:absolute;bottom:0;inset-inline-start:0;width:42%;height:3px;
      background:linear-gradient(90deg,var(--blue),var(--sky));border-radius:3px;}
.cv-card{border-radius:18px;}
.cv-footer{margin:34px 0 10px;padding:22px 26px;border-radius:20px;color:#DBEAFE;display:flex;flex-wrap:wrap;
      align-items:center;justify-content:space-between;gap:18px;
      background:linear-gradient(135deg,var(--navy2),var(--navy));box-shadow:0 10px 30px rgba(11,27,63,.18);
      animation:cvRise .6s ease both;}
.cv-f-main{display:flex;align-items:center;gap:16px;}
.cv-f-main img{height:72px;width:auto;}
.cv-f-main b{display:block;color:#fff;font-size:15px;}
.cv-f-main span{font-size:12.5px;color:#BFDBFE;}
.cv-f-meta{display:flex;flex-direction:column;gap:4px;font-size:12.5px;color:#BFDBFE;text-align:end;}
@media (max-width:900px){.cv-uni-logo{height:36px}.cv-hero-title{font-size:28px!important}
      .cv-f-meta{text-align:start}}
/* ===== البانر: تصميم جديد بألوان شعار الجامعة (كحلي + فيروزي + بنفسجي) ===== */
.st-key-hero{background:
      radial-gradient(520px 320px at 88% -10%,rgba(31,181,198,.38),transparent 70%),
      radial-gradient(460px 300px at 8% 115%,rgba(109,75,196,.42),transparent 70%),
      radial-gradient(rgba(255,255,255,.07) 1px,transparent 1.4px) 0 0/22px 22px,
      linear-gradient(135deg,#0B1B3F 0%,#102A5C 55%,#1A2468 100%)!important;
      background-size:auto,auto,22px 22px,auto!important;animation:cvRise .6s ease both!important;
      border:1px solid rgba(125,227,238,.18);box-shadow:0 18px 44px rgba(11,27,63,.28),inset 0 1px 0 rgba(255,255,255,.08);
      padding:42px 44px!important;}
.st-key-hero::before{width:240px!important;height:240px!important;top:-120px!important;
      background:conic-gradient(from 200deg,rgba(31,181,198,.0),rgba(31,181,198,.35),rgba(109,75,196,.35),rgba(31,181,198,0))!important;
      filter:blur(30px);}
.st-key-hero::after{background:rgba(109,75,196,.18)!important;filter:blur(20px);}
.cv-tag-hero{background:rgba(31,181,198,.14)!important;border:1px solid rgba(125,227,238,.32)!important;color:#CFFAFE!important;}
.cv-tag-hero.uni{background:rgba(109,75,196,.18)!important;border-color:rgba(167,139,250,.35)!important;color:#EDE9FE!important;}
.cv-hero-title{color:#fff!important;font-size:40px!important;text-shadow:0 4px 24px rgba(31,181,198,.25);}
.cv-hero-title::after{content:"";display:block;width:84px;height:4px;border-radius:4px;margin-top:12px;
      background:linear-gradient(90deg,#1FB5C6,#6D4BC4);}
.cv-hero-sub{color:#C7D2FE!important;max-width:640px;}
.cv-btn-white{background:linear-gradient(90deg,#14B8A6,#22D3EE)!important;color:#06263A!important;font-weight:700!important;
      box-shadow:0 10px 24px rgba(20,184,166,.35)!important;}
.cv-btn-white:hover{box-shadow:0 14px 30px rgba(20,184,166,.45)!important;}
.cv-stat{background:rgba(255,255,255,.06)!important;border:1px solid rgba(125,227,238,.25)!important;color:#E0F7FA!important;}
.cv-steps{position:relative;background:linear-gradient(160deg,rgba(255,255,255,.10),rgba(255,255,255,.03))!important;
      border:1px solid rgba(125,227,238,.22)!important;border-radius:20px!important;padding:22px 24px!important;
      backdrop-filter:blur(8px);box-shadow:0 12px 30px rgba(0,0,0,.18);}
.cv-steps h4{color:#7DE3EE!important;letter-spacing:.3px;}
.cv-step{position:relative;margin-bottom:16px!important;}
.cv-step:not(:last-child)::after{content:"";position:absolute;inset-inline-start:14px;top:32px;width:2px;height:calc(100% - 14px);
      background:linear-gradient(180deg,rgba(31,181,198,.6),rgba(109,75,196,.5));}
.cv-step i{background:linear-gradient(135deg,#1FB5C6,#6D4BC4)!important;color:#fff!important;
      box-shadow:0 0 0 4px rgba(31,181,198,.15);}
.cv-step span{color:#C7D2FE!important;}
/* ===== عدّاد الزوار ===== */
.cv-visits{display:inline-flex;align-items:center;gap:7px;align-self:flex-end;font-size:12.5px;color:#E0F7FA;
      background:rgba(31,181,198,.14);border:1px solid rgba(125,227,238,.3);padding:5px 12px;border-radius:999px;
      font-family:'Readex Pro',sans-serif;}
.cv-visits b{color:#fff;font-weight:700;}
.cv-visits span{opacity:.5;}
.cv-visits i{width:7px;height:7px;border-radius:50%;background:#22D3EE;box-shadow:0 0 0 3px rgba(34,211,238,.25);
      animation:dmBlinkV 1.6s ease-in-out infinite;}
@keyframes dmBlinkV{50%{opacity:.35}}
.st-key-topnav .cv-visits{align-self:auto;white-space:nowrap;font-size:11.5px;padding:5px 10px;}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;}}
</style>
""")
if RTL:
    html_block("""<style>
[data-testid="stMain"],.main{direction:rtl;text-align:right;}
.cv-tag{margin:0 6px 6px 0;}
.st-key-nav_lang{justify-content:flex-start;}
</style>""")


# ================= أيقونات =================
def svg(*paths, size=20) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            + "".join(f'<path d="{p}"/>' for p in paths) + "</svg>")


P = {
    "user": ("M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2", "M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"),
    "brief": ("M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16",
              "M20 6H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2z"),
    "list": ("M8 6h13", "M8 12h13", "M8 18h13", "M3 6h.01", "M3 12h.01", "M3 18h.01"),
    "target": ("M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z", "M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12z",
               "M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"),
    "spark": ("M12 3l1.9 5.8L20 10l-6.1 1.2L12 17l-1.9-5.8L4 10l6.1-1.2z",),
    "book": ("M4 19.5A2.5 2.5 0 0 1 6.5 17H20", "M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"),
    "upload": ("M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", "M17 8l-5-5-5 5", "M12 3v12"),
    "check": ("M20 6 9 17l-5-5",),
    "x": ("M18 6 6 18", "M6 6l12 12"),
    "minus": ("M5 12h14",),
    "clock": ("M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z", "M12 6v6l4 2"),
    "info": ("M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z", "M12 16v-4", "M12 8h.01"),
    "arrow": ("M7 17 17 7", "M7 7h10v10"),
}


def icon(name, size=20):
    return svg(*P[name], size=size)


def title_row(text: str, ic: str) -> str:
    return f'<div class="cv-title-row"><div class="cv-ic">{icon(ic, 18)}</div><div class="cv-h3">{esc(text)}</div></div>'


def field_label(text: str):
    html_block(f'<div class="cv-field">{esc(text)}</div>')


def chips(links: dict) -> str:
    return '<div class="cv-chips">' + "".join(
        f'<a class="cv-chip" href="{esc(u)}" target="_blank" rel="noopener">{esc(n)}{icon("arrow", 14)}</a>'
        for n, u in links.items()) + "</div>"


# ================= عدّاد الزوار (مرة واحدة لكل جلسة) =================
if "visit_counted" not in st.session_state:
    try:
        visitors.register_visit()
    except OSError:
        pass
    st.session_state.visit_counted = True
VISITS = visitors.get_counts()


def visitors_badge() -> str:
    """العداد يظهر بالإنجليزية دائماً، بغض النظر عن لغة الواجهة."""
    return (f'<div class="cv-visits" dir="ltr"><i></i><b>{VISITS["total"]:,}</b> Visitors'
            f'<span>·</span>Today <b>{VISITS["today"]:,}</b></div>')


# ================= شريط التنقل العلوي =================
with st.container(key="topnav"):
    c_brand, c_nav, c_lang = st.columns([1.6, 1.6, 1], vertical_alignment="center")
    with c_brand:
        html_block(f'<div class="cv-brand"><img class="cv-uni-logo" src="{LOGO_MARK}" alt="{esc(T("uni_name"))}">'
                   f'<span class="cv-sep"></span><div class="cv-logo">CV</div><div><b>CV Agent</b>'
                   f'<small>{esc(T("brand_sub"))}</small></div></div>')
    with c_nav:
        page = st.segmented_control("page", [0, 1], default=st.session_state.page, key="nav_page",
                                    format_func=lambda i: T("nav")[i], label_visibility="collapsed")
        if page is not None and page != st.session_state.page:
            st.session_state.page = page
            st.rerun()
    with c_lang:
        lang = st.segmented_control("lang", ["ar", "en"], default=LANG, key="nav_lang",
                                    format_func={"ar": "عربي", "en": "EN"}.get, label_visibility="collapsed")
        if lang and lang != LANG:
            st.session_state.lang = lang
            st.rerun()

def _secret(name: str) -> str:
    """المفتاح من متغيرات البيئة (Colab) أو من Secrets في Streamlit Community Cloud."""
    value = os.environ.get(name, "")
    if not value:
        try:
            value = st.secrets.get(name, "")
        except Exception:  # noqa: BLE001 — لا يوجد ملف secrets محلياً
            value = ""
    return value


env_key = _secret("OPENAI_API_KEY")






# ================= صفحة التحليل =================
def analysis_page():
    # ---- البانر ----
    with st.container(key="hero"):
        c_text, c_steps = st.columns([2.2, 1], gap="large", vertical_alignment="center")
        with c_text:
            html_block(f'<div class="cv-hero-tags"><span class="cv-tag-hero">{icon("spark", 14)}{esc(T("tag"))}</span>'
                       f'<span class="cv-tag-hero uni">{esc(T("college"))}</span></div>'
                       f'<div class="cv-hero-title">{esc(T("title"))}</div>'
                       f'<p class="cv-hero-sub">{esc(T("subtitle_hero"))}</p>'
                       f'<div class="cv-hero-cta"><a class="cv-btn-white" href="#start">{icon("upload", 16)}'
                       f'{esc(T("cta_upload"))}</a>' + "".join(f'<span class="cv-stat">{esc(s)}</span>'
                                                            for s in T("hero_stats")) + '</div>')
        with c_steps:
            html_block(f'<div class="cv-steps"><h4>{esc(T("how_title"))}</h4>' + "".join(
                f'<div class="cv-step"><i>{i + 1}</i><div><b>{esc(a)}</b><span>{esc(b)}</span></div></div>'
                for i, (a, b) in enumerate(T("steps"))) + "</div>")

    # ---- لوحة التحكم ----
    html_block('<div id="start"></div>')
    with st.container(key="panel"):
        html_block(title_row(T("panel_title"), "upload"))
        api_key = env_key
        if not api_key:
            field_label(T("api_key_label"))
            api_key = st.text_input("api_key", type="password", key="api_key", label_visibility="collapsed")
        model = DEFAULT_MODEL  # النموذج ثابت (يتغير فقط من Colab Secrets عبر OPENAI_MODEL) ولا يظهر للمستخدم
        c_up, c_city, c_btn = st.columns([3, 1.4, 1.1], vertical_alignment="bottom")
        # تسميات ثابتة للعناصر (label_visibility) حتى لا تُمسح قيمها عند تبديل اللغة
        with c_up:
            field_label(T("upload"))
            uploaded = st.file_uploader("cv_file", type=["pdf", "docx"], key="cv_file", label_visibility="collapsed")
        with c_city:
            field_label(T("city"))
            city = st.selectbox("city", list(CITIES.keys()), key="city", label_visibility="collapsed",
                                format_func=lambda k: city_name(k, LANG))
        with c_btn:
            clicked = st.button(T("analyze"), type="primary", disabled=not (uploaded and api_key),
                                use_container_width=True)

    if uploaded:
        data = uploaded.getvalue()
        run_key = (hashlib.sha256(data).hexdigest(), city, model, LANG)
        if clicked:
            try:
                cv_text = extract_text(data, uploaded.name)
                with st.status(T("analyzing"), expanded=True) as status:
                    result = analyze_cv(cv_text, city=city, lang=LANG,
                                        llm=build_llm(api_key=api_key, model=model), on_step=status.write)
                    status.update(label=T("done"), state="complete", expanded=False)
                st.session_state.update(result=result, cv_text=cv_text, run_key=run_key)
            except CVProcessingError as e:
                st.error(f"❌ {e.message(LANG)}")
            except Exception as e:  # noqa: BLE001
                name = type(e).__name__
                if "Authentication" in name:
                    st.error(f"❌ {T('err_auth')}")
                elif "RateLimit" in name:
                    st.error(f"❌ {T('err_rate')}")
                elif "NotFound" in name:
                    st.error(f"❌ {T('err_model', model=model)}")
                else:
                    st.error(f"❌ {T('err_unexpected')} {e}")
        stored = st.session_state.get("run_key")
        if st.session_state.get("result") and stored != run_key:
            st.info(T("stale_file") if stored[0] != run_key[0] else T("stale_settings"))

    r = st.session_state.get("result")
    if r:
        show_results(r)


def show_results(r):
    prio, level = t(LANG, "priority"), t(LANG, "level")
    c, g = r.candidate, r.skill_gap
    report_bytes = build_markdown_report(r).encode("utf-8")
    if r.truncated:
        st.warning(T("truncated"))

    top = f"{r.jobs.jobs[0].match_percentage}%" if r.jobs.jobs else "—"
    metrics = [("user", T("m_name"), c.name, ""), ("brief", T("m_years"), f"{c.experience_years:g}", ""),
               ("list", T("m_skills"), len(c.extracted_skills), ""), ("target", T("m_top"), top, " accent")]
    html_block('<div class="cv-grid">' + "".join(
        f'<div class="cv-card cv-metric"><div class="cv-ic{cls}">{icon(ic)}</div><div>'
        f'<div class="cv-label">{esc(l)}</div><div class="cv-value{cls}">{esc(v)}</div></div></div>'
        for ic, l, v, cls in metrics) + "</div>")

    def gap_html() -> str:
        return "".join(
            f'<div class="cv-gap-item"><span class="cv-badge {s.priority}">{esc(prio[s.priority])}</span>'
            f'<div><b>{esc(s.skill)}</b><span class="cv-sub">{esc(s.reason)}</span></div></div>'
            for s in g.missing_skills)

    tab_profile, tab_gap, tab_jobs, tab_courses, tab_cv = st.tabs(T("tabs"))

    with tab_profile:
        html_block(
            '<div class="cv-card">'
            f'<div class="cv-label">{esc(T("current_title"))}</div><div class="cv-h3">{esc(c.current_title)}</div><br>'
            f'<div class="cv-label">{esc(T("field"))}</div><div class="cv-h3">{esc(c.field)}</div><br>'
            f'<div class="cv-label">{esc(T("education"))}</div><div class="cv-h3">{esc(c.education)}</div>'
            f'<p class="cv-text">{esc(c.summary)}</p></div>'
            f'<div class="cv-card">{title_row(T("skills"), "list")}'
            + "".join(f'<span class="cv-tag">{esc(s)}</span>' for s in c.extracted_skills) + "</div>")
        with st.expander(T("extracted_text")):
            st.text(st.session_state.get("cv_text", ""))

    with tab_gap:
        html_block(f'<div class="cv-card">{title_row(T("gap_heading"), "target")}{gap_html()}</div>'
                   f'<div class="cv-card">{title_row(T("tips_heading"), "spark")}<ul class="cv-list">'
                   + "".join(f"<li>{esc(x)}</li>" for x in g.recommendations_to_improve) + "</ul></div>")

    with tab_jobs:
        col_jobs, col_side = st.columns([2.5, 1], gap="large")
        with col_jobs:
            html_block(f'<div class="cv-h2">{esc(T("jobs_heading", city=city_name(r.city, LANG)))}</div>'
                       f'<p class="cv-note">{esc(T("jobs_note"))}</p>')
            for j in r.jobs.jobs:
                sub = j.job_title_local if r.lang == "ar" else f'{city_name(r.city, "en")}, Saudi Arabia'
                html_block(
                    '<div class="cv-card"><div class="cv-top">'
                    f'<div><div class="cv-h3">{esc(j.job_title)}</div><div class="cv-sub">{esc(sub)}</div></div>'
                    f'<div class="cv-match"><b>{j.match_percentage}%</b><span>{esc(T("match"))}</span></div></div>'
                    f'<div class="cv-progress"><div style="width:{j.match_percentage}%"></div></div>'
                    f'<p class="cv-text">{esc(j.why_fit)}</p>'
                    f'<div class="cv-sub">{esc(T("employers"))} {esc(", ".join(j.example_employers))}</div>'
                    f'{chips(job_links(j.job_title, r.city, LANG))}</div>')
        with col_side:
            html_block(f'<div class="cv-card">{title_row(T("gap_heading"), "target")}{gap_html()}</div>')
            st.download_button(f"⬇ {T('download')}", data=report_bytes, file_name="cv_report.md",
                               mime="text/markdown", key="dl_jobs")

    with tab_courses:
        html_block(f'<div style="margin-top:12px">{title_row(T("courses_heading"), "book")}</div>')
        for co in r.courses.courses:
            html_block(
                '<div class="cv-card"><div class="cv-top">'
                f'<div><div class="cv-h3">{esc(co.course_name)}</div>'
                f'<div class="cv-sub">{esc(T("covers"))} {esc(co.target_skill)}</div></div>'
                f'<span class="cv-badge level">{esc(level[co.level])}</span></div>'
                f'{chips(course_links(co.course_name))}</div>')

    with tab_cv:
        imp = r.improved_cv
        st.text_area(T("summary_label"), imp.improved_summary, height=150)
        html_block(
            f'<div class="cv-card">{title_row(T("bullets_heading"), "list")}'
            f'<p class="cv-note">{esc(T("bullets_note"))}</p><ul class="cv-list" dir="auto">'
            + "".join(f'<li dir="auto">{esc(p)}</li>' for p in imp.improved_bullet_points) + "</ul></div>"
            f'<div class="cv-card">{title_row(T("ats_heading"), "spark")}<ul class="cv-list">'
            + "".join(f"<li>{esc(x)}</li>" for x in imp.ats_tips) + "</ul></div>")
        st.download_button(f"⬇ {T('download')}", data=report_bytes, file_name="cv_report.md",
                           mime="text/markdown", key="dl_cv")


# ================= صفحة فحص النظام =================
def check_page():
    model = DEFAULT_MODEL
    api_key = env_key or st.session_state.get("api_key", "")
    with st.container(key="chk_header"):
        c_title, c_btn = st.columns([4, 1], vertical_alignment="center")
        with c_title:
            html_block(f'<p class="cv-chk-title">{esc(T("chk_title"))}</p>'
                       f'<p class="cv-sub" style="margin:4px 0 0">{esc(T("chk_sub"))}</p>')
        with c_btn:
            run = st.button(T("chk_run"), type="primary", use_container_width=True)
        if run:
            with st.spinner(T("chk_run") + "…"):
                st.session_state.checks = checks.run_all(LANG, api_key=api_key, model=model)
        results = st.session_state.get("checks")
        if results:
            passed = sum(r.status == "pass" for r in results)
            failed = sum(r.status == "fail" for r in results)
            total_s = sum(r.seconds for r in results)
            stats = [(T("chk_total"), len(results), "var(--ink)"), (T("chk_passed"), passed, "#15803D"),
                     (T("chk_failed"), failed, "#DC2626"), (T("chk_time"), f'{total_s:.2f} {T("chk_sec")}', "var(--blue)")]
            bar_color = "linear-gradient(90deg,var(--blue),#22C55E)" if not failed else "linear-gradient(90deg,#F59E0B,#DC2626)"
            html_block('<div class="cv-grid" style="margin:18px 0 0">' + "".join(
                f'<div class="cv-mini"><div class="cv-label">{esc(l)}</div>'
                f'<div class="cv-value" style="color:{col}">{esc(v)}</div></div>' for l, v, col in stats)
                + f'</div><div class="cv-chk-bar" style="background:{bar_color}"></div>')

    results = st.session_state.get("checks")
    if not results:
        html_block(f'<div class="cv-info">{icon("info")}<span>{esc(T("chk_empty"))}</span></div>')
    else:
        names, labels = T("chk_names"), T("chk_status")
        icons = {"pass": "check", "fail": "x", "skip": "minus"}
        html_block('<div class="cv-card" style="padding:8px 24px;margin-top:20px">' + "".join(
            f'<div class="cv-chk-row"><div class="st {r.status}">{icon(icons[r.status], 18)}</div>'
            f'<div class="tx"><b>{i + 1}. {esc(names[r.key])}</b><span class="cv-sub">{esc(r.detail)}</span></div>'
            f'<span class="tm">{icon("clock", 14)} {r.seconds:.2f} {esc(T("chk_sec"))}</span>'
            f'<span class="cv-badge {r.status}">{esc(labels[r.status])}</span></div>'
            for i, r in enumerate(results)) + "</div>")
    html_block(f'<div class="cv-info">{icon("info")}<span>{esc(T("chk_note"))}</span></div>')


# ================= التذييل =================
def footer():
    html_block(f'<div class="cv-footer"><div class="cv-f-main"><img src="{LOGO_WHITE}" alt="{esc(T("uni_name"))}">'
               f'<div><b>{esc(T("uni_name"))}</b><span>{esc(T("college"))}</span></div></div>'
               f'<div class="cv-f-meta">{visitors_badge()}<span>{esc(T("footer_project"))}</span>'
               f'<span>{esc(T("footer_sup"))} · {esc(T("footer_year"))}</span></div></div>')


if st.session_state.page == 1:
    check_page()
else:
    analysis_page()
footer()
