import streamlit as st
import pandas as pd
import re

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BA Smart Hub | مساعد أسئلة الجودة",
    page_icon="🔍",
    layout="centered",
)

# ─── Custom CSS (RTL + Arabic styling) ───────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');

    * { font-family: 'Cairo', sans-serif !important; }

    html, body, [class*="css"] {
        direction: rtl;
        text-align: right;
    }

    .main { background-color: #f0f4f8; }

    .stApp {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
    }

    /* Header */
    .hero-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        color: white;
        padding: 2rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(30,58,95,0.3);
    }
    .hero-header h1 { font-size: 1.8rem; font-weight: 900; margin: 0; letter-spacing: -0.5px; }
    .hero-header p  { font-size: 0.95rem; opacity: 0.85; margin: 0.4rem 0 0; }

    /* Search box */
    .stTextArea textarea {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1rem !important;
        border-radius: 10px !important;
        border: 2px solid #2d6a9f !important;
    }
    .stTextArea textarea:focus { border-color: #1e3a5f !important; box-shadow: 0 0 0 3px rgba(45,106,159,0.2) !important; }

    /* Result card */
    .result-card {
        background: white;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.9rem;
        border-right: 5px solid #2d6a9f;
        box-shadow: 0 4px 15px rgba(0,0,0,0.07);
        transition: transform 0.2s;
    }
    .result-card:hover { transform: translateX(-3px); }

    .result-card .q-label {
        font-size: 0.75rem;
        color: #6b7280;
        font-weight: 600;
        margin-bottom: 0.3rem;
        letter-spacing: 0.5px;
    }
    .result-card .q-text {
        font-size: 1rem;
        color: #1e293b;
        font-weight: 600;
        margin-bottom: 0.7rem;
        line-height: 1.6;
    }
    .answer-badge {
        display: inline-block;
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        font-size: 1rem;
        font-weight: 700;
        padding: 0.4rem 1.1rem;
        border-radius: 50px;
        box-shadow: 0 3px 10px rgba(16,185,129,0.3);
    }
    .answer-badge.alt {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        box-shadow: 0 3px 10px rgba(59,130,246,0.3);
    }

    /* Stats bar */
    .stats-bar {
        background: white;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        color: #6b7280;
        border: 1px solid #e5e7eb;
    }

    /* Radio buttons */
    .stRadio > div { flex-direction: row !important; gap: 1rem; }
    .stRadio label { font-weight: 600 !important; font-size: 0.95rem !important; }

    /* Alerts */
    .no-result {
        background: #fff7ed;
        border: 2px dashed #f97316;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        color: #9a3412;
        font-weight: 600;
        font-size: 1rem;
    }

    .ocr-result-box {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 1rem;
        color: #0c4a6e;
        font-size: 0.9rem;
    }

    /* File uploader */
    .stFileUploader { direction: rtl !important; }

    /* Divider */
    .section-label {
        font-size: 0.8rem;
        color: #9ca3af;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Load Data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path: str = "BA_Questions.csv") -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="utf-8")
    df.columns = df.columns.str.strip()
    df = df.drop_duplicates(subset=["السؤال"])
    df = df.dropna(subset=["السؤال", "الإجابة"])
    df = df.reset_index(drop=True)
    return df


# ─── Search Logic ─────────────────────────────────────────────────────────────
def clean_arabic(text: str) -> str:
    """Normalise Arabic text: strip diacritics, tashkeel, tatweel."""
    text = re.sub(r"[\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7-\u06ED]", "", text)
    text = re.sub(r"\u0640", "", text)          # tatweel
    text = re.sub(r"[أإآا]", "ا", text)
    text = re.sub(r"[ةه]", "ه", text)
    text = re.sub(r"[يىئ]", "ي", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return text.strip()


def smart_search(query: str, df: pd.DataFrame, min_match_ratio: float = 0.4) -> pd.DataFrame:
    """Keyword-based fuzzy search — returns rows where ≥ min_match_ratio of keywords match."""
    query_clean = clean_arabic(query.strip().lower())
    keywords = [k for k in query_clean.split() if len(k) > 1]
    if not keywords:
        return pd.DataFrame()

    def score_row(question: str) -> float:
        q_clean = clean_arabic(question.lower())
        hits = sum(1 for kw in keywords if kw in q_clean)
        return hits / len(keywords)

    df = df.copy()
    df["_score"] = df["السؤال"].apply(score_row)
    results = df[df["_score"] >= min_match_ratio].sort_values("_score", ascending=False)
    return results.drop(columns=["_score"])


# ─── OCR Helper ───────────────────────────────────────────────────────────────
def ocr_image(image_file) -> str:
    """Extract Arabic text from an uploaded image using pytesseract."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_file)
        text = pytesseract.image_to_string(img, lang="ara")
        return text.strip()
    except ImportError:
        return "__import_error__"
    except Exception as e:
        return f"__error__{e}"


# ─── Answer badge color ────────────────────────────────────────────────────────
def answer_class(answer: str) -> str:
    green_keywords = ["صحيحة", "right", "yes", "نعم", "جميع"]
    if any(k in answer.lower() for k in green_keywords):
        return "answer-badge"
    return "answer-badge alt"


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN UI
# ═══════════════════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div class="hero-header">
    <h1>🔍 BA Smart Hub</h1>
    <p>مساعدك الذكي للبحث في أسئلة الجودة والتشغيل</p>
</div>
""", unsafe_allow_html=True)

# Load data with error handling
try:
    df = load_data("BA_Questions.csv")
    total_q = len(df)
except FileNotFoundError:
    st.error("⚠️ لم يتم العثور على ملف البيانات `BA_Questions.csv`.\n\nتأكد من وجود الملف في نفس مجلد التطبيق.")
    st.stop()
except Exception as e:
    st.error(f"❌ خطأ في تحميل البيانات: {e}")
    st.stop()

# Stats bar
st.markdown(f"""
<div class="stats-bar">
    <span>📚 إجمالي الأسئلة: <strong>{total_q}</strong></span>
    <span>✅ جاهز للبحث</span>
</div>
""", unsafe_allow_html=True)

# ─── Input Method ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">طريقة الإدخال</div>', unsafe_allow_html=True)
input_method = st.radio(
    "",
    ["✍️ كتابة نص السؤال", "📸 رفع صورة السؤال"],
    horizontal=True,
    label_visibility="collapsed",
)

search_text = ""

# ── Mode 1: Text Input ────────────────────────────────────────────────────────
if input_method == "✍️ كتابة نص السؤال":
    st.markdown('<div class="section-label">اكتب السؤال أو كلمات مفتاحية منه</div>', unsafe_allow_html=True)
    search_text = st.text_area(
        "",
        placeholder="مثال: تسجيل مبيعات الكاش  |  صلاحية العرض  |  ويب تراكر ...",
        height=100,
        label_visibility="collapsed",
    )

# ── Mode 2: Image Upload ──────────────────────────────────────────────────────
else:
    st.markdown('<div class="section-label">ارفع صورة (Screenshot) تحتوي على نص السؤال</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "",
        type=["png", "jpg", "jpeg", "webp", "bmp"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.image(uploaded_file, caption="الصورة المرفوعة", use_container_width=True)

        with st.spinner("⏳ جاري قراءة النص من الصورة..."):
            ocr_text = ocr_image(uploaded_file)

        if ocr_text == "__import_error__":
            st.error(
                "⚠️ مكتبة `pytesseract` غير متاحة على هذا الخادم.\n\n"
                "**الحل:** ثبّت المكتبة بتشغيل:\n```\npip install pytesseract Pillow\n```\n"
                "وتأكد من تثبيت برنامج **Tesseract-OCR** على الجهاز."
            )
            st.stop()
        elif ocr_text.startswith("__error__"):
            st.error(f"❌ حدث خطأ أثناء قراءة الصورة: {ocr_text.replace('__error__','')}")
            st.stop()
        elif not ocr_text:
            st.warning("⚠️ لم يتم استخلاص أي نص من الصورة. تأكد من وضوح الصورة وأن النص ظاهر بشكل جيد.")
            st.stop()
        else:
            st.markdown(f"""
            <div class="ocr-result-box">
                <strong>📝 النص المستخلص من الصورة:</strong><br>{ocr_text}
            </div>
            """, unsafe_allow_html=True)
            search_text = ocr_text

# ─── Search & Results ─────────────────────────────────────────────────────────
if search_text and search_text.strip():
    results = smart_search(search_text, df)

    st.markdown("---")

    if results.empty:
        st.markdown("""
        <div class="no-result">
            🔎 لا توجد نتائج مطابقة<br>
            <small style="font-weight:400; font-size:0.85rem;">
                حاول تقليل الكلمات المفتاحية أو استخدم كلمات أكثر دقة من نص السؤال
            </small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-label">النتائج ({len(results)} نتيجة)</div>', unsafe_allow_html=True)
        for _, row in results.iterrows():
            badge_cls = answer_class(str(row["الإجابة"]))
            st.markdown(f"""
            <div class="result-card">
                <div class="q-label">📋 السؤال</div>
                <div class="q-text">{row["السؤال"]}</div>
                <div class="q-label">✅ الإجابة الصحيحة</div>
                <span class="{badge_cls}">{row["الإجابة"]}</span>
            </div>
            """, unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#9ca3af; font-size:0.78rem; margin-top:2rem; padding-top:1rem; border-top:1px solid #e5e7eb;">
    BA Smart Hub &nbsp;|&nbsp; أداة داخلية لدعم الموظفين
</div>
""", unsafe_allow_html=True)
