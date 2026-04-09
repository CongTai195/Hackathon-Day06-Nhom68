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

# ─── Cấu hình dữ liệu ────────────────────────────────────────────────────────
DATA_FILE = "vinfast_cars.json"
DATA_UPDATED_DATE = "2026-04-09"

_PRICE_DISCLAIMER = (
    f"\n\n⚠️ *Thông tin giá & chính sách tham khảo tại ngày {DATA_UPDATED_DATE}. "
    "Vui lòng xác nhận tại đại lý VinFast gần nhất hoặc gọi hotline 1900 23 23 89 "
    "để có báo giá chính xác nhất.*"
)

SOS_KEYWORDS = [
    "hỏng đường", "tai nạn", "phanh", "không phanh", "mất lái", "khẩn cấp",
    "xe chết", "xe không khởi động", "cháy xe", "kẹt cửa", "sos",
    "cứu", "nguy hiểm", "lỗi ota", "lỗi phần cứng",
]

def _is_sos(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in SOS_KEYWORDS)

def _load_db():
    """Tải dữ liệu xe mới nhất từ file JSON."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _find_car(model_name: str):
    """Tìm xe trong DB theo tên/model (fuzzy match)."""
    db = _load_db()
    q = model_name.lower().replace(" ", "").replace("-", "")
    for car in db:
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
    Dùng tool này khi khách hỏi về pin, tầm hoạt động, công suất, tăng tốc, và màu sắc (bảng màu)."""
    car = _find_car(model_name)
    if not car:
        return f"Không tìm thấy thông số kỹ thuật cho dòng xe: '{model_name}'. Các dòng xe hiện có: VF 3, VF 5 Plus, VF e34, VF 6, VF 7, VF 8, VF 9."

    perf = car["performance"]
    accel_val = perf.get("acceleration_0_100_secs") or perf.get("acceleration_0_50_secs")
    accel_label = "0–100 km/h" if "acceleration_0_100_secs" in perf else "0–50 km/h"
    accel_str = f"{accel_val} giây ({accel_label})" if accel_val else "Đang cập nhật"

    colors = car.get("colors", [])
    color_str = f"\n• Bảng màu  : {', '.join(colors)}" if colors else ""

    return (
        f"📋 Thông số kỹ thuật — {car['name']}\n"
        f"• Phân khúc : {car['segment']} | Số chỗ: {car['capacity']} chỗ\n"
        f"• Pin        : {car['battery']['capacity_kwh']} kWh\n"
        f"• Tầm hoạt  : {car['battery']['range_km']} km (1 lần sạc đầy)\n"
        f"• Sạc nhanh : ~{car['battery']['fast_charge_time_mins']} phút (10→80%)\n"
        f"• Công suất  : {perf['max_power_kw']} kW | Mô-men: {perf['max_torque_nm']} Nm\n"
        f"• Tăng tốc  : {accel_str}"
        f"{color_str}"
    )


@tool
def get_pricing_and_battery_policy(model_name: str) -> str:
    """Lấy bảng giá chi tiết kèm ưu đãi của một dòng xe VinFast.
    Bao gồm: Giá công bố, Khuyến mãi VinFast, Bảo hiểm và Ưu đãi đại lý.
    Dùng khi khách hỏi giá xe."""
    car = _find_car(model_name)
    if not car:
        return f"Không tìm thấy thông tin giá cho dòng xe: '{model_name}'."

    full_price = car["pricing"]["battery_included_price_vnd"]
    
    # Logic tính toán ưu đãi (Tháng 4/2026)
    promo_vf_percent = 6 # Khuyến mãi chung 6%
    promo_vf_amount = full_price * (promo_vf_percent / 100)
    insurance_2yr = 0 # Quy đổi bảo hiểm 2 năm, được tặng
    dealer_promo = 4_000_000 # Ưu đãi đại lý mặc định
    total_savings = promo_vf_amount + insurance_2yr + dealer_promo
    final_estimated = full_price - total_savings
    
    # Chi phí đăng ký & Lăn bánh (Tháng 4/2026)
    reg_fees = {
        "Thuế trước bạ (đến 28/02/2027)": 0,
        "Lệ phí biển số": 200_000,
        "Phí đăng kiểm": 140_000,
        "Phí bảo trì đường bộ (1 năm)": 1_560_000,
        "Dịch vụ đăng ký xe": 0, # Tặng
        "Bảo hiểm TNDS": 480_700
    }
    total_reg_fees = sum(reg_fees.values())
    final_on_road = final_estimated + total_reg_fees

    return (
        f"📊 **BẢNG TÍNH GIÁ XE & ƯU ĐÃI — {car['name'].upper()}**\n\n"
        f"| Hạng mục | Chi tiết | Giá trị (VNĐ) |\n"
        f"| :--- | :--- | :---: |\n"
        f"| **1. Giá xe công bố** | Niêm yết (kèm pin) | {full_price:,.0f} |\n"
        f"| **2. Khuyến mãi VinFast** | Ưu đãi 6% giá xe | -{promo_vf_amount:,.0f} |\n"
        f"| **3. Bảo hiểm quy đổi** | Gói bảo hiểm vật chất 2 năm | {insurance_2yr:,.0f} |\n"
        f"| **4. Khuyến mãi đại lý** | Ưu đãi thêm tại showroom | -{dealer_promo:,.0f} |\n"
        f"| --- | --- | --- |\n"
        f"| 💰 **GIÁ ƯU ĐÃI TẾ** | **Tổng sau khuyến mãi** | **{final_estimated:,.0f}** |\n"
        f"| --- | --- | --- |\n"
        f"| **5. Thuế trước bạ** | Ưu đãi 0% (đến 28/02/2027) | 0 |\n"
        f"| **6. Lệ phí biển số** | Cấp mới biển số | 200,000 |\n"
        f"| **7. Phí đăng kiểm** | Kiểm định kỹ thuật | 140,000 |\n"
        f"| **8. Phí đường bộ** | Gói 1 năm (Cá nhân) | 1,560,000 |\n"
        f"| **9. Bảo hiểm TNDS** | Bảo hiểm bắt buộc | 480,700 |\n"
        f"| --- | --- | --- |\n"
        f"| 🚀 **GIÁ LĂN BÁNH TẠM TÍNH** | **Tổng chi phí sở hữu** | **{final_on_road:,.0f}** |\n\n"
        f"*(Giá lăn bánh đã bao gồm ưu đãi thuế trước bạ 0% áp dụng đến hết 28/02/2027)*\n"
        + _PRICE_DISCLAIMER
    )



