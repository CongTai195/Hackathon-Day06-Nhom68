"""
server.py — FastAPI backend cho VinFast AI Chat UI
Endpoints:
  POST /api/chat      — gửi tin nhắn, nhận trả lời từ agent
  GET  /api/stats     — lấy session stats (eval metrics)
  POST /api/reset     — reset session mới
  GET  /              — serve index.html
"""

import uuid
import os
import re
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Import agent logic từ agent.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from tools import agent_tools, _is_sos
from feedback_handler import analyze_negative_feedback, get_recent_lessons
from dotenv import load_dotenv

load_dotenv()

# ─── Agent Setup ─────────────────────────────────────────────────────────────
with open("system_promt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

tools_list = agent_tools
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
llm_with_tools = llm.bind_tools(tools_list)

def agent_node(state: AgentState):
    messages = state["messages"]
    human_indices = [i for i, m in enumerate(messages) if getattr(m, "type", "") == "human"]
    if len(human_indices) > 10:
        cutoff_idx = human_indices[-10]
        context_messages = messages[cutoff_idx:]
    else:
        context_messages = list(messages)

    lessons_learned = get_recent_lessons()
    DYNAMIC_PROMPT = SYSTEM_PROMPT + lessons_learned

    if not context_messages or getattr(context_messages[0], "type", "") != "system":
        context_messages = [SystemMessage(content=DYNAMIC_PROMPT)] + context_messages

    last_human = next(
        (m for m in reversed(context_messages) if getattr(m, "type", "") == "human"), None
    )
    if last_human and _is_sos(last_human.content):
        sos_hint = SystemMessage(
            content=(
                "[SYSTEM OVERRIDE] Tình huống khẩn cấp/kỹ thuật sâu. "
                "Gọi NGAY tool `escalate_to_human` với reason mô tả ngắn vấn đề."
            )
        )
        context_messages = [context_messages[0], sos_hint] + context_messages[1:]

    response = llm_with_tools.invoke(context_messages)
    return {"messages": [response]}

builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools_list))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# ─── Session Stats ────────────────────────────────────────────────────────────
sessions: dict[str, dict] = {}

def get_or_create_session(session_id: str) -> dict:
    if session_id not in sessions:
        sessions[session_id] = {
            "total_turns": 0,
            "tool_calls_made": [],
            "fallback_count": 0,
            "sos_count": 0,
            "feedback": {"likes": 0, "dislikes": 0},
        }
    return sessions[session_id]

# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(title="VinFast AI Chat", version="1.0.0")

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

_OPTIONS_RE = re.compile(r'\[OPTIONS:\s*(.+?)\]\s*$', re.IGNORECASE | re.DOTALL)

def parse_choices(raw_reply: str) -> tuple[str, list[str]]:
    match = _OPTIONS_RE.search(raw_reply)
    if not match:
        return raw_reply, []
    options = [o.strip() for o in match.group(1).split('|') if o.strip()]
    clean = raw_reply[:match.start()].rstrip()
    return clean, options if len(options) >= 2 else []

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    tool_calls: list[str]
    is_escalation: bool
    is_sos: bool
    choices: list[str] = []

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    stats = get_or_create_session(session_id)
    stats["total_turns"] += 1

    sos_detected = _is_sos(req.message)
    if sos_detected:
        stats["sos_count"] += 1

    config = {"configurable": {"thread_id": session_id}}
    try:
        result = graph.invoke({"messages": [("human", req.message)]}, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    messages = result["messages"]
    final = messages[-1]

    # Collect tool calls from all intermediate messages
    tool_calls_made = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_made.append(tc["name"])
                stats["tool_calls_made"].append(tc["name"])
                if tc["name"] == "escalate_to_human":
                    stats["fallback_count"] += 1

    is_escalation = "escalate_to_human" in tool_calls_made

    raw_reply = final.content
    clean_reply, choices = parse_choices(raw_reply)

    return ChatResponse(
        reply=clean_reply,
        session_id=session_id,
        tool_calls=tool_calls_made,
        is_escalation=is_escalation,
        is_sos=sos_detected,
        choices=choices,
    )

@app.get("/api/stats")
async def get_stats(session_id: str):
    stats = sessions.get(session_id, {})
    total = stats.get("total_turns", 0)
    fallback = stats.get("fallback_count", 0)
    fallback_rate = (fallback / total * 100) if total > 0 else 0
    return {
        "session_id": session_id,
        "total_turns": total,
        "fallback_count": fallback,
        "fallback_rate_pct": round(fallback_rate, 1),
        "fallback_threshold_pct": 20,
        "sos_count": stats.get("sos_count", 0),
        "tool_calls_made": stats.get("tool_calls_made", []),
        "feedback": stats.get("feedback", {"likes": 0, "dislikes": 0}),
        "status": "🟢 OK" if fallback_rate <= 20 else "🔴 HIGH FALLBACK",
    }

@app.post("/api/reset")
async def reset_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "reset", "new_session_id": str(uuid.uuid4())}

class FeedbackRequest(BaseModel):
    session_id: str
    msg_id: str
    score: int  # 1 = like, 0 = dislike

@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    stats = get_or_create_session(req.session_id)
    if req.score == 1:
        stats["feedback"]["likes"] += 1
    else:
        stats["feedback"]["dislikes"] += 1
        # Tự động phân tích nguyên nhân khi có Dislike
        try:
            config = {"configurable": {"thread_id": req.session_id}}
            state = graph.get_state(config)
            history = state.values.get("messages", [])
            analyze_negative_feedback(history, req.session_id)
        except Exception as e:
            print(f"Feedback RCA Error: {e}")

    return {"status": "recorded", "msg_id": req.msg_id, "score": req.score}

# Serve static UI
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    print("🚀 VinFast AI Chat UI → http://localhost:8080")
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
