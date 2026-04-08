# SPEC draft — Agent CSKH VinFast

## Track: VinFast

## Problem statement
Khách hàng có nhu cầu tìm hiểu các dòng xe ô tô điện VinFast (thông số, giá bán, chính sách thuê/mua pin), hoặc cần hướng dẫn bảo trì, bảo dưỡng, theo dõi khuyến mãi thường phải tra cứu qua nhiều nguồn hoặc chờ đợi kết nối tổng đài (mất 5-10 phút). Nhân viên CSKH/Sales phải giải quyết khối lượng lớn các câu hỏi lặp đi lặp lại. Một AI Agent có thể đóng vai trò tư vấn viên 24/7, hỏi đáp nhu cầu thực tế, sau đó tự động cung cấp thông tin, so sánh xe, đặt lịch dịch vụ và tư vấn hậu mãi một cách chính xác.

## Canvas draft

| | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| Trả lời | Khách hàng mới và cũ. Pain: chờ 10 phút, tra cứu thông tin xe/chính sách rườm rà. AI giúp gợi ý dòng xe, giải đáp chi phí lăn bánh, lịch bảo dưỡng trong vài giây. | Thông tin giá xe, chính sách bảo hành, khuyến mãi đặc biệt phải chính xác 100%. Nếu AI "bịa" sai giá (hallucination) sẽ gây phẫn nộ. Cần nút "Gặp chuyên viên" ngay màn hình. | Có thể triển khai RAG với cơ sở dữ liệu có sẵn (json, manual). API LLM ~$0.005/lượt, latency <3s. Risk: Chính sách thay đổi liên tục cần hệ thống cập nhật data real-time. |

**Auto hay aug?** Augmentation — AI đóng vai trò tiếp đón, phân loại nhu cầu, cung cấp thông tin cơ bản và bảng giá. Khách hàng và nhân viên Sales/CSKH sẽ quyết định chốt cọc hoặc lập lệnh sửa chữa cuối cùng.

**Learning signal:** Bấm nút "Đặt cọc", "Đặt lịch bảo dưỡng" (dương tính); hoặc "Chuyển tư vấn viên thực" ngay sau vài câu chat (tín hiệu sửa lỗi). So sánh xe AI gợi ý với xe khách hàng thực mua.

## Hướng đi chính
- Prototype: Chatbot kết nối với kho dữ liệu (như file `vinfast_cars.json`) có khả năng hỏi 3-5 câu về ngân sách/nhu cầu -> gợi ý 2 dòng xe phù hợp + báo giá sơ bộ. Hoặc nhận request bảo dưỡng -> cấp ngay lịch trống.
- Eval: Precision của thông tin giá xe và khuyến mãi = 100% (factual alignment).
- Main failure mode: Khách hàng hỏi các trường hợp quá đặc thù (xe hỏng giữa đường, lỗi kỹ thuật sâu) → AI cung cấp thông tin chung chung không hữu ích → Thiết lập luồng SOS/chuyển ngay cho kỹ thuật viên.

## Phân công
- Tài: Quản lý dự án & Business - Lập Canvas, phân tích failure modes (Hallucination về giá) và đánh giá ROI (Giảm tải tổng đài)
- Sơn: Product & UX - Lên User stories cho 4 paths (Mua xe, Thu cũ đổi mới, Bảo dưỡng, Hậu mãi), thiết kế luồng hội thoại
- Quang: Data Engineer - Thu thập và làm sạch cơ sở dữ liệu nội bộ (JSON xe VinFast, chính sách), cấu hình Vector Database
- Tín: AI/Backend Engineer - Xây dựng Prototype RAG cốt lõi, gắn kết LLM và thử nghiệm/tối ưu Prompt
- Ngọc: QA & Frontend/Integration - Đặt ra các tiêu chí Eval metrics để Test bot, xây dựng giao diện Chat demo (Web/Zalo)
