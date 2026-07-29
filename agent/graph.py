"""
LangGraph ReAct Agent Architecture for DataMind AI using Groq Cloud.
"""
from typing import Dict, Any, List, TypedDict, Annotated, Optional
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition

from core.config import settings
from core.logger import logger
from agent.prompts import AGENT_SYSTEM_PROMPT
from agent.tools import ALL_AGENT_TOOLS

def is_general_chat(query: str) -> bool:
    query = query.lower().strip()

    general_phrases = [
        "hi", "hello", "hey",
        "how are you",
        "who are you",
        "what can you do",
        "thanks", "thank you",
        "good morning",
        "good evening",
        "bye",
        "good night"
    ]

    return any(query == phrase or query.startswith(phrase) for phrase in general_phrases)
    
# State Schema for LangGraph
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    reasoning: Optional[str]
    chart_spec: Optional[Dict[str, Any]]
    sql_executed: Optional[str]


import os


def create_agent_graph():
    """Builds and compiles the LangGraph ReAct StateGraph."""
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or "your_groq_api_key_here"
    base_url = settings.GROQ_BASE_URL or os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
    model_name = settings.MODEL_NAME or os.getenv("MODEL_NAME") or "llama-3.3-70b-versatile"
    
    # 1. Initialize Groq LLM via ChatOpenAI
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,  # type: ignore
        base_url=base_url,  # type: ignore
        temperature=0,
        streaming=True
    )


    # 2. Bind Tools
    llm_with_tools = llm.bind_tools(ALL_AGENT_TOOLS)

    # 3. Define Nodes
    def agent_node(state: AgentState) -> Dict[str, Any]:
        """Core ReAct LLM Agent Node."""
        messages = state["messages"]
        session_id = state.get("session_id", "default")
        
        # Inject System Prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            system_msg = SystemMessage(content=f"{AGENT_SYSTEM_PROMPT}\nActive Session ID: {session_id}")
            messages = [system_msg] + messages
 
        logger.info(f"Agent Node invoking Groq LLM for session {session_id}")
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(ALL_AGENT_TOOLS)

    # 4. Construct Graph Workflow
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    # 5. Checkpointer Memory
    checkpointer = MemorySaver()
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    return compiled_graph


# Singleton Graph Instance
agent_graph = create_agent_graph()


def run_agent_query(session_id: str, query: str) -> Dict[str, Any]:
    """
    Executes a multi-turn query through the LangGraph ReAct agent.
    Returns response text, reasoning explanation, chart spec, and generated SQL/Pandas code.
    """
    config = {"configurable": {"thread_id": session_id}}

    inputs = {
        "messages": [HumanMessage(content=f"[Session ID: {session_id}] {query}")],
        "session_id": session_id
    }

    logger.info(f"Running agent query for session '{session_id}': '{query}'")


    reasoning_text = f"Analyzed dataset using ReAct reasoning loop to answer: '{query}'."
    chart_spec = None
    sql_executed = None

    final_state = agent_graph.invoke(inputs, config=config)  # type: ignore
    messages = final_state.get("messages", [])

    # Inspect messages to extract reasoning, charts, and executed SQL
    last_ai_message = ""
    pandas_code = None
    for msg in messages:
        if isinstance(msg, AIMessage):
            if msg.content:
                last_ai_message = msg.content
        elif hasattr(msg, "name") and msg.name == "generate_chart_tool":
            try:
                chart_data = json.loads(msg.content)
                if chart_data.get("status") == "success":
                    chart_spec = chart_data.get("chart_spec")
            except Exception:
                pass
        elif hasattr(msg, "name") and msg.name == "query_data_tool":
            try:
                sql_data = json.loads(msg.content)
                if sql_data.get("sql_executed"):
                    sql_executed = sql_data.get("sql_executed")
            except Exception:
                pass
        elif hasattr(msg, "name") and msg.name == "sql_generation_tool":
            try:
                gen_data = json.loads(msg.content)
                if gen_data.get("generated_pandas"):
                    pandas_code = gen_data.get("generated_pandas")
            except Exception:
                pass

    if not reasoning_text:
        reasoning_text = f"Selected tools to inspect session '{session_id}' schema, compute relevant aggregates, and format output."

    return {
        "text": last_ai_message,
        "reasoning": reasoning_text,
        "chart_spec": chart_spec,
        "sql_code": sql_executed,
        "pandas_code": pandas_code
    }
