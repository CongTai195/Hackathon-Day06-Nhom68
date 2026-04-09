# Individual Reflection — [Họ Tên] ([Mã Học Viên])

> **Note:** Anh điền tên và mã học viên vào dòng trên trước khi nộp.

---

## 1. Role cụ thể trong nhóm

**AI / Backend Engineer** — Phụ trách thiết kế và xây dựng lõi AI của prototype: LangGraph agent, tool integration, và system prompt engineering.

---

## 2. Phần phụ trách cụ thể (output rõ ràng)

1. **Xây dựng `agent.py`:** Triển khai LangGraph StateGraph với ReAct loop (agent node → tools node → agent node), tích hợp MemorySaver để giữ context 10 lượt gần nhất, bind tools vào LLM.

2. **Viết `tools.py`:** Định nghĩa 5 Python tools (`get_vinfast_car_info`, `compare_cars`, `schedule_maintenance`, `get_promotions`, `get_all_cars`) với description rõ ràng để LLM biết khi nào gọi tool nào.

3. **System prompt engineering (`system_promt.txt`):** Viết và iterate system prompt để agent giữ đúng vai trò tư vấn viên VinFast, không hallucinate thông tin ngoài data source, và luôn kèm disclaimer khi đưa thông tin giá.

---

## 3. SPEC phần nào mạnh nhất, phần nào yếu nhất?

**Mạnh nhất: Phần 4 — Failure Modes.**
Nhóm identify được failure mode nguy hiểm nhất không phải là "AI không biết", mà là "AI biết sai nhưng tự tin cao" (hallucinate giá/chính sách). Từ đó thiết kế mitigation cụ thể: disclaimer timestamp + flag data stale → trigger update.

**Yếu nhất: Phần 5 — ROI 3 kịch bản.**
Ba kịch bản khác nhau chủ yếu ở số lượng user, assumption giữ nguyên nhau quá nhiều. Kịch bản conservative và realistic chỉ scale số lượng, không tách được assumption thực sự khác nhau (VD: conservative = 1 đại lý pilot với CSKH được training, optimistic = self-serve không cần CSKH). Cần refine thêm.

---

## 4. Đóng góp cụ thể khác

- **Debug context drift:** Phát hiện và fix bug agent quên budget constraint của user sau 8+ lượt chat. Giải pháp: slice messages về 10 lượt gần nhất + luôn prepend SystemMessage vào đầu context slice.
- **Test các edge cases:** Chạy thử 15+ scenario khác nhau (câu hỏi out-of-scope, câu tiếng Anh, câu hỏi kỹ thuật sâu) và ghi nhận failure patterns để bổ sung vào spec.

---

## 5. 1 điều học được trong hackathon mà trước đó chưa biết

Trước hackathon, em nghĩ LangGraph chỉ là một layer orchestration đơn giản trên LangChain. Sau khi build prototype mới hiểu: **StateGraph là vòng lặp có điều kiện**, không phải pipeline tuyến tính. Việc thiết kế `tools_condition` để quyết định khi nào quay lại agent, khi nào kết thúc — đây là phần logic sản phẩm thực sự, không chỉ là kỹ thuật. Một tool description viết không rõ → LLM gọi sai tool → user experience tệ → đây là product decision, không phải engineering decision.

---

## 6. Nếu làm lại, đổi gì?

Sẽ **test system prompt sớm hơn với adversarial cases** (câu hỏi bẫy agent đưa thông tin ngoài data source) ngay từ tối D5. Thực tế đến sáng D6 mới bắt đầu test nghiêm túc, phát hiện ra agent hay hallucinate giá khi không tìm thấy dữ liệu chính xác. Nếu test sớm 1 ngày, có thể iterate thêm 3–4 vòng prompt và thiết kế tool schema tốt hơn (cụ thể: thêm trường `data_updated_at` vào JSON để agent biết khi nào data stale).

---

## 7. AI giúp gì? AI sai/mislead ở đâu?

**AI giúp:**
- Dùng Claude để brainstorm failure modes — AI gợi ý được case "user hỏi bằng tiếng Anh mixed với tiếng Việt" và "user báo triệu chứng kỹ thuật sâu" mà nhóm chưa nghĩ đến.
- Dùng GPT-4 để draft system prompt ban đầu — tiết kiệm ~1h so với viết từ đầu.
- GitHub Copilot giúp autocomplete boilerplate LangGraph code nhanh.

**AI sai/mislead:**
- Claude gợi ý thêm feature "tích hợp live chat với đại lý" và "lịch sử mua hàng của user" vào prototype — nghe hay nhưng scope quá lớn cho 1 ngày hackathon. Suýt bị scope creep nếu không dừng lại kịp.
- GPT-4 draft system prompt ban đầu có đoạn "Bạn có thể ước tính giá nếu chưa có data" → đây là instruction nguy hiểm, phải sửa lại thành "Chỉ trả lời dựa trên data có sẵn, không ước tính giá".
- **Bài học:** AI rất giỏi brainstorm và draft, nhưng không biết constraint của scope và không hiểu risk đặc thù của domain (tài chính/giá cả). Phải review kỹ mọi output AI trước khi dùng.
