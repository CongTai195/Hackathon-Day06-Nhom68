import json
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

ANALYSIS_FILE = "feedback_analysis.json"

def analyze_negative_feedback(history: list, session_id: str):
    """
    Thực hiện Root Cause Analysis (RCA) cho tin nhắn bị dislike.
    history: list các tin nhắn từ LangGraph state.
    """
    if not history:
        return

    # Chuẩn bị context cho LLM phân tích
    # Lấy 5 tin nhắn gần nhất để phân tích ngữ cảnh lỗi
    context_msgs = history[-6:] if len(history) > 6 else history
    
    formatted_context = ""
    for msg in context_msgs:
        mtype = getattr(msg, "type", "unknown")
        content = getattr(msg, "content", "")
        formatted_context += f"{mtype.upper()}: {content}\n"

    analysis_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    analysis_prompt = f"""
Bạn là một AI Quality Auditor. Nhiệm vụ của bạn là phân tích tại sao người dùng lại 'Dislike' câu trả lời cuối cùng của AI trong đoạn hội thoại dưới đây.

ĐOẠN HỘI THOẠI:
{formatted_context}

YÊU CẦU:
1. Xác định lỗi chính (VD: Sai số liệu, giọng điệu chưa tốt, không gọi đúng tool, trả lời lan man, hoặc tool trả về lỗi).
2. Đưa ra một "Bài học" (Lesson Learned) ngắn gọn để tránh lặp lại lỗi này.
3. Trả về kết quả dưới dạng JSON:
{{
  "root_cause": "mô tả nguyên nhân",
  "lesson": "câu lệnh/rule ngắn gọn để AI sửa đổi trong tương lai"
}}
"""

    try:
        response = analysis_llm.invoke([HumanMessage(content=analysis_prompt)])
        # Lưu ý: gpt-4o-mini có thể trả về text kèm markdown code blocks
        clean_content = response.content.replace("```json", "").replace("```", "").strip()
        analysis_data = json.loads(clean_content)
        
        # Thêm metadata
        analysis_data["timestamp"] = datetime.now().isoformat()
        analysis_data["session_id"] = session_id
        
        _store_lesson(analysis_data)
        return analysis_data
    except Exception as e:
        print(f"Error in feedback analysis: {e}")
        return None

def _store_lesson(data: dict):
    lessons = []
    if os.path.exists(ANALYSIS_FILE):
        try:
            with open(ANALYSIS_FILE, "r", encoding="utf-8") as f:
                lessons = json.load(f)
        except:
            lessons = []
            
    lessons.append(data)
    
    # Chỉ giữ lại 10 bài học gần nhất để tránh overload context
    lessons = lessons[-10:]
    
    with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)

def get_recent_lessons():
    """Lấy danh sách các bài học gần đây để nạp vào prompt."""
    if not os.path.exists(ANALYSIS_FILE):
        return ""
    
    try:
        with open(ANALYSIS_FILE, "r", encoding="utf-8") as f:
            lessons = json.load(f)
        
        if not lessons:
            return ""
            
        formatted = "\n[BÀI HỌC TỪ PHẢN HỒI TIÊU CỰC TRƯỚC ĐÓ - HÃY TRÁNH CÁC LỖI NÀY]:\n"
        for i, l in enumerate(lessons, 1):
            formatted += f"{i}. Lỗi: {l['root_cause']} -> Khắc phục: {l['lesson']}\n"
        return formatted
    except:
        return ""
