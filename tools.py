"""
tools.py — AI Agent CSKH VinFast
Các tools theo spec-final.md:
  - get_car_specs            : thông số kỹ thuật chi tiết
  - get_pricing_and_battery_policy : giá + chính sách thuê pin (kèm disclaimer timestamp)
  - recommend_cars           : gợi ý xe theo budget + số chỗ (core selling tool)
  - compare_vinfast_cars     : so sánh 2 dòng xe
  - get_battery_lease_policy : giải đáp riêng chính sách thuê pin
  - get_maintenance_schedule : lịch bảo dưỡng theo số km
  - book_service             : đặt lịch lái thử / bảo dưỡng / sửa chữa
  - escalate_to_human        : chuyển CSKH (fallback khi AI không chắc / SOS)
"""

import json
from datetime import date
from langchain_core.tools import tool

# ─── Load dữ liệu xe ─────────────────────────────────────────────────────────
DATA_FILE = "vinfast_cars.json"
DATA_UPDATED_DATE = "2026-04-09"  # Cập nhật mỗi khi refresh file JSON

try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        CARS_DB = json.load(f)
except FileNotFoundError:
    CARS_DB = []

# ─── Disclaimer bắt buộc theo spec (Failure Mode #1: data stale) ─────────────
_PRICE_DISCLAIMER = (
    f"\n\n⚠️ *Thông tin giá & chính sách tham khảo tại ngày {DATA_UPDATED_DATE}. "
    "Vui lòng xác nhận tại đại lý VinFast gần nhất hoặc gọi hotline 1900 23 23 89 "
    "để có báo giá chính xác nhất.*"
)

# ─── SOS keywords (Failure Mode #2) ──────────────────────────────────────────
SOS_KEYWORDS = [
    "hỏng đường", "tai nạn", "phanh", "không phanh", "mất lái", "khẩn cấp",
    "xe chết", "xe không khởi động", "cháy xe", "kẹt cửa", "sos",
    "cứu", "nguy hiểm", "lỗi ota", "lỗi phần cứng",
]


def _is_sos(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in SOS_KEYWORDS)


def _find_car(model_name: str):
    """Tìm xe trong DB theo tên/model (fuzzy match)."""
    q = model_name.lower().replace(" ", "").replace("-", "")
    for car in CARS_DB:
        name_norm = car["name"].lower().replace(" ", "").replace("-", "")
        id_norm = car["id"].lower().replace("-", "")
        model_norm = car["model"].lower().replace(" ", "").replace("-", "")
        if q in name_norm or q in id_norm or q == model_norm:
            return car
    return None


# ─── Tools ───────────────────────────────────────────────────────────────────

@tool
def get_car_specs(model_name: str) -> str:
    """Lấy thông số kỹ thuật chi tiết của một dòng xe VinFast cụ thể.
    Ví dụ: 'VF 5 Plus', 'VF 6 Eco', 'VF 8 Plus', 'VF 9'.
    Dùng tool này khi khách hỏi về pin, tầm hoạt động, công suất, tăng tốc."""
    car = _find_car(model_name)
    if not car:
        return f"Không tìm thấy thông số kỹ thuật cho dòng xe: '{model_name}'. Các dòng xe hiện có: VF 3, VF 5 Plus, VF e34, VF 6, VF 7, VF 8, VF 9."

    perf = car["performance"]
    accel_key = "acceleration_0_100_secs" if "acceleration_0_100_secs" in perf else "acceleration_0_50_secs"
    accel_label = "0–100 km/h" if accel_key == "acceleration_0_100_secs" else "0–50 km/h"

    return (
        f"📋 Thông số kỹ thuật — {car['name']}\n"
        f"• Phân khúc : {car['segment']} | Số chỗ: {car['capacity']} chỗ\n"
        f"• Pin        : {car['battery']['capacity_kwh']} kWh\n"
        f"• Tầm hoạt  : {car['battery']['range_km']} km (1 lần sạc đầy)\n"
        f"• Sạc nhanh : ~{car['battery']['fast_charge_time_mins']} phút (10→80%)\n"
        f"• Công suất  : {perf['max_power_kw']} kW | Mô-men: {perf['max_torque_nm']} Nm\n"
        f"• Tăng tốc  : {perf[accel_key]} giây ({accel_label})"
    )


