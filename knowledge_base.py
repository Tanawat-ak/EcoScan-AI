
waste_rules = [
    {
        "category": "recyclable",
        "name": "ขยะรีไซเคิล",
        "bin_color": "🟡 สีเหลือง",
        "items": [
            "ขวดพลาสติก",
            "แก้วพลาสติก",
            "กระป๋องอลูมิเนียม",
            "กระดาษสะอาด",
            "กล่องกระดาษสะอาด",
            "ภาชนะพลาสติกที่สะอาด"
        ],
        "instruction": "เทของเหลวออกและทำความสะอาดเบื้องต้นก่อนทิ้ง"
    },
    {
        "category": "general",
        "name": "ขยะทั่วไป",
        "bin_color": "🔵 สีฟ้า",
        "items": [
            "ตุ๊กตา",
            "ของเล่น",
            "ทิชชู่ใช้แล้ว",
            "ซองอาหาร",
            "พลาสติกที่ปนเปื้อนอาหารอย่างหนัก"
        ],
        "instruction": "ทิ้งลงถังขยะทั่วไป"
    },
    {
        "category": "organic",
        "name": "ขยะอินทรีย์",
        "bin_color": "🟢 สีเขียว",
        "items": [
            "เศษอาหาร",
            "เปลือกผลไม้",
            "เศษผัก",
            "อาหารเหลือ"
        ],
        "instruction": "แยกเศษอาหารและทิ้งลงถังขยะอินทรีย์"
    },
    {
        "category": "hazardous",
        "name": "ขยะอันตราย",
        "bin_color": "🔴 สีแดง",
        "items": [
            "ถ่านไฟฉาย",
            "แบตเตอรี่",
            "หลอดไฟ",
            "ภาชนะสารเคมี"
        ],
        "instruction": "ทิ้งในจุดหรือถังสำหรับขยะอันตรายโดยเฉพาะ"
    }
]


def retrieve_rule(category):
    """ค้นหากฎจากประเภทขยะ"""

    for rule in waste_rules:
        if rule["category"] == category:
            return rule

    return None


def get_rule_by_contamination(category, contamination):
    """
    เลือกกฎการทิ้งโดยพิจารณาทั้งประเภทขยะ
    และระดับการปนเปื้อน
    """

    # -------------------------
    # Unknown / invalid category
    # -------------------------

    valid_categories = {
        "recyclable",
        "general",
        "organic",
        "hazardous"
    }

    if category not in valid_categories:
        return {
            "name": "ไม่สามารถระบุประเภทได้",
            "bin_color": "⚪ ไม่ระบุ",
            "instruction": "ไม่สามารถแนะนำถังขยะได้ กรุณาถ่ายรูปใหม่ให้เห็นสิ่งของชัดเจนขึ้น"
        }

    # -------------------------
    # Recyclable
    # -------------------------

    if category == "recyclable":

        if contamination == "high":
            return {
                "name": "ขยะทั่วไป",
                "bin_color": "🔵 สีฟ้า",
                "instruction": "วัสดุมีการปนเปื้อนสูง ควรแยกอาหารหรือสิ่งปนเปื้อนออกก่อน หากไม่สามารถทำความสะอาดได้ ให้ทิ้งลงถังขยะทั่วไป"
            }

        if contamination == "medium":
            return {
                "name": "ขยะรีไซเคิล",
                "bin_color": "🟡 สีเหลือง",
                "instruction": "เทของเหลวหรือเศษอาหารออก และทำความสะอาดเบื้องต้นก่อนทิ้งลงถังรีไซเคิล"
            }

        return {
            "name": "ขยะรีไซเคิล",
            "bin_color": "🟡 สีเหลือง",
            "instruction": "เทของเหลวออกและทำความสะอาดเบื้องต้นก่อนทิ้งลงถังรีไซเคิล"
        }

    # -------------------------
    # General
    # -------------------------

    if category == "general":

        if contamination == "high":
            return {
                "name": "ขยะทั่วไป",
                "bin_color": "🔵 สีฟ้า",
                "instruction": "เทอาหารหรือเศษอาหารออกก่อน แล้วทิ้งลงถังขยะทั่วไป"
            }

        return {
            "name": "ขยะทั่วไป",
            "bin_color": "🔵 สีฟ้า",
            "instruction": "ทิ้งลงถังขยะทั่วไป"
        }

    # -------------------------
    # Organic
    # -------------------------

    if category == "organic":
        return {
            "name": "ขยะอินทรีย์",
            "bin_color": "🟢 สีเขียว",
            "instruction": "แยกเศษอาหารหรือวัสดุอินทรีย์ออกจากสิ่งอื่น แล้วทิ้งลงถังขยะอินทรีย์"
        }

    # -------------------------
    # Hazardous
    # -------------------------

    if category == "hazardous":
        return {
            "name": "ขยะอันตราย",
            "bin_color": "🔴 สีแดง",
            "instruction": "ห้ามทิ้งรวมกับขยะทั่วไป ควรนำไปทิ้งในจุดหรือถังสำหรับขยะอันตรายโดยเฉพาะ"
        }

    return retrieve_rule(category)
