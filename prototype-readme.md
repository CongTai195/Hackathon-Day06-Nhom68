# Prototype — AI Agent CSKH VinFast

## Mô tả
Chatbot tư vấn xe điện VinFast 24/7 tích hợp LangGraph ReAct Agent. Agent hỏi 3–5 câu về nhu cầu/ngân sách, tra cứu cơ sở dữ liệu xe (JSON), gợi ý 2 dòng xe phù hợp kèm bảng so sánh thông số và giá sơ bộ, đồng thời hỗ trợ đặt lịch bảo dưỡng và giải đáp chính sách thuê pin.

## Level: ☑ Working Prototype

Prototype chạy thật trên terminal CLI với LLM (GPT-4o-mini), LangGraph memory, và 5 tools tích hợp.

## Links
- **Prototype (source code):** Repo này — `agent.py` + `tools.py` + `vinfast_cars.json`
- **Dữ liệu xe:** `vinfast_cars.json` — 6 dòng xe VinFast đầy đủ thông số
- **System prompt:** `system_promt.txt`
- **Chạy thử:** `python3 agent.py` (yêu cầu `OPENAI_API_KEY` trong `.env`)

## Tools & API
| Công cụ | Mô tả |
|--------|-------|
| **LangGraph** (v0.6.11) | ReAct agent orchestration, conversation memory (MemorySaver) |
| **GPT-4o-mini** (OpenAI) | LLM core — inference, intent detection, response generation |
| **LangChain** (v0.3.28) | Tool binding, message management |
| **Python tools tự viết** | `get_vinfast_car_info`, `compare_cars`, `schedule_maintenance`, `get_promotions`, `get_all_cars` |
| **python-dotenv** | Quản lý API key |

## Architecture
```
User (CLI) 
    ↓
agent_node (LLM + Tool Binding)
    ↓ cần tool?
tools_node (5 tools)
    ↓
agent_node (tổng hợp kết quả)
    ↓
User (response)
```
Memory: `MemorySaver` per session — giới hạn 10 lượt Human gần nhất để tránh context drift.

## Phân công

| Thành viên | Role | Output |
|-----------|------|--------|
| **Tài** | Business / PM | Canvas, phân tích failure modes, đánh giá ROI |
| **Sơn** | Product / UX | User stories 4 paths, thiết kế luồng hội thoại |
| **Quang** | Data Engineer | Thu thập & làm sạch `vinfast_cars.json`, cấu hình data pipeline |
| **Tín** | AI / Backend Engineer | Xây dựng `agent.py`, `tools.py`, tích hợp LangGraph + GPT-4o-mini, system prompt engineering |
| **Ngọc** | QA / Frontend | Định nghĩa eval metrics, test bot, thiết kế UI chat demo (Web/Zalo) |

## Cách chạy
```bash
# 1. Kích hoạt virtual environment
source venv/bin/activate

# 2. Cài dependencies
pip install -r requirement.txt

# 3. Tạo file .env với API key
echo "OPENAI_API_KEY=sk-..." > .env

# 4. Chạy agent
python3 agent.py
```
