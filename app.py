import streamlit as st
import pandas as pd
import re
from PIL import Image
import io
import requests

st.set_page_config(page_title="مساعد اختبارات BA", layout="centered")

st.title("🤖 مساعد الإجابات الذكي - اختبارات BA")
st.write("ابحث عن إجابة أي سؤال بكتابته أو برفع لقطة الشاشة مباشرة!")

# قراءة قاعدة البيانات وتنظيفها
@st.cache_data
def load_data():
    df = pd.read_csv("BA_Questions.csv")
    df = df.drop_duplicates(subset=['السؤال'])
    return df

try:
    df = load_data()
except Exception as e:
    st.error("رجاءً تأكد من وجود ملف BA_Questions.csv في نفس المجلد.")
    st.stop()

# دالة ذكية لإرسال الصورة لخادم OCR خارجي سريع ومجاني ومستقر جداً
def query_ocr_api(image_bytes):
    try:
        # استخدام محرك قراءة متقدم ومجاني عبر الـ API
        api_url = "https://api-inference.huggingface.co/models/briaai/BRIA-2.3" # محرك معالجة صور سريع
        # كمحرك بديل وأسهل ومستقر 100% للغات المختلطة عبر أداة مجانية للـ OCR:
        # سنقوم هنا بالاتصال بـ خادم مجاني ومفتوح للقراءة العربية
        files = {"file": ("image.png", image_bytes, "image/png")}
        response = requests.post("https://api.ocr.space/parse/image", 
                                 files=files, 
                                 data={"apikey": "helloworld", "language": "ara"})
        
        result = response.json()
        if result and "ParsedResults" in result and len(result["ParsedResults"]) > 0:
            return result["ParsedResults"][0]["ParsedText"]
    except Exception as e:
        st.error(f"حدث بطء مؤقت في خادم القراءة: {e}")
    return ""

# خيارات الإدخال
option = st.radio("اختر طريقة البحث:", ("✍️ كتابة نص السؤال", "📸 رفع صورة السؤال"))

answer_found = False
search_query = ""

if option == "✍️ كتابة نص السؤال":
    search_query = st.text_input("أدخل الكلمات المفتاحية أو السؤال هنا:")

elif option == "📸 رفع صورة السؤال":
    uploaded_file = st.file_uploader("اختر صورة السؤال (Screenshot)...", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="الصورة المرفوعة", use_column_width=True)
        
        with st.spinner("جاري قراءة النص بدقة فائقة عبر السحابة الذكية..."):
            # تحويل الصورة إلى بايتات لإرسالها للـ API
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # استدعاء الـ API
            search_query = query_ocr_api(img_byte_arr)

if search_query:
    st.subheader("نتائج البحث المعتمدة:")
    
    # تنظيف النص المستخلص وإزالة الرموز غير المرغوبة
    search_query_cleaned = re.sub(r'[^\w\s]', ' ', search_query)
    keywords = [kw for kw in re.split(r'\s+', search_query_cleaned.strip()) if len(kw) > 2]
    
    if keywords:
        # البحث المرن في قاعدة البيانات
        results = df[df['السؤال'].str.contains('|'.join(keywords), case=False, na=False, regex=True)]
        
        if not results.empty:
            for idx, row in results.iterrows():
                st.success(f"**السؤال المستهدف:** {row['السؤال']}")
                st.info(f"🎯 **الإجابة الصحيحة:** {row['الإجابة']}")
                st.markdown("---")
            answer_found = True

    if not answer_found:
        st.warning("لم يتم العثور على إجابة مطابقة تماماً. جرب استخدام البحث النصي بكتابة كلمات مفتاحية أدق.")
