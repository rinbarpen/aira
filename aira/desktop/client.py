"""API 客户端用于与后端通信。"""

from __future__ import annotations

from typing import Any, AsyncIterator
import asyncio
from pathlib import Path
import json

import httpx
from PyQt6.QtCore import QObject, pyqtSignal


class ApiClient(QObject):
    """AIRA API 客户端。"""
    
    # 定义信号
    message_received = pyqtSignal(dict)
    stream_chunk_received = pyqtSignal(str)  # 流式响应片段
    error_occurred = pyqtSignal(str)
    connection_status_changed = pyqtSignal(bool)

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        """初始化 API 客户端。
        
        Args:
            base_url: 后端 API 的基础 URL
        """
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self._connected = False

    async def check_health(self) -> bool:
        """检查后端健康状态。"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            is_healthy = response.status_code == 200 and response.json().get("status") == "ok"
            if is_healthy != self._connected:
                self._connected = is_healthy
                self.connection_status_changed.emit(is_healthy)
            return is_healthy
        except Exception as e:
            if self._connected:
                self._connected = False
                self.connection_status_changed.emit(False)
            self.error_occurred.emit(f"连接失败: {str(e)}")
            return False

    async def send_message(
        self,
        message: str,
        session_id: str = "default",
        persona_id: str = "aira",
        history: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        stream: bool = False,
        language: str | None = None,
    ) -> dict[str, Any] | None:
        """发送消息到后端。
        
        Args:
            message: 用户消息
            session_id: 会话 ID
            persona_id: 角色 ID
            history: 对话历史
            metadata: 元数据
            stream: 是否使用流式响应
            language: 回复语言（zh/en等）
            
        Returns:
            后端响应或 None（如果出错）
        """
        try:
            payload = {
                "message": message,
                "session_id": session_id,
                "persona_id": persona_id,
                "history": history or [],
                "metadata": metadata or {},
                "stream": stream,
            }
            
            if language:
                payload["language"] = language
            
            if stream:
                # 流式响应
                return await self._send_stream_message(payload)
            else:
                # 常规响应
                response = await self.client.post(
                    f"{self.base_url}/api/v1/chat",
                    json=payload,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.message_received.emit(result)
                    return result
                else:
                    error_msg = f"请求失败 (状态码 {response.status_code}): {response.text}"
                    self.error_occurred.emit(error_msg)
                    return None
                
        except Exception as e:
            error_msg = f"发送消息时出错: {str(e)}"
            self.error_occurred.emit(error_msg)
            return None

    async def _send_stream_message(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """发送流式消息请求。
        
        Args:
            payload: 请求负载
            
        Returns:
            完整响应
        """
        try:
            full_response = ""
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/v1/chat",
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_msg = f"请求失败 (状态码 {response.status_code})"
                    self.error_occurred.emit(error_msg)
                    return None
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            chunk = data.get("chunk", "")
                            if chunk:
                                full_response += chunk
                                self.stream_chunk_received.emit(chunk)
                        except json.JSONDecodeError:
                            continue
            
            result = {"reply": full_response, "session_id": payload["session_id"]}
            self.message_received.emit(result)
            return result
            
        except Exception as e:
            error_msg = f"流式请求失败: {str(e)}"
            self.error_occurred.emit(error_msg)
            return None

    async def upload_file(
        self,
        file_path: str,
        file_type: str = "image",
    ) -> dict[str, Any] | None:
        """上传文件。
        
        Args:
            file_path: 文件路径
            file_type: 文件类型（image/audio/document）
            
        Returns:
            上传结果
        """
        try:
            files = {"file": open(file_path, "rb")}
            data = {"type": file_type}
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/upload",
                files=files,
                data=data,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"上传失败 (状态码 {response.status_code}): {response.text}"
                self.error_occurred.emit(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"上传文件时出错: {str(e)}"
            self.error_occurred.emit(error_msg)
            return None

    async def get_conversation_history(self, session_id: str) -> list[dict[str, Any]]:
        """获取会话历史（需要后端支持该端点）。
        
        Args:
            session_id: 会话 ID
            
        Returns:
            对话历史列表
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/conversation/{session_id}"
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.error_occurred.emit(f"获取历史记录失败: {str(e)}")
            return []

    async def close(self) -> None:
        """关闭客户端连接。"""
        await self.client.aclose()

    def is_connected(self) -> bool:
        """返回连接状态。"""
        return self._connected

