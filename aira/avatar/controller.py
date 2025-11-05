"""3D Avatar控制器 - 支持VRoid、Unity3D等3D模型的表情和动作控制。"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

try:
    import aiohttp
except ImportError:
    aiohttp = None  # type: ignore


logger = logging.getLogger(__name__)


class AvatarPlatform(str, Enum):
    """Avatar平台类型。"""
    
    UNITY3D = "unity3d"
    VROID = "vroid"
    LIVE2D = "live2d"
    THREEJS = "threejs"
    CUSTOM = "custom"


class EmotionExpression(str, Enum):
    """情绪表情映射。"""
    
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    CONFUSED = "confused"
    THINKING = "thinking"
    EXCITED = "excited"
    TIRED = "tired"
    SHY = "shy"


class BodyAnimation(str, Enum):
    """身体动画类型。"""
    
    IDLE = "idle"
    WAVE = "wave"
    NOD = "nod"
    SHAKE_HEAD = "shake_head"
    THINKING = "thinking"
    EXCITED = "excited"
    CELEBRATE = "celebrate"
    POINT = "point"
    BOW = "bow"
    CLAP = "clap"
    SHRUG = "shrug"
    TYPING = "typing"


@dataclass
class AvatarAction:
    """Avatar动作定义。"""
    
    expression: EmotionExpression | None = None
    animation: BodyAnimation | None = None
    duration: float = 2.0  # 动作持续时间（秒）
    intensity: float = 1.0  # 强度 (0.0 - 1.0)
    blend: bool = True  # 是否与当前动作混合
    metadata: dict[str, Any] | None = None


@dataclass
class AvatarState:
    """Avatar当前状态。"""
    
    current_expression: EmotionExpression
    current_animation: BodyAnimation
    is_speaking: bool
    lip_sync_enabled: bool
    eye_tracking_enabled: bool
    position: tuple[float, float, float]  # (x, y, z)
    rotation: tuple[float, float, float]  # (pitch, yaw, roll)


class Unity3DAvatarController:
    """Unity3D Avatar控制器 - 通过WebSocket/HTTP与Unity通信。"""
    
    def __init__(self, unity_url: str = "http://localhost:8765"):
        self.unity_url = unity_url
        self.websocket: aiohttp.ClientWebSocketResponse | None = None
        self.session: aiohttp.ClientSession | None = None
        self.current_state = AvatarState(
            current_expression=EmotionExpression.NEUTRAL,
            current_animation=BodyAnimation.IDLE,
            is_speaking=False,
            lip_sync_enabled=True,
            eye_tracking_enabled=True,
            position=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0),
        )
    
    async def connect(self) -> bool:
        """连接到Unity3D实例。"""
        try:
            self.session = aiohttp.ClientSession()
            
            # 尝试WebSocket连接
            ws_url = self.unity_url.replace("http://", "ws://").replace("https://", "wss://")
            self.websocket = await self.session.ws_connect(f"{ws_url}/avatar")
            
            logger.info(f"已连接到Unity3D Avatar: {self.unity_url}")
            return True
        except Exception as e:
            logger.error(f"连接Unity3D失败: {e}")
            return False
    
    async def disconnect(self) -> None:
        """断开连接。"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("已断开Unity3D连接")
    
    async def perform_action(self, action: AvatarAction) -> bool:
        """执行Avatar动作。"""
        try:
            command = {
                "type": "perform_action",
                "action": {
                    "expression": action.expression.value if action.expression else None,
                    "animation": action.animation.value if action.animation else None,
                    "duration": action.duration,
                    "intensity": action.intensity,
                    "blend": action.blend,
                    "metadata": action.metadata or {},
                },
            }
            
            if self.websocket:
                await self.websocket.send_json(command)
            else:
                # 回退到HTTP POST
                async with self.session.post(
                    f"{self.unity_url}/avatar/action", 
                    json=command,
                ) as resp:
                    return resp.status == 200
            
            # 更新状态
            if action.expression:
                self.current_state.current_expression = action.expression
            if action.animation:
                self.current_state.current_animation = action.animation
            
            return True
        except Exception as e:
            logger.error(f"执行Avatar动作失败: {e}")
            return False
    
    async def set_expression(self, expression: EmotionExpression, intensity: float = 1.0) -> bool:
        """设置面部表情。"""
        action = AvatarAction(
            expression=expression,
            intensity=intensity,
            duration=0.5,
        )
        return await self.perform_action(action)
    
    async def play_animation(self, animation: BodyAnimation, duration: float = 2.0) -> bool:
        """播放身体动画。"""
        action = AvatarAction(
            animation=animation,
            duration=duration,
        )
        return await self.perform_action(action)
    
    async def start_speaking(self, audio_data: bytes | None = None) -> bool:
        """开始说话（启动口型同步）。"""
        try:
            command = {
                "type": "start_speaking",
                "audio": None,  # 可以传递音频数据进行唇同步
            }
            
            if self.websocket:
                await self.websocket.send_json(command)
            
            self.current_state.is_speaking = True
            return True
        except Exception as e:
            logger.error(f"启动说话失败: {e}")
            return False
    
    async def stop_speaking(self) -> bool:
        """停止说话。"""
        try:
            command = {"type": "stop_speaking"}
            
            if self.websocket:
                await self.websocket.send_json(command)
            
            self.current_state.is_speaking = False
            return True
        except Exception as e:
            logger.error(f"停止说话失败: {e}")
            return False
    
    async def look_at(self, target: tuple[float, float, float]) -> bool:
        """让Avatar看向某个位置（眼球追踪）。"""
        try:
            command = {
                "type": "look_at",
                "target": {"x": target[0], "y": target[1], "z": target[2]},
            }
            
            if self.websocket:
                await self.websocket.send_json(command)
            
            return True
        except Exception as e:
            logger.error(f"设置视线失败: {e}")
            return False


