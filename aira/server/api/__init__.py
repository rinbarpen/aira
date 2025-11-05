"""API 服务入口。"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from aira.dialogue.orchestrator import DialogueContext, DialogueOrchestrator

from aira.core.config import ConfigWatcher, get_app_config
from aira.core.logging import setup_logging


def create_app() -> FastAPI:
    config = get_app_config()
    app = FastAPI(title=config["app"]["name"], docs_url="/docs" if config["api"]["docs"] else None)

    orchestrator = DialogueOrchestrator()
    watcher = ConfigWatcher()

    @app.on_event("startup")
    async def on_startup() -> None:
        log_cfg = config.get("logging", {})
        setup_logging(log_cfg.get("output", "logs/aira.log"), log_cfg.get("level", "INFO"))
        await watcher.__aenter__()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await watcher.__aexit__(None, None, None)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/chat")
    async def chat_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        message = payload.get("message")
        if not message:
            raise HTTPException(status_code=422, detail="message 字段不能为空")

        # 检查是否请求流式响应
        use_stream = payload.get("stream", False)
        metadata: dict[str, Any] = dict(payload.get("metadata") or {})
        metadata.setdefault("request_id", payload.get("request_id", "api"))
        if payload.get("language") is not None:
            metadata["language"] = payload.get("language")

        if use_stream:
            # 重定向到流式端点
            from aira.server.api.streaming import generate_stream_response
            from fastapi.responses import StreamingResponse
            
            context = DialogueContext(
                session_id=payload.get("session_id", "default"),
                persona_id=payload.get("persona_id", config["app"]["default_persona"]),
                history=payload.get("history", []),
                metadata=metadata,
            )
            
            return StreamingResponse(
                generate_stream_response(orchestrator, context, message),
                media_type="text/event-stream",
            )
        
        # 常规响应
        context = DialogueContext(
            session_id=payload.get("session_id", "default"),
            persona_id=payload.get("persona_id", config["app"]["default_persona"]),
            history=payload.get("history", []),
            metadata=metadata,
        )
        result = await orchestrator.handle_turn(context, message)
        return result
    
    # 添加文件上传端点
    @app.post("/api/v1/upload")
    async def upload_file(file_type: str = "image") -> dict[str, Any]:
        """文件上传端点（占位实现）。"""
        return {
            "status": "success",
            "file_type": file_type,
            "url": "/uploads/placeholder",
            "message": "文件上传功能待实现"
        }

    return app

