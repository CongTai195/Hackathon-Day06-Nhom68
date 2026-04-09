# Individual Reflection — [Họ Tên] ([Mã Học Viên])

> **Note:** Anh điền tên và mã học viên vào dòng trên trước khi nộp.

---

## 1. Role cụ thể trong nhóm

**AI Lead / Backend Architect** — Phụ trách thiết kế và xây dựng "bộ não" của trợ lý ảo: LangGraph agent, logic truy vấn dữ liệu chính xác (Precision JSON), quy trình tư vấn chuyên nghiệp (Sequential Probing) và hệ thống tự học từ phản hồi (Feedback Refinement).

---

## 2. Phần phụ trách cụ thể (output rõ ràng)

1.  **Chuyển đổi từ RAG sang Pure JSON**: Nhận thấy RAG đôi khi gây ra sai lệch thông tư liệu kỹ thuật xe, em đã thay đổi toàn bộ kiến trúc sang truy vấn trực tiếp từ `vinfast_cars.json`. Kết quả: độ chính xác thông số và giá đạt 100% (Zero Hallucination).
2.  **Thiết kế Quy trình Tư vấn Tuần tự (Sequential Probing)**: Xây dựng bộ quy tắc ép AI phải hỏi khách hàng từng bước (Ngân sách -> Số chỗ -> Nhu cầu) thay vì hỏi gộp, tạo cảm giác chuyên nghiệp như một tư vấn viên thực thụ.
3.  **Hệ thống Tự học (Feedback Loop)**: Triển khai `feedback_handler.py` tự động chạy Root Cause Analysis (RCA) khi người dùng nhấn "Dislike". AI tự tìm ra lỗi của chính mình và nạp "bài học" vào context cho các lượt chat sau.
4.  **Thiết lập Guardrails nghiêm ngặt**: Cài đặt các chốt chặn "Stay on Topic" (không trả lời ngoài lề VinFast) và "One Question Per Turn" (không hỏi quá 1 câu mỗi lượt) để tối ưu trải nghiệm người dùng.
5.  **Tích hợp Backend - Frontend**: Xây dựng API FastAPI kết nối LangGraph với giao diện Glassmorphism, đảm bảo hiển thị metrics (Fallback rate, SOS count) thời gian thực.

---

## 3. SPEC phần nào mạnh nhất, phần nào yếu nhất?

**Mạnh nhất: Phần 4 — Failure Modes & Mitigation.**
Chúng em không chỉ liệt kê các lỗi tiềm ẩn mà đã hiện thực hóa được một hệ thống **Self-healing**. Thay vì chỉ có disclaimer, hệ thống đã biết tự phân tích nguyên nhân thất bại và tự điều chỉnh instructions ngay lập tức mà không cần can thiệp code (thông qua Lesson Injection).

**Yêu nhất: Phần 5 — ROI & Chi phí triển khai.**
Phần tính toán ROI cho kịch bản Optimistic còn dựa nhiều vào giả định về tỷ lệ chuyển đổi khách hàng từ chatbot sang mua xe thực tế. Cần có dữ liệu thực tế từ các đại lý để con số này thuyết phục hơn đối với các nhà đầu tư.

---

## 4. Đóng góp cụ thể khác

- **Optimizing SPEC Lookup**: Xây dựng logic Fuzzy matching trong `tools.py` giúp AI nhận diện đúng dòng xe ngay cả khi người dùng gõ sai tên (VD: "vf9 Plus" thay vì "VinFast VF 9 Plus").
- **UI UX Polish**: Trực tiếp tinh chỉnh mã CSS/JS để đảm bảo các bảng so sánh xe (Markdown tables) hiển thị đẹp mắt, trực quan và chuyên nghiệp trên màn hình.
- **Auto-fill Bug Fix**: Phát hiện và khắc phục lỗi trình duyệt tự động điền từ "vinfast" vào ô nhập liệu, cải thiện độ mượt mà khi chat.

---

## 5. 1 điều học được trong hackathon mà trước đó chưa biết

Em nhận ra rằng **"Precision is more important than Breadth"** trong lĩnh vực bán lẻ cao cấp. Trước đó, em nghĩ AI càng biết nhiều càng tốt, nhưng với xe hơi (giá trị lớn), chỉ cần AI nói sai một con số giá hoặc tầm hoạt động là mất niềm tin của khách hàng. Việc từ bỏ RAG để quay lại cấu trúc JSON thuần túy là quyết định khó khăn nhưng đúng đắn nhất để bảo vệ uy tín thương hiệu.

---

## 6. Nếu làm lại, đổi gì?

Nếu làm lại, em sẽ thiết kế **Hệ thống đánh giá tự động (Auto-eval)** ngay từ đầu. Thay vì chờ người dùng nhấn Dislike mới phân tích, em muốn xây dựng một "Agent giám sát" chạy song song để chấm điểm mọi câu trả lời của Agent chính theo thang điểm 10 ngay khi vừa sinh ra, giúp ngăn chặn câu trả lời tồi trước khi nó đến mắt khách hàng.

---

## 7. AI giúp gì? AI sai/mislead ở đâu?

**AI giúp:**
- **RCA Analysis**: Dùng GPT-4o-mini để đóng vai trò Auditor phân tích lỗi cực kỳ khách quan và sắc sảo.
- **Boilerplate Code**: Sinh các cấu trúc state machine cho LangGraph rất nhanh chóng.
- **CSS Design**: Gợi ý các mã màu và hiệu ứng Glassmorphism cho UI để có vẻ ngoài "cao cấp".

**AI sai/mislead:**
- Trong quá trình phát triển, AI nhiều lần phá vỡ quy tắc "Hỏi từng câu một" vì bản năng của LLM là muốn cung cấp giải pháp trọn gói. Em đã phải dùng đến cơ chế **"Negative Example"** (cho AI thấy ví dụ sai) trong prompt thì mới kiểm soát được hoàn toàn hành vi này.
- **Bài học**: Rules thôi là chưa đủ, AI cần các "Shadow Examples" (ví dụ xấu) để hiểu được ranh giới của những việc không được làm.
