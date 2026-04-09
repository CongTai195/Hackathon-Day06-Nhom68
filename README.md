# VinFast AI Consultant — Trợ lý Thông minh Đa nền tảng

Chào mừng bạn đến với dự án **VinFast AI Consultant**, một trợ lý AI tiên tiến được thiết kế để cung cấp trải nghiệm tư vấn xe điện cá nhân hóa, chuyên nghiệp và chính xác theo tiêu chuẩn VinFast.

![VinFast UI](static/vinfast_v_emblem.png)

## 🚀 Tính năng chính

- **Tư vấn gợi ý xe thông minh**: Logic gợi ý xe dựa trên ngân sách (ưu tiên tiệm cận ngân sách) và nhu cầu sử dụng (thành phố vs đường trường).
- **Hệ thống dữ liệu động**: Luôn cập nhật thông tin mới nhất về các dòng xe (bao gồm cả VF 7S và dòng thương mại Green mới: Minio, Herio, Nerio, Limo).
- **Chính sách sạc pin 2026**: Cập nhật các ưu đãi miễn phí sạc mới nhất (áp dụng đến 2029).
- **Quy trình SOS & Escalation**: Tự động nhận diện các yêu cầu khẩn cấp hoặc kỹ thuật phức tạp để chuyển hướng tới chuyên viên hỗ trợ (Human-in-the-loop).
- **Giao diện Glassmorphism**: UI hiện đại, hiệu ứng kính mờ, tối ưu trải nghiệm người dùng trên cả desktop và mobile.
- **Giám sát thời gian thực**: Theo dõi chỉ số Fallback Rate và các Tool calls ngay trên sidebar.

## 🛠 Công nghệ sử dụng

- **Backend**: Python, FastAPI, Uvicorn.
- **AI Logic**: LangGraph (quản lý state-machine), LangChain, OpenAI GPT-4o-mini.
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (ES6+).
- **Data storage**: Cấu trúc JSON phẳng (`vinfast_cars.json`) giúp truy xuất dữ liệu xe siêu nhanh.

## 📦 Hướng dẫn cài đặt

### 1. Cài đặt môi trường
Đảm bảo bạn đã cài đặt Python 3.9+.

```bash
# Clone repository
git clone <your-repo-url>
cd hackathon_Day06

# Tạo và kích hoạt môi trường ảo
python3 -m venv venv
source venv/bin/activate  # Trên MacOS/Linux
# venv\Scripts\activate   # Trên Windows

# Cài đặt dependencies
pip install -r requirement.txt
```

### 2. Cấu hình biến môi trường
Tạo file `.env` tại thư mục gốc và thêm các khóa API của bạn:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Khởi chạy ứng dụng
```bash
python3 server.py
```
Ứng dụng sẽ khả dụng tại: **[http://localhost:8080](http://localhost:8080)**

## 📂 Cấu trúc dự án

- `server.py`: Entry point chính, xử lý API và serve giao diện tĩnh.
- `agent.py`: Định nghĩa cấu trúc đồ thị (graph) của AI Agent và logic ghi nhớ (Memory).
- `tools.py`: Tập hợp các công cụ (tools) mà Agent có thể gọi (gợi ý xe, bảo dưỡng, chính sách sạc...).
- `static/index.html`: Giao diện người dùng tích hợp sẵn CSS và JS.
- `vinfast_cars.json`: Database thông số kỹ thuật và giá bán của toàn bộ dòng xe VinFast.
- `system_promt.txt`: Hướng dẫn hành vi và cá tính cho Agent.

## 💡 Cách sử dụng
- **Gợi ý xe**: "Tôi có khoảng 700 triệu, nên mua xe nào?"
- **Hỏi chính sách sạc**: "Chính sách miễn phí sạc hiện nay thế nào?"
- **So sánh xe**: "So sánh VF 5 và VF e34 cho tôi."
- **Đặt lịch**: "Tôi muốn đăng ký lái thử VF 7 tại Đà Nẵng."

---
*Dự án được phát triển trong khuôn khổ Hackathon Day 06 — Nhom 68.*
