import json
from langchain_core.tools import tool

# Tải dữ liệu xe từ JSON
try:
    with open("vinfast_cars.json", "r", encoding="utf-8") as f:
        CARS_DB = json.load(f)
except FileNotFoundError:
    CARS_DB = []

def find_car(model_name: str):
    name_lower = model_name.lower().replace(" ", "")
    for car in CARS_DB:
        # Match "vf3", "vf8", "vf8eco" etc.
        if name_lower in car["name"].lower().replace(" ", "") or name_lower in car["id"].replace("-", ""):
            return car
    return None

@tool
def get_car_specs(model_name: str) -> str:
    """Lấy thông số kỹ thuật chi tiết của dòng xe VinFast (VD: VF 3, VF 8, VF 9)."""
    car = find_car(model_name)
    if car:
        return (f"Thông số xe {car['name']}: \n"
                f"- Phân khúc: {car['segment']}\n"
                f"- Số chỗ ngồi: {car['capacity']}\n"
                f"- Pin: {car['battery']['capacity_kwh']} kWh, Tầm hoạt động: {car['battery']['range_km']} km (chỉ một lần sạc)\n"
                f"- Tăng tốc 0-100km/h: {car['performance'].get('acceleration_0_100_secs', car['performance'].get('acceleration_0_50_secs', 'N/A'))} giây\n"
                f"- Công suất cực đại: {car['performance']['max_power_kw']} kW\n"
                f"- Mô-men xoắn cực đại: {car['performance']['max_torque_nm']} Nm")
    return f"Không tìm thấy thông số kỹ thuật cho dòng xe: {model_name}."

@tool
def get_pricing_and_battery_policy(model_name: str, region: str = "VN") -> str:
    """Lấy giá bán và chính sách thuê/mua pin của xe."""
    car = find_car(model_name)
    if car:
        base_price = car['pricing']['base_price_vnd']
        battery_price = car['pricing']['battery_included_price_vnd']
        return (f"Chính sách giá cho {car['name']}:\n"
                f"- Giá mua không kèm pin (thuê pin): {base_price:,.0f} VNĐ\n"
                f"- Giá mua kèm pin (đứt pin): {battery_price:,.0f} VNĐ\n"
                f"(Khách hàng ở tỉnh/thành phố khác sẽ có thêm chi phí lăn bánh, thường cộng thêm 10-20tr cho phí trước bạ và biển số tuỳ khu vực).")
    return f"Không tìm thấy thông tin giá cho dòng xe: {model_name}."

@tool
def compare_vinfast_cars(model_1: str, model_2: str) -> str:
    """So sánh 2 dòng xe VinFast."""
    car1 = find_car(model_1)
    car2 = find_car(model_2)
    if not car1 or not car2:
        return "Vui lòng cung cấp đúng tên 2 dòng xe để so sánh."
    return (f"Bảng so sánh {car1['name']} và {car2['name']}:\n"
            f"- Phân khúc/Số chỗ: {car1['segment']}/{car1['capacity']} chỗ VS {car2['segment']}/{car2['capacity']} chỗ.\n"
            f"- Tầm hoạt động: {car1['battery']['range_km']} km VS {car2['battery']['range_km']} km.\n"
            f"- Dung lượng pin: {car1['battery']['capacity_kwh']} kWh VS {car2['battery']['capacity_kwh']} kWh.\n"
            f"- Giá thấp nhất: {car1['pricing']['base_price_vnd']:,.0f} đ VS {car2['pricing']['base_price_vnd']:,.0f} đ.")

@tool
def get_maintenance_schedule(model_name: str, mileage_km: int) -> str:
    """Lấy danh mục bảo dưỡng định kỳ dựa trên số km khách hàng đã đi."""
    if mileage_km < 12000:
        parts = "Kiểm tra hệ thống treo, phanh, nước làm mát, lốp và mức độ tiêu hao pin (SOH)."
    elif mileage_km < 40000:
        parts = "Thay nước làm mát pin, kiểm tra thay thế lọc gió điều hoà, cân chỉnh thước lái và kiểm tra toàn diện hệ thống điện cao áp."
    else:
        parts = "Bảo dưỡng lớn: kiểm tra pin động cơ, thay dầu phanh, dầu hộp số (nếu có), làm sạch hệ thống phanh và cân bằng động 4 bánh."
    return f"Dựa trên số km {mileage_km}km của dòng xe {model_name}, quý khách cần bảo dưỡng các hạng mục: {parts}"

@tool
def book_service(customer_name: str, phone: str, service_type: str, showroom_location: str, date: str) -> str:
    """Đặt lịch lái thử hoặc lịch bảo dưỡng/sửa chữa tại xưởng."""
    return f"Success: Đã đặt lịch {service_type} thành công cho khách hàng {customer_name} (SĐT: {phone}) tại {showroom_location} vào ngày {date}. Sẽ có nhân viên gọi xác nhận trong 24h."

@tool
def escalate_to_human() -> str:
    """Chuyển đoạn chat cho nhân viên CSKH con người (dùng khi khách bực hoặc hỏi điều rất nhạy cảm mà bot không chắc)."""
    return "Đã trigger lệnh chuyển kết nối cho chuyên viên chăm sóc khách hàng là người thật. Vui lòng nói với khách chờ một lát."

# Gom cụm các tool để export
agent_tools = [get_car_specs, get_pricing_and_battery_policy, compare_vinfast_cars, get_maintenance_schedule, book_service, escalate_to_human]
