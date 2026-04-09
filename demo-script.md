# Demo Script — AI Agent CSKH VinFast

**Thời gian:** 2 phút | **Nhóm:** Nhom68

---

## Phân công demo

| Người | Nhiệm vụ |
|-------|---------|
| **Tín** | Chạy live demo trên terminal, giải thích luồng kỹ thuật |
| **Sơn** | Dẫn chuyện (storytelling), giải thích UX flow |
| **Tài / Ngọc / Quang** | Trực tại bàn, trả lời câu hỏi từ người xem |

---

## Script (2 phút)

### [0:00 – 0:20] Hook — Đặt vấn đề *(Sơn dẫn)*

> "Bạn muốn mua xe VinFast. Bạn lên website → bị choáng ngợp bởi 6 dòng xe, chục gói pin, trăm thông số. Bạn gọi hotline → chờ 7 phút. Chúng tôi hỏi: có cần phải vậy không?"

*[Chỉ vào màn hình terminal đã mở sẵn]*

---

### [0:20 – 1:30] Live Demo *(Tín chạy + giải thích)*

**Bước 1 — User nhập nhu cầu mua xe:**
```
Bạn: Tôi muốn mua xe điện, ngân sách khoảng 700 triệu, chủ yếu đi trong thành phố
```
*[AI hỏi thêm 1 câu: "Anh/chị cần mấy chỗ ngồi?"]*

```
Bạn: 5 chỗ
```
*[AI gợi ý VF5 Plus và VF6 kèm bảng so sánh thông số: giá, range, sạc nhanh]*

> **Tín giải thích:** "AI tự gọi tool `compare_cars`, tra `vinfast_cars.json`, ghép kết quả vào câu trả lời — không hallucinate vì dùng dữ liệu structured."

---

**Bước 2 — User hỏi về chính sách thuê pin:**
```
Bạn: Chính sách thuê pin của VF5 thế nào?
```
*[AI trả lời gói thuê pin + disclaimer "giá tham khảo, xác nhận tại đại lý"]*

> **Tín giải thích:** "Đây là failure mode chúng tôi thiết kế rõ nhất — data có thể stale, nên AI luôn kèm cảnh báo."

---

**Bước 3 — Demo memory:**
```
Bạn: Quay lại xe tôi hỏi lúc nãy
```
*[AI nhớ ngữ cảnh từ đầu phiên, nhắc lại VF5 Plus và VF6 mà không cần user nói lại]*

> **Tín giải thích:** "LangGraph MemorySaver giữ 10 lượt gần nhất — user không phải lặp lại context."

---

### [1:30 – 2:00] Tóm tắt + Q&A *(Sơn/Tài)*

> "Augmentation, không phải automation. AI tiếp đón, phân loại, cung cấp thông tin — con người chốt deal. Failure mode chính chúng tôi lo nhất: hallucinate giá → giải bằng dữ liệu structured + disclaimer cứng. Metric ưu tiên: Factual Accuracy ≥ 95%."

*[Chỉ vào poster/slide tóm tắt: Problem → Solution → Auto/Aug → Demo]*

**Câu hỏi dự kiến có thể hỏi lại:**
- "Auto hay aug?" → Augmentation. User ra quyết định cuối.
- "Failure mode chính?" → Hallucinate giá khi data stale → disclaimer + link đại lý.
- "Tín làm phần nào?" → agent.py, tools.py, LangGraph setup, system prompt engineering.

---

## Backup plan nếu demo crash
1. Mở file `agent.py` và `tools.py` trong VS Code — giải thích code live
2. Show screenshot conversation đã chạy trước
3. Chạy 1 tool đơn giản trực tiếp: `python3 -c "from tools import *; print(get_all_cars())"`
