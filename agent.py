from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from tools import agent_tools
from dotenv import load_dotenv

load_dotenv()

# 1. Đọc System Prompt (chú ý đúng tên file bạn đang dùng)
with open("system_promt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# 2. Khai báo State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Khởi tạo LLM và Tools (Sử dụng đúng agent_tools của VinFast)
tools_list = agent_tools
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools_list)

# 4. Agent Node
def agent_node(state: AgentState):
    messages = state["messages"]
    
    # Giới hạn bộ nhớ: Lọc lấy tối đa 10 lượt chat gần nhất từ Human
    human_indices = [i for i, m in enumerate(messages) if getattr(m, 'type', '') == 'human']
    if len(human_indices) > 10:
        cutoff_idx = human_indices[-10]
        context_messages = messages[cutoff_idx:]
    else:
        context_messages = messages[:]
        
    # Kiểm tra và chèn system prompt vào đầu context để LLM luôn nhớ System Role
    if not context_messages or getattr(context_messages[0], "type", "") != "system":
        context_messages = [SystemMessage(content=SYSTEM_PROMPT)] + context_messages

    response = llm_with_tools.invoke(context_messages)

    # === LOGGING ===
    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"🔄 Đang gọi tool: {tc['name']} với args: {tc['args']}")
    else:
        pass # Trả lời trực tiếp thì không in gì để giữ luồng sạch đẹp cho CLI

    return {"messages": [response]}

# 5. Xây dựng Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

# Khai báo edges thiết lập vòng lặp ReAct
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# 6. Chat loop
if __name__ == "__main__":
    print("=" * 60)
    print("VinFastAI - Trợ lý Bán Hàng & Dịch Vụ Thông minh")
    print("  Gõ 'quit' hoặc 'q' để thoát")
    print("=" * 60)

    # Thread ID dùng để nhớ context hội thoại, mỗi user sẽ có thread_id riêng
    config = {"configurable": {"thread_id": "session_mem_vf1"}}

    # Mở đầu bằng một lời chào mẫu
    print("\nVinFastAI:\nXin chào Anh/Chị! Em là trợ lý ảo chính thức của VinFast. Em có thể hỗ trợ Anh/Chị tìm hiểu mua xe, tham khảo chính sách thuê pin, hay đặt lịch bảo dưỡng ạ?")
    
    while True:
        user_input = input("\nBạn: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            print("VinFastAI: Tạm biệt Anh/Chị. Rất mong được phục vụ Anh/Chị lần sau!")
            break
        if not user_input:
            continue

        print("\n[ VinFastAI đang xử lý... ]")
        result = graph.invoke({"messages": [("human", user_input)]}, config=config)
        
        final = result["messages"][-1]
        print(f"\nVinFastAI:\n{final.content}")
