import streamlit as st
import hashlib
import json
import re

from google import genai
from google.genai import types

from knowledge_base import get_rule_by_contamination

MODEL = "gemini-3.6-flash"

# ต่ำกว่าค่านี้ หรือโมเดลตอบ unknown -> ไม่แสดงคำแนะนำ ให้ถ่ายรูปใหม่
CONFIDENCE_THRESHOLD = 0.70

VALID_CATEGORIES = {"recyclable", "general", "organic", "hazardous", "unknown"}
VALID_CONTAMINATION = {"low", "medium", "high"}


@st.cache_resource
def get_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


client = get_client()


# =========================
# Parse ผลจาก Gemini อย่างปลอดภัย
# =========================
def parse_vision_response(text):
    """
    แปลงข้อความที่โมเดลตอบเป็น dict ที่ครบทุกฟิลด์เสมอ
    คืน None ถ้าอ่าน JSON ไม่ได้เลย
    """
    if not text:
        return None

    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    category = str(data.get("category", "unknown")).strip().lower()
    if category not in VALID_CATEGORIES:
        category = "unknown"

    contamination = str(data.get("contamination", "low")).strip().lower()
    if contamination not in VALID_CONTAMINATION:
        contamination = "low"

    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    if 1.0 < confidence <= 100.0:
        confidence = confidence / 100.0

    confidence = max(0.0, min(1.0, confidence))

    return {
        "item": str(data.get("item", "ไม่ทราบ")),
        "category": category,
        "contamination": contamination,
        "confidence": confidence,
    }


def needs_retake(vision_result):
    """True ถ้าควรให้ผู้ใช้ถ่ายรูปใหม่ แทนที่จะแสดงคำแนะนำ"""
    return (
        vision_result["category"] == "unknown"
        or vision_result["confidence"] < CONFIDENCE_THRESHOLD
    )


# =========================
# โควตาเต็ม + แคชผลต่อรูป
# =========================
class QuotaExceeded(Exception):
    """โควตา Gemini เต็ม (ต่อนาทีหรือต่อวัน)"""


def is_quota_error(error):
    msg = str(error).upper()
    return (
        "429" in msg
        or "RESOURCE_EXHAUSTED" in msg
        or "QUOTA" in msg
    )


@st.cache_resource
def get_result_cache():
    # เก็บเฉพาะผลลัพธ์ ไม่เก็บรูป จนกว่าแอปจะรีสตาร์ต
    return {}


def analyze_waste_cached(image_bytes, mime_type):
    """
    คืน (ผลลัพธ์, มาจากแคชหรือไม่)
    รูปเดิม (ไบต์ตรงกัน) จะไม่เรียก Gemini ซ้ำ จึงไม่ใช้โควตา
    ไม่แคชผลที่อ่านไม่ได้ (None)
    """
    key = hashlib.sha256(image_bytes).hexdigest()
    cache = get_result_cache()

    if key in cache:
        return cache[key], True

    result = analyze_waste(image_bytes, mime_type)

    if result is not None:
        cache[key] = result

    return result, False


# =========================
# Gemini Vision
# =========================
def analyze_waste(image_bytes, mime_type):

    prompt = """
    วิเคราะห์รูปขยะนี้และตอบเป็น JSON เท่านั้น

    {
      "item": "ชื่อสิ่งของ",
      "category": "recyclable/general/organic/hazardous/unknown",
      "contamination": "low/medium/high",
      "confidence": 0.0
    }

    ให้พิจารณาด้วยว่าวัตถุนั้นมีเศษอาหาร ของเหลว
    หรือสิ่งปนเปื้อนติดอยู่หรือไม่

    ถ้าในรูปไม่มีขยะที่ชัดเจน ภาพเบลอ มืดเกินไป
    หรือไม่แน่ใจว่าเป็นอะไร ให้ตอบ category เป็น "unknown"
    และให้ confidence ต่ำ

    ห้ามใส่ข้อความอื่นนอก JSON
    """

    try:
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
    except Exception as e:
        if is_quota_error(e):
            raise QuotaExceeded() from e
        raise

    return parse_vision_response(resp.text)


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

                try:
                    vision_result, from_cache = analyze_waste_cached(
                        image_bytes,
                        uploaded_file.type
                    )
                except QuotaExceeded:
                    st.warning(
                        "⏳ โควตา AI เต็มชั่วคราว "
                        "กรุณารอสักครู่แล้วลองใหม่อีกครั้ง "
                        "หากโควตารายวันเต็ม กรุณาลองใหม่ภายหลัง"
                    )
                    st.stop()
                except Exception as e:
                    st.error(
                        "ระบบขัดข้องชั่วคราว กรุณาลองใหม่อีกครั้ง "
                        f"({type(e).__name__})"
                    )
                    st.stop()

            if from_cache:
                st.caption("ผลจากการวิเคราะห์รูปนี้ก่อนหน้า (ไม่ใช้โควตา)")

            if vision_result is None:

                st.error(
                    "ไม่สามารถอ่านผลจาก AI ได้ กรุณาลองใหม่อีกครั้ง"
                )
                st.stop()

            # ---- ไม่มั่นใจ / ระบุไม่ได้ -> ไม่แสดงคำแนะนำ ----
            if needs_retake(vision_result):

                st.warning(
                    "⚠️ AI ไม่มั่นใจในภาพนี้ "
                    "กรุณาถ่ายรูปใหม่ให้เห็นสิ่งของชัดเจนขึ้น "
                    "แสงสว่างพอ และมีชิ้นเดียวในภาพ"
                )
                st.stop()

            category = vision_result["category"]
            contamination = vision_result["contamination"]
            confidence = vision_result["confidence"]

            rule = get_rule_by_contamination(
                category,
                contamination
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