@tool
def get_pricing_and_battery_policy(model_name: str) -> str:
    """Lấy giá bán và chính sách thuê pin / mua đứt pin của một dòng xe VinFast cụ thể.
    Luôn kèm disclaimer về tính thời điểm của giá. Dùng khi khách hỏi giá xe."""
    car = _find_car(model_name)
    if not car:
        return f"Không tìm thấy thông tin giá cho dòng xe: '{model_name}'."

    base = car["pricing"]["base_price_vnd"]
    full = car["pricing"]["battery_included_price_vnd"]
    monthly_lease = base * 0.0025  # ước tính ~0.25%/tháng giá xe

    return (
        f"💰 Giá bán — {car['name']}\n"
        f"• Thuê pin (trả góp pin hàng tháng): {base:,.0f} VNĐ\n"
        f"  → Phí thuê pin ước tính: ~{monthly_lease:,.0f} VNĐ/tháng\n"
        f"• Mua đứt pin (sở hữu hoàn toàn) : {full:,.0f} VNĐ\n"
        f"• Chênh lệch mua đứt vs thuê pin  : {full - base:,.0f} VNĐ"
        + _PRICE_DISCLAIMER
    )


@tool
def recommend_cars(budget_million_vnd: int, seats_needed: int = 5, use_case: str = "thành phố") -> str:
    """Gợi ý tối đa 2 dòng xe VinFast phù hợp nhất dựa trên ngân sách và nhu cầu.
    - budget_million_vnd: ngân sách tính theo triệu VNĐ (VD: 700 = 700 triệu)
    - seats_needed: số ghế tối thiểu cần (mặc định 5)
    - use_case: mục đích dùng ('thành phố', 'đường dài', 'gia đình')
    Đây là tool CHÍNH để tư vấn mua xe — ưu tiên xe có giá sát nhất với ngân sách."""
    budget_vnd = budget_million_vnd * 1_000_000

    # Lọc ban đầu: ưu tiên xe cùng phân khúc giá (từ 50% đến 115% ngân sách)
    # Chúng ta cho phép vượt 15% để khách có thêm lựa chọn tốt hơn một chút
    candidates = [
        c for c in CARS_DB
        if c["pricing"]["base_price_vnd"] <= budget_vnd * 1.15
        and c["capacity"] >= seats_needed
    ]

    # Nếu không có xe nào trong tầm giá sát, nới lỏng xuống các xe rẻ hơn (Mini-SUV)
    if not candidates:
        candidates = [
            c for c in CARS_DB
            if c["capacity"] >= seats_needed
        ]
        if not candidates:
            return (
                f"Với yêu cầu {seats_needed} chỗ ngồi, em chưa tìm được dòng xe VinFast phù hợp. "
                f"Anh/chị có thể điều chỉnh yêu cầu không ạ?"
            )

    # Logic sắp xếp:
    if "dài" in use_case.lower():
        # Đường dài: Ưu tiên Range, nhưng vẫn phải quan tâm đến Budget
        # Chọn top 5 xe gần budget nhất rồi sort theo range
        candidates.sort(key=lambda c: abs(c["pricing"]["base_price_vnd"] - budget_vnd))
        near_budget = candidates[:5]
        near_budget.sort(key=lambda c: -c["battery"]["range_km"])
        top = near_budget[:2]
    else:
        # Bình thường: Ưu tiên xe có giá sát ngân sách khách đưa ra nhất
        candidates.sort(key=lambda c: abs(c["pricing"]["base_price_vnd"] - budget_vnd))
        top = candidates[:2]

    lines = [f"🚗 Dựa trên ngân sách {budget_million_vnd} triệu | {seats_needed} chỗ | {use_case}:\n"]

    for i, car in enumerate(top, 1):
        price = car["pricing"]["base_price_vnd"]
        lines.append(
            f"  {i}. {car['name']} ({car['segment']})\n"
            f"     • Giá thuê pin: {price:,.0f} VNĐ\n"
            f"     • Tầm hoạt động: {car['battery']['range_km']} km\n"
            f"     • Tăng tốc: {car['performance'].get('acceleration_0_100_secs', car['performance'].get('acceleration_0_50_secs', '?'))}s"
        )

    lines.append(_PRICE_DISCLAIMER)
    return "\n".join(lines)


