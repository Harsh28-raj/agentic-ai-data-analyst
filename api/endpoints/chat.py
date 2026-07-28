"""
Chat and Query API Endpoints for DataMind AI.
"""
import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse

from core.session import session_store
from core.logger import logger
from agent.graph import run_agent_query
from agent.tools import anomaly_detection_tool
from api.schemas import (
    ChatRequest,
    ChatResponse,
    AnomalyRequest,
    AnomalyResponse,
    SessionHistoryResponse,
    QueryCsvRequest
)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{request.session_id}' not found.")

    try:
        agent_result = run_agent_query(request.session_id, request.query)
        session.history.append({"role": "user", "content": request.query})
        session.history.append({"role": "assistant", "content": agent_result["text"], "reasoning": agent_result["reasoning"]})

        return ChatResponse(
            session_id=request.session_id,
            response_text=agent_result["text"],
            reasoning=agent_result["reasoning"],
            chart_spec=agent_result.get("chart_spec"),
            sql_code=agent_result.get("sql_code"),
            pandas_code=agent_result.get("pandas_code")
        )
    except Exception as e:
        logger.error(f"Chat execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution error: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{request.session_id}' not found.")

    async def event_generator():
        try:
            yield f"data: {{'type': 'reasoning', 'content': 'Analyzing request: {request.query}'}}\\n\\n"
            await asyncio.sleep(0.05)
            agent_result = await asyncio.to_thread(run_agent_query, request.session_id, request.query)

            tokens = agent_result["text"].split(" ")
            for token in tokens:
                yield f"data: {json.dumps({'type': 'token', 'content': token + ' '})}\\n\\n"
                await asyncio.sleep(0.02)

            if agent_result.get("chart_spec"):
                yield f"data: {json.dumps({'type': 'chart', 'data': agent_result['chart_spec']})}\\n\\n"
            if agent_result.get("sql_code"):
                yield f"data: {json.dumps({'type': 'sql', 'content': agent_result['sql_code']})}\\n\\n"
            if agent_result.get("pandas_code"):
                yield f"data: {json.dumps({'type': 'pandas', 'content': agent_result['pandas_code']})}\\n\\n"

            yield f"data: {json.dumps({'type': 'complete', 'reasoning': agent_result['reasoning']})}\\n\\n"
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\\n\\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/anomalies", response_model=AnomalyResponse)
async def detect_anomalies(request: AnomalyRequest):
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{request.session_id}' not found.")

    try:
        tool_result = anomaly_detection_tool.invoke({
            "session_id": request.session_id,
            "table_name": request.table_name,
            "column_name": request.column_name
        })
        
        result_data = json.loads(tool_result)
        if result_data.get("status") == "error":
            raise HTTPException(status_code=400, detail=result_data.get("message"))

        return AnomalyResponse(
            session_id=request.session_id,
            table_name=result_data.get("table_name", "unknown"),
            total_anomalies_flagged=result_data.get("total_anomalies_flagged", 0),
            flagged_rows=result_data.get("flagged_rows", []),
            business_explanation=result_data.get("business_explanation", "")
        )
    except Exception as e:
        logger.error(f"Anomaly detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    return SessionHistoryResponse(
        session_id=session_id,
        message_count=len(session.history),
        history=session.history
    )


@router.post("/query/csv", response_class=PlainTextResponse)
async def query_csv(request: QueryCsvRequest):
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{request.session_id}' not found.")

    try:
        df = session.duckdb_mgr.execute_sql(request.sql_code)
        if df is None or df.empty:
            return "No results found."
        return df.to_csv(index=False)
    except Exception as e:
        logger.error(f"Error executing CSV query: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error executing SQL: {str(e)}")
