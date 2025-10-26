"""流式响应支持模块。"""

from __future__ import annotations

from typing import Any, AsyncIterator
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from aira.dialogue.orchestrator import DialogueContext, DialogueOrchestrator
from aira.core.config import get_app_config


async def generate_stream_response(
    orchestrator: DialogueOrchestrator,
    context: DialogueContext,
    user_input: str,
) -> AsyncIterator[str]:
    """生成流式响应。
    
    Args:
        orchestrator: 对话编排器
        context: 对话上下文
        user_input: 用户输入
        
    Yields:
        SSE格式的数据块
    """
    try:
        # 这里需要修改orchestrator以支持流式生成
        # 目前先返回模拟的流式响应
        result = await orchestrator.handle_turn(context, user_input)
        reply = result.get("reply", "")
        
        # 将完整响应分块发送（模拟流式）
        chunk_size = 5
        words = reply.split()
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            data = {"chunk": chunk + " "}
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        # 发送完成信号
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_data = {"error": str(e)}
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"


def add_streaming_endpoint(app: FastAPI, orchestrator: DialogueOrchestrator) -> None:
    """添加流式响应端点。
    
    Args:
        app: FastAPI 应用
        orchestrator: 对话编排器
    """
    
    @app.post("/api/v1/chat/stream")
    async def chat_stream_endpoint(payload: dict[str, Any]) -> StreamingResponse:
        """流式聊天端点。"""
        config = get_app_config()
        
        message = payload.get("message")
        if not message:
            return {"error": "message 字段不能为空"}
        
        context = DialogueContext(
            session_id=payload.get("session_id", "default"),
            persona_id=payload.get("persona_id", config["app"]["default_persona"]),
            history=payload.get("history", []),
            metadata={"request_id": payload.get("request_id", "api"), "language": payload.get("language")},
        )
        
        return StreamingResponse(
            generate_stream_response(orchestrator, context, message),
            media_type="text/event-stream",
        )
    
    @app.post("/api/v1/upload")
    async def upload_file_endpoint(file: Any, file_type: str = "image") -> dict[str, Any]:
        """文件上传端点。
        
        Args:
            file: 上传的文件
            file_type: 文件类型
            
        Returns:
            上传结果
        """
        # TODO: 实现文件上传逻辑
        return {
            "status": "success",
            "file_type": file_type,
            "url": "/uploads/placeholder",
        }