@tool
def compare_vinfast_cars(model_1: str, model_2: str) -> str:
    """So sánh chi tiết 2 dòng xe VinFast cạnh nhau.
    Dùng khi khách muốn chọn giữa 2 dòng xe cụ thể."""
    car1 = _find_car(model_1)
    car2 = _find_car(model_2)
    if not car1 and not car2:
        return "Không tìm thấy thông tin của cả 2 dòng xe. Vui lòng kiểm tra lại tên xe."
    if not car1:
        return f"Không tìm thấy thông tin dòng xe: '{model_1}'."
    if not car2:
        return f"Không tìm thấy thông tin dòng xe: '{model_2}'."

    return (
        f"⚖️ So sánh {car1['name']} vs {car2['name']}\n"
        f"{'Tiêu chí':<22} {'  ' + car1['name']:<24} {car2['name']}\n"
        f"{'-'*72}\n"
        f"{'Phân khúc':<22} {car1['segment']:<24} {car2['segment']}\n"
        f"{'Số chỗ':<22} {str(car1['capacity']) + ' chỗ':<24} {str(car2['capacity'])} chỗ\n"
        f"{'Tầm hoạt động':<22} {str(car1['battery']['range_km']) + ' km':<24} {str(car2['battery']['range_km'])} km\n"
        f"{'Pin':<22} {str(car1['battery']['capacity_kwh']) + ' kWh':<24} {str(car2['battery']['capacity_kwh'])} kWh\n"
        f"{'Giá thuê pin':<22} {car1['pricing']['base_price_vnd']:>18,.0f} đ  {car2['pricing']['base_price_vnd']:>18,.0f} đ\n"
        f"{'Giá mua đứt pin':<22} {car1['pricing']['battery_included_price_vnd']:>18,.0f} đ  {car2['pricing']['battery_included_price_vnd']:>18,.0f} đ"
        + _PRICE_DISCLAIMER
    )


@tool
def get_battery_lease_policy() -> str:
    """Giải thích chính sách thuê pin VinFast (battery-as-a-service).
    Dùng khi khách hỏi riêng về thuê pin, mua đứt pin, hay chính sách pin là gì."""
    return (
        "🔋 Chính sách Pin VinFast (Battery-as-a-Service)\n\n"
        "VinFast cung cấp 2 lựa chọn:\n"
        "1️⃣  Thuê pin (BaaS): Mua xe với giá thấp hơn + trả phí thuê pin hàng tháng.\n"
        "   • Phí thuê dao động ~750.000 – 1.500.000 VNĐ/tháng tuỳ dòng xe & gói km.\n"
        "   • VinFast bảo hành pin trọn đời (SOH ≥ 70%) khi thuê.\n"
        "   • Nếu pin hỏng/xuống cấp: VinFast thay pin miễn phí.\n\n"
        "2️⃣  Mua đứt pin: Sở hữu pin hoàn toàn, giá mua cao hơn nhưng không tốn phí thuê tháng.\n"
        "   • Bảo hành pin 8 năm hoặc 160.000 km (tuỳ điều kiện nào đến trước).\n\n"
        "📌 Lợi thế thuê pin: chi phí trả trước thấp hơn, không lo pin cũ mất giá.\n"
        "📌 Lợi thế mua đứt: tổng chi phí dài hạn thấp hơn nếu giữ xe > 5 năm."
        + _PRICE_DISCLAIMER
    )


@tool
def get_maintenance_schedule(model_name: str, mileage_km: int) -> str:
    """Tra cứu lịch bảo dưỡng định kỳ VinFast dựa trên số km đã đi.
    Dùng khi khách hỏi nên bảo dưỡng những gì, bảo dưỡng định kỳ gồm gì."""
    if mileage_km < 5000:
        items = "Kiểm tra áp suất lốp, mức nước rửa kính, đèn chiếu sáng và phanh tay."
        interval_note = "Đây là lần kiểm tra đầu tiên sau khi nhận xe."
    elif mileage_km < 12000:
        items = (
            "Kiểm tra hệ thống treo, phanh (má phanh, đĩa phanh), "
            "nước làm mát, lốp và đo chỉ số sức khỏe pin (SOH)."
        )
        interval_note = "Bảo dưỡng định kỳ 6 tháng / 10.000 km."
    elif mileage_km < 40000:
        items = (
            "Thay nước làm mát pin, kiểm tra & thay lọc gió điều hoà, "
            "cân chỉnh thước lái, kiểm tra toàn diện hệ thống điện cao áp và cáp sạc."
        )
        interval_note = "Bảo dưỡng định kỳ 1 năm / 20.000 km."
    else:
        items = (
            "Bảo dưỡng lớn: tổng kiểm tra pin traction battery, thay dầu phanh, "
            "kiểm tra hệ thống làm mát, cân bằng động 4 bánh và reset hệ thống BMS."
        )
        interval_note = "Bảo dưỡng định kỳ 2 năm / 40.000 km."

    return (
        f"🔧 Lịch bảo dưỡng — {model_name} | {mileage_km:,} km\n"
        f"📌 {interval_note}\n\n"
        f"Các hạng mục cần bảo dưỡng:\n{items}\n\n"
        "Đặt lịch bảo dưỡng ngay để được phục vụ ưu tiên tại VinFast Service Center."
    )