class VRoidAvatarController:
    """VRoid Avatar控制器 - 兼容VRoid Hub和VRM格式。"""
    
    def __init__(self, vrm_file_path: str | None = None):
        self.vrm_file_path = vrm_file_path
        self.unity_controller = Unity3DAvatarController()  # 内部使用Unity渲染
        
    async def load_model(self, vrm_path: str) -> bool:
        """加载VRM模型。"""
        self.vrm_file_path = vrm_path
        # 通知Unity加载VRM
        try:
            command = {
                "type": "load_vrm",
                "path": vrm_path,
            }
            if self.unity_controller.websocket:
                await self.unity_controller.websocket.send_json(command)
            logger.info(f"已加载VRM模型: {vrm_path}")
            return True
        except Exception as e:
            logger.error(f"加载VRM模型失败: {e}")
            return False
    
    async def perform_action(self, action: AvatarAction) -> bool:
        """执行动作（委托给Unity控制器）。"""
        return await self.unity_controller.perform_action(action)


class AvatarManager:
    """Avatar管理器 - 统一管理多种平台的Avatar控制。"""
    
    def __init__(self):
        self.controllers: dict[str, Unity3DAvatarController | VRoidAvatarController] = {}
        self.active_controller: str | None = None
        self._emotion_mapping = self._build_emotion_mapping()
    
    def _build_emotion_mapping(self) -> dict[str, EmotionExpression]:
        """构建情绪到表情的映射。"""
        return {
            "happy": EmotionExpression.HAPPY,
            "sad": EmotionExpression.SAD,
            "angry": EmotionExpression.ANGRY,
            "surprised": EmotionExpression.SURPRISED,
            "neutral": EmotionExpression.NEUTRAL,
            "tired": EmotionExpression.TIRED,
            "focused": EmotionExpression.THINKING,
            "fearful": EmotionExpression.CONFUSED,
        }
    
    async def register_controller(
        self, 
        name: str, 
        platform: AvatarPlatform,
        **kwargs: Any,
    ) -> bool:
        """注册一个Avatar控制器。"""
        try:
            if platform == AvatarPlatform.UNITY3D:
                controller = Unity3DAvatarController(
                    unity_url=kwargs.get("unity_url", "http://localhost:8765")
                )
            elif platform == AvatarPlatform.VROID:
                controller = VRoidAvatarController(
                    vrm_file_path=kwargs.get("vrm_file_path")
                )
            else:
                logger.warning(f"不支持的平台: {platform}")
                return False
            
            # 连接
            if hasattr(controller, "connect"):
                await controller.connect()
            
            self.controllers[name] = controller
            
            if self.active_controller is None:
                self.active_controller = name
            
            logger.info(f"已注册Avatar控制器: {name} ({platform})")
            return True
        except Exception as e:
            logger.error(f"注册控制器失败: {e}")
            return False
    
    def set_active_controller(self, name: str) -> bool:
        """设置活动的控制器。"""
        if name not in self.controllers:
            logger.warning(f"控制器不存在: {name}")
            return False
        
        self.active_controller = name
        logger.info(f"切换到控制器: {name}")
        return True
    
    async def express_emotion(
        self, 
        emotion: str, 
        intensity: float = 1.0,
        controller_name: str | None = None,
    ) -> bool:
        """根据情绪名称设置表情。"""
        controller_name = controller_name or self.active_controller
        if not controller_name or controller_name not in self.controllers:
            return False
        
        expression = self._emotion_mapping.get(emotion.lower(), EmotionExpression.NEUTRAL)
        controller = self.controllers[controller_name]
        
        if hasattr(controller, "set_expression"):
            return await controller.set_expression(expression, intensity)
        else:
            action = AvatarAction(expression=expression, intensity=intensity)
            return await controller.perform_action(action)
    
    async def perform_gesture(
        self, 
        gesture: str,
        controller_name: str | None = None,
    ) -> bool:
        """执行手势动作。"""
        controller_name = controller_name or self.active_controller
        if not controller_name or controller_name not in self.controllers:
            return False
        
        # 映射手势名称到动画
        gesture_map = {
            "wave": BodyAnimation.WAVE,
            "nod": BodyAnimation.NOD,
            "shake_head": BodyAnimation.SHAKE_HEAD,
            "thinking": BodyAnimation.THINKING,
            "celebrate": BodyAnimation.CELEBRATE,
            "point": BodyAnimation.POINT,
            "bow": BodyAnimation.BOW,
            "clap": BodyAnimation.CLAP,
            "shrug": BodyAnimation.SHRUG,
        }
        
        animation = gesture_map.get(gesture.lower(), BodyAnimation.IDLE)
        controller = self.controllers[controller_name]
        
        if hasattr(controller, "play_animation"):
            return await controller.play_animation(animation)
        else:
            action = AvatarAction(animation=animation)
            return await controller.perform_action(action)
    
    async def sync_with_speech(
        self, 
        text: str,
        audio_data: bytes | None = None,
        controller_name: str | None = None,
    ) -> bool:
        """与语音同步（启用口型同步）。"""
        controller_name = controller_name or self.active_controller
        if not controller_name or controller_name not in self.controllers:
            return False
        
        controller = self.controllers[controller_name]
        
        if hasattr(controller, "start_speaking"):
            await controller.start_speaking(audio_data)
            # 模拟说话时长
            duration = len(text) * 0.1  # 假设每个字0.1秒
            await asyncio.sleep(duration)
            await controller.stop_speaking()
            return True
        
        return False
    
    async def react_to_user_state(
        self, 
        user_emotion: str,
        user_posture: str,
        engagement_level: float,
    ) -> bool:
        """根据用户状态做出反应。"""
        # 如果用户疲劳，表现出关心
        if "tired" in user_emotion.lower() or engagement_level < 0.3:
            await self.express_emotion("concerned", 0.8)
            await self.perform_gesture("thinking")
            return True
        
        # 如果用户高兴，回应高兴
        if "happy" in user_emotion.lower():
            await self.express_emotion("happy", 1.0)
            await self.perform_gesture("wave")
            return True
        
        # 如果用户专注（前倾），保持中性并点头
        if "forward" in user_posture.lower():
            await self.express_emotion("neutral", 0.7)
            await self.perform_gesture("nod")
            return True
        
        return False
    
    async def cleanup(self) -> None:
        """清理所有控制器。"""
        for controller in self.controllers.values():
            if hasattr(controller, "disconnect"):
                await controller.disconnect()
        
        self.controllers.clear()
        self.active_controller = None
        logger.info("Avatar管理器已清理")