@tool
def get_registration_fees(model_name: str) -> str:
    """Trả lời chi tiết về các loại phí đăng ký xe (phí lăn bánh) tại Việt Nam.
    Bao gồm Thuế trước bạ, Biển số, Đăng kiểm, Bảo trì đường bộ, Bảo hiểm TNDS."""
    return (
        f"📋 **BẢNG CHI TIẾT PHÍ ĐĂNG KÝ XE ĐIỆN — {model_name.upper()}**\n\n"
        f"| Hạng mục | Chi tiết | Giá trị (VNĐ) |\n"
        f"| :--- | :--- | :---: |\n"
        f"| **1. Thuế trước bạ** | Ưu đãi 0% (đến 28/02/2027) | 0 |\n"
        f"| **2. Lệ phí biển số** | Cấp mới biển số | 200,000 |\n"
        f"| **3. Phí đăng kiểm** | Kiểm định kỹ thuật | 140,000 |\n"
        f"| **4. Phí bảo trì đường bộ** | Gói 1 năm (Cá nhân) | 1,560,000 |\n"
        f"| **5. Dịch vụ đăng ký** | Phí dịch vụ phía đại lý | Tặng |\n"
        f"| **6. Bảo hiểm TNDS** | Bảo hiểm bắt buộc | 480,700 |\n"
        f"| --- | --- | --- |\n"
        f"| 📝 **TỔNG CỘNG PHÍ** | **Phí đăng ký tạm tính** | **2,380,700** |\n\n"
        f"*Lưu ý: Bảng tính này áp dụng cho xe cá nhân đăng ký mới tại Việt Nam.*"
    )


@tool
def get_shop_url(model_name: str) -> str:
    """Lấy đường dẫn VinFast Shop để khách hàng xem thêm hình ảnh, thông tin chi tiết hoặc đặt cọc.
    Dùng tool này KHI VÀ CHỈ KHI khách hàng muốn xem thêm ảnh/thông tin hoặc đã xác nhận muốn xem link."""
    car = _find_car(model_name)
    if not car or "shop_url" not in car:
        return f"Hiện chưa có đường dẫn trực tiếp cho dòng xe: '{model_name}'. Quý khách có thể truy cập https://shop.vinfastauto.com/vn_vi/o-to-dien-vinfast.html để xem tất cả dòng xe."

    return (
        f"🔗 **ĐƯỜNG DẪN ĐẶT CỌC TRỰC TUYẾN — {car['name'].upper()}**\n"
        f"Quý khách có thể tiến hành đặt cọc và chọn cấu hình xe tại đây:\n"
        f"{car['shop_url']}\n\n"
        f"*Chúc quý khách sớm sở hữu chiếc xe ưng ý!*"
    )