@tool
def book_service(
    customer_name: str,
    phone: str,
    service_type: str,
    showroom_location: str,
    preferred_date: str,
) -> str:
    """Đặt lịch lái thử xe hoặc lịch bảo dưỡng / sửa chữa tại VinFast Service Center.
    - service_type: 'lái thử', 'bảo dưỡng định kỳ', 'sửa chữa', hoặc mô tả cụ thể
    - preferred_date: ngày mong muốn (VD: '12/04/2026' hoặc 'cuối tuần này')
    Dùng khi khách muốn đặt lịch."""
    today = date.today().strftime("%d/%m/%Y")
    return (
        f"✅ Đặt lịch thành công!\n"
        f"• Khách hàng : {customer_name}\n"
        f"• SĐT        : {phone}\n"
        f"• Dịch vụ    : {service_type}\n"
        f"• Địa điểm   : VinFast Service – {showroom_location}\n"
        f"• Ngày mong muốn: {preferred_date}\n\n"
        f"Nhân viên VinFast sẽ gọi xác nhận slot chính xác trong vòng 24h kể từ {today}.\n"
        "Hotline hỗ trợ: 1900 23 23 89"
    )


@tool
def escalate_to_human(reason: str = "Khách yêu cầu") -> str:
    """Chuyển phiên chat sang nhân viên CSKH hoặc kỹ thuật viên người thật.
    Dùng khi: (1) khách không hài lòng với AI, (2) câu hỏi kỹ thuật sâu/khẩn cấp
    AI không thể xử lý an toàn, (3) khách chủ động yêu cầu gặp người thật.
    Luôn gọi tool này cho các tình huống SOS (xe hỏng, tai nạn, nguy hiểm)."""
    return (
        f"🎧 Chuyển kết nối sang chuyên viên người thật.\n"
        f"Lý do: {reason}\n\n"
        "Vui lòng giữ máy, chuyên viên VinFast sẽ tiếp nhận ngay.\n"
        "Hotline khẩn cấp 24/7: **1900 23 23 89**\n"
        "Roadside Assistance: **1800 599 945** (miễn phí trong giờ hành chính)"
    )


@tool
def get_charging_policy() -> str:
    """Tra cứu chính sách miễn phí sạc pin mới nhất (tháng 4/2026).
    Dùng khi khách hỏi về sạc pin miễn phí, ưu đãi trạm sạc V-Green, hoặc quyền lợi sạc của Xanh SM."""
    return (
        "⚡ Chính sách Miễn phí Sạc Pin VinFast (Cập nhật tháng 04/2026)\n\n"
        "1️⃣  Đối với Ô tô điện cá nhân:\n"
        "   • Khách mua xe từ 10/02/2026: Miễn phí sạc tại trạm V-Green trong 03 năm (đến 10/02/2029).\n"
        "   • Khách mua xe trước 10/02/2026: Miễn phí sạc 03 năm kể từ ngày nhận xe.\n"
        "   • Định mức: Tối đa 10 lần sạc/tháng (phù hợp nhu cầu di chuyển 1.500 - 5.000 km/tháng).\n\n"
        "2️⃣  Đối với đối tác Xanh SM Platform:\n"
        "   • Miễn phí sạc KHÔNG GIỚI HẠN số lần trên hệ thống trạm sạc toàn quốc.\n\n"
        "3️⃣  Đối với Xe máy điện (Dùng pin đổi):\n"
        "   • Miễn phí đổi pin đến hết ngày 30/06/2028.\n"
        "   • Định mức: Tối đa 20 lần đổi/tháng.\n\n"
        "📌 Lưu ý: Chính sách áp dụng tại hệ thống trạm sạc V-Green trên toàn quốc. "
        "Ngoài định mức miễn phí, phí sạc sẽ được tính theo biểu giá hiện hành của V-Green."
        + _PRICE_DISCLAIMER
    )


# ─── Export ───────────────────────────────────────────────────────────────────
agent_tools = [
    get_car_specs,
    get_pricing_and_battery_policy,
    get_charging_policy,
    recommend_cars,
    compare_vinfast_cars,
    get_battery_lease_policy,
    get_maintenance_schedule,
    book_service,
    escalate_to_human,
]
