"""
agent.py — AI Agent CSKH VinFast
Kiến trúc: LangGraph ReAct (StateGraph) + GPT-4o-mini + MemorySaver

Aligned với spec-final.md:
  - Augmentation model: AI tư vấn, user + chuyên viên ra quyết định cuối
  - Memory: 10 lượt Human gần nhất (tránh context drift - Failure Mode #3)
  - SOS detection: chuyển escalate_to_human ngay khi phát hiện từ khóa khẩn cấp
  - Logging: in tool calls + tracking fallback để eval Fallback Rate metric
  - Disclaimer: gắn qua tool, không cần nhắc lại trong prompt
"""

from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from tools import agent_tools, SOS_KEYWORDS, _is_sos
from dotenv import load_dotenv

load_dotenv()

# ─── 1. System Prompt ────────────────────────────────────────────────────────
with open("system_promt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# ─── 2. State ────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# ─── 3. LLM + Tools ──────────────────────────────────────────────────────────
tools_list = agent_tools
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
llm_with_tools = llm.bind_tools(tools_list)

# ─── 4. Eval Metric Counters (in-memory, per session) ────────────────────────
# Dùng để track Fallback Rate và Intent Detection cho spec eval metrics
_session_stats = {
    "total_turns": 0,
    "tool_calls": 0,
    "fallback_escalations": 0,
    "sos_triggers": 0,
}

# ─── 5. SOS Pre-check ────────────────────────────────────────────────────────
def _check_sos(user_text: str) -> bool:
    """Kiểm tra từ khóa khẩn cấp (Failure Mode #2 mitigation).
    Nếu phát hiện SOS → AI không cố trả lời → gọi escalate_to_human ngay."""
    return _is_sos(user_text)

# ─── 6. Agent Node ───────────────────────────────────────────────────────────
def agent_node(state: AgentState):
    messages = state["messages"]
    _session_stats["total_turns"] += 1

    # ── Giới hạn context: 10 lượt Human gần nhất (Failure Mode #3 fix) ──────
    human_indices = [i for i, m in enumerate(messages) if getattr(m, "type", "") == "human"]
    if len(human_indices) > 10:
        cutoff_idx = human_indices[-10]
        context_messages = messages[cutoff_idx:]
    else:
        context_messages = list(messages)

    # ── Luôn chèn System Prompt vào đầu context ──────────────────────────────
    if not context_messages or getattr(context_messages[0], "type", "") != "system":
        context_messages = [SystemMessage(content=SYSTEM_PROMPT)] + context_messages

    # ── SOS fast-path: inject tool call hint vào system ─────────────────────
    last_human = next(
        (m for m in reversed(context_messages) if getattr(m, "type", "") == "human"),
        None,
    )
    if last_human and _check_sos(last_human.content):
        _session_stats["sos_triggers"] += 1
        sos_hint = SystemMessage(
            content=(
                "[SYSTEM OVERRIDE] Phát hiện tình huống khẩn cấp/kỹ thuật sâu. "
                "KHÔNG cố đưa ra câu trả lời kỹ thuật. "
                "Gọi NGAY tool `escalate_to_human` với reason là mô tả ngắn vấn đề của khách."
            )
        )
        context_messages = [context_messages[0], sos_hint] + context_messages[1:]

    response = llm_with_tools.invoke(context_messages)

    # ── Logging tool calls ────────────────────────────────────────────────────
    if response.tool_calls:
        _session_stats["tool_calls"] += 1
        for tc in response.tool_calls:
            print(f"  🔄 Tool: {tc['name']}({_fmt_args(tc['args'])})")
            if tc["name"] == "escalate_to_human":
                _session_stats["fallback_escalations"] += 1

    return {"messages": [response]}


def _fmt_args(args: dict) -> str:
    """Format args ngắn gọn cho logging."""
    parts = []
    for k, v in args.items():
        val = str(v)
        if len(val) > 30:
            val = val[:27] + "..."
        parts.append(f"{k}={val!r}")
    return ", ".join(parts)

# ─── 7. Build Graph ──────────────────────────────────────────────────────────
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools_list))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# ─── 8. CLI Chat Loop ─────────────────────────────────────────────────────────
def _print_stats():
    """In eval metrics khi kết thúc session."""
    t = _session_stats["total_turns"]
    if t == 0:
        return
    fallback_rate = _session_stats["fallback_escalations"] / t * 100
    print("\n" + "─" * 55)
    print("📊 Session Stats (Eval Metrics)")
    print(f"   Turns: {t} | Tool calls: {_session_stats['tool_calls']}")
    print(f"   Fallback Rate : {fallback_rate:.1f}% (threshold ≤20%)")
    print(f"   SOS triggers  : {_session_stats['sos_triggers']}")
    print("─" * 55)


if __name__ == "__main__":
    DIVIDER = "=" * 55
    print(DIVIDER)
    print("  VinFast AI — Trợ lý Tư vấn & CSKH Thông minh 🚗⚡")
    print("  Gõ 'quit' hoặc 'q' để thoát | 'stats' để xem metrics")
    print(DIVIDER)

    config = {"configurable": {"thread_id": "vinfast_session_001"}}

    print(
        "\nVinFastAI:\n"
        "Xin chào Anh/Chị! Em là trợ lý ảo của VinFast 🤖\n"
        "Em có thể giúp Anh/Chị:\n"
        "  🚗 Tư vấn chọn xe theo ngân sách & nhu cầu\n"
        "  💰 Tham khảo giá & chính sách thuê pin\n"
        "  🔧 Tra cứu lịch bảo dưỡng định kỳ\n"
        "  📅 Đặt lịch lái thử hoặc bảo dưỡng\n"
        "  📞 Kết nối chuyên viên khi cần\n"
    )

    while True:
        try:
            user_input = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("VinFastAI: Tạm biệt Anh/Chị! Rất vui được hỗ trợ. Chúc Anh/Chị ngày tốt lành! 👋")
            _print_stats()
            break

        if user_input.lower() == "stats":
            _print_stats()
            continue

        print("  ⏳ Đang xử lý...")
        result = graph.invoke({"messages": [("human", user_input)]}, config=config)
        final = result["messages"][-1]
        print(f"\nVinFastAI:\n{final.content}\n")