@tool
def recommend_cars(budget_million_vnd: int, seats_needed: int = 5, use_case: str = "thành phố") -> str:
    """Gợi ý tối đa 2 dòng xe VinFast phù hợp nhất dựa trên ngân sách và nhu cầu.
    CHỈ GỌI tool này sau khi đã thu thập đủ 3 thông tin qua hội thoại từng bước (Sequential Probing):
    1. Ngân sách (budget_million_vnd)
    2. Số chỗ ngồi (seats_needed)
    3. Nhu cầu sử dụng (use_case)
    Hãy tóm tắt lại nhu cầu của khách trước khi đưa ra gợi ý."""
    budget_vnd = budget_million_vnd * 1_000_000

    # Lọc ban đầu: ưu tiên xe cùng phân khúc giá (từ 50% đến 115% ngân sách)
    # Chúng ta cho phép vượt 15% để khách có thêm lựa chọn tốt hơn một chút
    db = _load_db()
    candidates = [
        c for c in db
        if c["pricing"]["battery_included_price_vnd"] <= budget_vnd * 1.15
        and c["capacity"] >= seats_needed
    ]

    # Nếu không có xe nào trong tầm giá sát, nới lỏng xuống các xe rẻ hơn (Mini-SUV)
    if not candidates:
        candidates = [
            c for c in db
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
        candidates.sort(key=lambda c: abs(c["pricing"]["battery_included_price_vnd"] - budget_vnd))
        near_budget = candidates[:5]
        near_budget.sort(key=lambda c: -c["battery"]["range_km"])
        top = near_budget[:2]
    else:
        # Bình thường: Ưu tiên xe có giá sát ngân sách khách đưa ra nhất
        candidates.sort(key=lambda c: abs(c["pricing"]["battery_included_price_vnd"] - budget_vnd))
        top = candidates[:2]

    lines = [f"🚗 Dựa trên ngân sách {budget_million_vnd} triệu | {seats_needed} chỗ | {use_case}:\n"]

    for i, car in enumerate(top, 1):
        full_price = car["pricing"]["battery_included_price_vnd"]
        lines.append(
            f"  {i}. {car['name']} ({car['segment']})\n"
            f"     • Giá kèm pin: {full_price:,.0f} VNĐ\n"
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
        f"{'Giá bán (kèm pin)':<22} {car1['pricing']['battery_included_price_vnd']:>18,.0f} đ  {car2['pricing']['battery_included_price_vnd']:>18,.0f} đ"
        + _PRICE_DISCLAIMER
    )


@tool
def get_battery_lease_policy() -> str:
    """Giải thích chính sách Pin VinFast mới nhất (2026).
    Dùng khi khách hỏi về chính sách bảo hành pin, sạc pin hoặc giá pin."""
    return (
        "🔋 **Chính sách Pin VinFast — Tiêu chuẩn Hiện hành (2026)**\n\n"
        "Từ năm 2026, VinFast áp dụng chính sách **Mua xe kèm Pin** làm tiêu chuẩn duy nhất cho các dòng xe điện thế hệ mới, "
        "nhằm đơn giản hóa quy trình sở hữu và tối ưu chi phí cho khách hàng.\n\n"
        "1️⃣  **Quyền sở hữu**: Khách hàng sở hữu hoàn toàn bộ pin theo xe, không phát sinh chi phí thuê hàng tháng.\n"
        "2️⃣  **Bảo hành tiêu chuẩn**: Pin được bảo hành chính hãng từ 8-10 năm hoặc 160.000 - 200.000 km (tùy dòng xe).\n"
        "3️⃣  **Cam kết chất lượng**: VinFast cam kết hiệu suất pin ổn định, hỗ trợ sửa chữa/thay thế tại hệ thống xưởng dịch vụ toàn quốc.\n"
        "4️⃣  **Cứu hộ pin 24/7**: Hỗ trợ sạc khẩn cấp hoặc cứu hộ xe về trạm sạc gần nhất nếu gặp sự cố cạn pin trên đường.\n\n"
        "📌 Với chính sách này, tổng giá trị sở hữu xe (TCO) trong dài hạn được tối ưu hóa rõ rệt so với các mô hình trước đây."
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
    """- preferred_date: ngày mong muốn (VD: '12/04/2026' hoặc 'cuối tuần này')
    CHỈ ĐƯỢC GỌI sau khi đã thu thập đủ 5 thông tin thông qua hội thoại từng bước (Sequential Collection). 
    Phải tóm tắt lại thông tin cho khách xác nhận trước khi gọi tool này."""
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


# ─── RAG Tool ────────────────────────────────────────────────────────────────

@tool
def search_vinfast_docs(query: str) -> str:
    """Tìm kiếm thông tin từ tài liệu chính hãng VinFast (Brochure, chính sách, hướng dẫn...).
    Dùng để tra cứu: Chính sách bảo hành, Quy trình sửa chữa, 
    Hướng dẫn sử dụng, Trạm sạc V-Green, v.v.
    Đây là nguồn dữ liệu chính thống cho các thông tin văn bản dài."""
    return _rag_search(query)


# ─── Export ───────────────────────────────────────────────────────────────────
agent_tools = [
    get_car_specs,
    get_pricing_and_battery_policy,
    get_charging_policy,
    get_registration_fees,
    get_shop_url,
    recommend_cars,
    compare_vinfast_cars,
    get_battery_lease_policy,
    get_maintenance_schedule,
    book_service,
    escalate_to_human,
]
