
import streamlit as st
import json
import re
from google import genai
from google.genai import types

from knowledge_base import get_rule_by_contamination


MODEL = "gemini-3.5-flash"


# -----------------------------
# Gemini Client
# -----------------------------

@st.cache_resource
def get_client():
    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


client = get_client()


# -----------------------------
# AI Vision
# -----------------------------

def analyze_waste(image_bytes, mime_type):

    prompt = """
วิเคราะห์รูปขยะนี้และตอบเป็น JSON เท่านั้น

{
  "item": "ชื่อสิ่งของ",
  "category": "recyclable/general/organic/hazardous",
  "contamination": "low/medium/high",
  "confidence": 0.0
}

ให้พิจารณาด้วยว่าวัตถุนั้นมีเศษอาหาร ของเหลว
หรือสิ่งปนเปื้อนติดอยู่หรือไม่

ห้ามใส่ข้อความอื่นนอก JSON
"""

    resp = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            ),
            prompt
        ]
    )

    match = re.search(r'\{.*\}', resp.text, re.DOTALL)

    if not match:
        return None

    return json.loads(match.group())


# -----------------------------
# Page
# -----------------------------

st.set_page_config(
    page_title="EcoScan AI",
    page_icon="♻️",
    layout="centered"
)


st.title("♻️ EcoScan AI")
st.caption("AI Waste Sorting Assistant")


uploaded_file = st.file_uploader(
    "📷 Upload waste image",
    type=["jpg", "jpeg", "png"]
)


if uploaded_file:

    st.image(
        uploaded_file,
        caption="Uploaded image",
        use_container_width=True
    )

    if st.button("🔍 Analyze", use_container_width=True):

        with st.spinner("AI is analyzing..."):

            image_bytes = uploaded_file.getvalue()

            vision_result = analyze_waste(
                image_bytes,
                uploaded_file.type
            )

        if vision_result is None:

            st.error("ไม่สามารถอ่านผลจาก AI ได้")

        else:

            category = vision_result["category"]
            contamination = vision_result["contamination"]
            confidence = vision_result["confidence"]

            # ใช้ category + contamination
            rule = get_rule_by_contamination(
                category,
                contamination
            )

            if confidence < 0.70:

                st.warning(
                    "⚠️ AI ไม่มั่นใจในภาพนี้ กรุณาถ่ายรูปใหม่"
                )

            if rule is None:

                st.error(
                    "ไม่พบข้อมูลการทิ้งสำหรับประเภทนี้"
                )

            else:

                st.divider()

                st.subheader("Result")

                st.write(
                    f"🗑️ **Item:** {vision_result['item']}"
                )

                st.write(
                    f"♻️ **Waste Type:** {rule['name']}"
                )

                st.write(
                    f"🗑️ **Disposal Bin:** {rule['bin_color']}"
                )

                st.write(
                    f"🎯 **Confidence:** {confidence * 100:.0f}%"
                )

                st.write(
                    f"💡 **Disposal Guide:** {rule['instruction']}"
                )
