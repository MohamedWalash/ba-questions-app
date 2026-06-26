import streamlit as st
import pandas as pd
import re
from PIL import Image
import numpy as np
from paddleocr import PaddleOCR  # المكتبة البديلة فائقة الدقة والخفيفة

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

# تفعيل محرك القراءة فائق السرعة والخفيف (يدعم العربية والانجليزية)
@st.cache_resource
def load_ocr_reader():
    # use_angle_cls يضمن قراءة النصوص حتى لو كانت الصورة مائلة
    return PaddleOCR(use_angle_cls=True, lang='ar', show_log=False)

ocr = load_ocr_reader()

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
        
        with st.spinner("جاري قراءة النص بدقة عالية عبر تقنية PaddleOCR..."):
            try:
                # تحويل الصورة لتوافق المكتبة
                img_np = np.array(image)
                # تنفيذ القراءة
                result = ocr.ocr(img_np, cls=True)
                
                # استخراج النصوص المكتوبة وتجميعها
                ocr_texts = []
                if result and result[0]:
                    for line in result[0]:
                        ocr_texts.append(line[1][0]) # استخراج النص فقط بدون الإحداثيات
                
                search_query = " ".join(ocr_texts)
            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الصورة: {e}")

if search_query:
    st.subheader("نتائج البحث المعتمدة:")
    
    # تنظيف النص واستخراج الكلمات المفتاحية
    keywords = [kw for kw in re.split(r'\s+', search_query.strip()) if len(kw) > 2]
    
    if keywords:
        results = df[df['السؤال'].str.contains('|'.join(keywords), case=False, na=False, regex=True)]
        
        if not results.empty:
            for idx, row in results.iterrows():
                st.success(f"**السؤال المستهدف:** {row['السؤال']}")
                st.info(f"🎯 **الإجابة الصحيحة:** {row['الإجابة']}")
                st.markdown("---")
            answer_found = True

    if not answer_found:
        st.warning("لم يتم العثور على إجابة مطابقة تماماً. جرب استخدام البحث النصي بكتابة كلمات مفتاحية أدق.")
