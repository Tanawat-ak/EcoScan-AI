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
