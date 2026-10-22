import streamlit as st
import json
import re
from google import genai
from google.genai import types

from knowledge_base import get_rule_by_contamination

MODEL = "gemini-3.6-flash"


@st.cache_resource
def get_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


client = get_client()


# =========================
# Gemini Vision
# =========================
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


# =========================
# Demo Data
# =========================
DEMO_RESULTS = {
    "ตุ๊กตา": {
        "item": "ตุ๊กตา",
        "category": "general",
        "contamination": "low",
        "confidence": 0.95
    },

    "ขวดพลาสติก": {
        "item": "ขวดพลาสติก",
        "category": "recyclable",
        "contamination": "low",
        "confidence": 0.96
    },

    "กล่องอาหารมีเศษอาหาร": {
        "item": "กล่องอาหารพลาสติก",
        "category": "recyclable",
        "contamination": "high",
        "confidence": 0.91
    },

    "เศษอาหาร": {
        "item": "เศษอาหาร",
        "category": "organic",
        "contamination": "high",
        "confidence": 0.98
    },

    "ถ่านไฟฉาย": {
        "item": "ถ่านไฟฉาย",
        "category": "hazardous",
        "contamination": "low",
        "confidence": 0.97
    }
}


# =========================
# UI
# =========================
st.set_page_config(
    page_title="EcoScan AI",
    page_icon="♻️",
    layout="centered"
)

st.title("♻️ EcoScan AI")
st.caption("AI Waste Sorting Assistant")


# Demo Mode
demo_mode = st.sidebar.toggle(
    "🧪 Demo Mode",
    value=False
)

if demo_mode:
    st.sidebar.info(
        "Demo Mode เปิดอยู่\n"
        "ระบบจะไม่เรียก Gemini API"
    )


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

    if demo_mode:

        demo_choice = st.selectbox(
            "เลือกตัวอย่างสำหรับ Demo",
            list(DEMO_RESULTS.keys())
        )

        if st.button(
            "🔍 Analyze",
            use_container_width=True
        ):

            vision_result = DEMO_RESULTS[demo_choice]

            category = vision_result["category"]
            contamination = vision_result["contamination"]
            confidence = vision_result["confidence"]

            rule = get_rule_by_contamination(
                category,
                contamination
            )

            st.success("🧪 Demo Result")

            st.divider()

            st.subheader("Result")

            st.write(
                f"🗑️ **Item:** "
                f"{vision_result['item']}"
            )

            st.write(
                f"♻️ **Waste Type:** "
                f"{rule['name']}"
            )

            st.write(
                f"🗑️ **Disposal Bin:** "
                f"{rule['bin_color']}"
            )

            st.write(
                f"🎯 **Confidence:** "
                f"{confidence * 100:.0f}%"
            )

            st.write(
                f"💡 **Disposal Guide:** "
                f"{rule['instruction']}"
            )

    else:

        if st.button(
            "🔍 Analyze",
            use_container_width=True
        ):

            with st.spinner(
                "AI is analyzing..."
            ):

                image_bytes = uploaded_file.getvalue()

                vision_result = analyze_waste(
                    image_bytes,
                    uploaded_file.type
                )

            if vision_result is None:

                st.error(
                    "ไม่สามารถอ่านผลจาก AI ได้"
                )

            else:

                category = vision_result["category"]
                contamination = vision_result["contamination"]
                confidence = vision_result["confidence"]

                rule = get_rule_by_contamination(
                    category,
                    contamination
                )

                if confidence < 0.70:

                    st.warning(
                        "⚠️ AI ไม่มั่นใจในภาพนี้ "
                        "กรุณาถ่ายรูปใหม่"
                    )

                if rule is None:

                    st.error(
                        "ไม่พบข้อมูลการทิ้งสำหรับประเภทนี้"
                    )

                else:

                    st.divider()

                    st.subheader("Result")

                    st.write(
                        f"🗑️ **Item:** "
                        f"{vision_result['item']}"
                    )

                    st.write(
                        f"♻️ **Waste Type:** "
                        f"{rule['name']}"
                    )

                    st.write(
                        f"🗑️ **Disposal Bin:** "
                        f"{rule['bin_color']}"
                    )

                    st.write(
                        f"🎯 **Confidence:** "
                        f"{confidence * 100:.0f}%"
                    )

                    st.write(
                        f"💡 **Disposal Guide:** "
                        f"{rule['instruction']}"
                    )
