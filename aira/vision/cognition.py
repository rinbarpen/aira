"""视觉认知模块 - 通过摄像头识别用户状态（表情、姿态）。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore

try:
    import mediapipe as mp
except ImportError:
    mp = None  # type: ignore

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore


logger = logging.getLogger(__name__)


class EmotionState(str, Enum):
    """情绪状态枚举。"""
    
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    FOCUSED = "focused"
    TIRED = "tired"


class PostureState(str, Enum):
    """姿态状态枚举。"""
    
    UPRIGHT = "upright"  # 端正坐姿
    SLOUCHING = "slouching"  # 懒散
    LEANING_FORWARD = "leaning_forward"  # 前倾（专注）
    LEANING_BACK = "leaning_back"  # 后仰（放松）
    TILTED = "tilted"  # 歪头
    STANDING = "standing"  # 站立
    UNKNOWN = "unknown"


@dataclass
class UserState:
    """用户状态综合信息。"""
    
    emotion: EmotionState
    emotion_confidence: float
    posture: PostureState
    posture_confidence: float
    engagement_level: float  # 参与度 (0.0 - 1.0)
    fatigue_level: float  # 疲劳度 (0.0 - 1.0)
    distance: float  # 距离相机的距离（相对值）
    face_detected: bool
    metadata: dict[str, Any]


class VisionCognitionSystem:
    """视觉认知系统 - 识别用户表情和姿态。"""
    
    def __init__(
        self, 
        camera_id: int = 0,
        enable_emotion: bool = True,
        enable_posture: bool = True,
    ):
        self.camera_id = camera_id
        self.enable_emotion = enable_emotion
        self.enable_posture = enable_posture
        
        # 初始化摄像头
        self.cap: cv2.VideoCapture | None = None
        
        # 初始化MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_pose = mp.solutions.pose
        self.mp_hands = mp.solutions.hands
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) if enable_emotion else None
        
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) if enable_posture else None
        
        # 历史状态（用于平滑）
        self.emotion_history: list[EmotionState] = []
        self.posture_history: list[PostureState] = []
        self.max_history = 5
    
    def start_capture(self) -> bool:
        """启动摄像头捕获。"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                logger.error(f"无法打开摄像头 {self.camera_id}")
                return False
            logger.info(f"摄像头 {self.camera_id} 已启动")
            return True
        except Exception as e:
            logger.error(f"启动摄像头失败: {e}")
            return False
    
    def stop_capture(self) -> None:
        """停止摄像头捕获。"""
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("摄像头已停止")
    
    def capture_user_state(self) -> UserState | None:
        """捕获并分析当前用户状态。"""
        if not self.cap or not self.cap.isOpened():
            if not self.start_capture():
                return None
        
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("无法读取摄像头帧")
            return None
        
        # 转换为RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 分析表情
        emotion = EmotionState.NEUTRAL
        emotion_confidence = 0.0
        face_detected = False
        distance = 1.0
        
        if self.enable_emotion and self.face_mesh:
            emotion, emotion_confidence, face_detected, distance = self._analyze_emotion(frame_rgb)
        
        # 分析姿态
        posture = PostureState.UNKNOWN
        posture_confidence = 0.0
        
        if self.enable_posture and self.pose:
            posture, posture_confidence = self._analyze_posture(frame_rgb)
        
        # 计算参与度和疲劳度
        engagement_level = self._calculate_engagement(emotion, posture, face_detected)
        fatigue_level = self._calculate_fatigue(emotion, posture)
        
        return UserState(
            emotion=emotion,
            emotion_confidence=emotion_confidence,
            posture=posture,
            posture_confidence=posture_confidence,
            engagement_level=engagement_level,
            fatigue_level=fatigue_level,
            distance=distance,
            face_detected=face_detected,
            metadata={
                "frame_shape": frame.shape,
                "timestamp": cv2.getTickCount(),
            },
        )
    
    def _analyze_emotion(self, frame_rgb: np.ndarray) -> tuple[EmotionState, float, bool, float]:
        """分析面部表情。
        
        Returns:
            (emotion, confidence, face_detected, distance)
        """
        if not self.face_mesh:
            return EmotionState.NEUTRAL, 0.0, False, 1.0
        
        results = self.face_mesh.process(frame_rgb)
        
        if not results.multi_face_landmarks:
            return EmotionState.NEUTRAL, 0.0, False, 1.0
        
        face_landmarks = results.multi_face_landmarks[0]
        
        # 简化的表情识别（基于关键点几何特征）
        emotion, confidence = self._classify_emotion_from_landmarks(face_landmarks)
        
        # 计算人脸距离（基于人脸大小）
        landmarks_array = np.array([(lm.x, lm.y) for lm in face_landmarks.landmark])
        face_width = np.max(landmarks_array[:, 0]) - np.min(landmarks_array[:, 0])
        distance = 1.0 / max(0.1, face_width)  # 距离的相对值
        
        # 平滑处理
        self.emotion_history.append(emotion)
        if len(self.emotion_history) > self.max_history:
            self.emotion_history.pop(0)
        
        # 使用众数作为最终结果
        from collections import Counter
        emotion = Counter(self.emotion_history).most_common(1)[0][0]
        
        return emotion, confidence, True, distance
    
    def _classify_emotion_from_landmarks(
        self, 
        face_landmarks: Any,
    ) -> tuple[EmotionState, float]:
        """从面部关键点分类情绪（简化版本）。
        
        实际应用中可以使用更复杂的模型，如FER、DeepFace等。
        """
        # 提取关键点
        landmarks = face_landmarks.landmark
        
        # 简化的特征提取
        # 嘴角 (61, 291) vs 中心 (13)
        left_mouth = landmarks[61]
        right_mouth = landmarks[291]
        mouth_center = landmarks[13]
        
        # 眼睛 (159, 145) vs (386, 374)
        left_eye_top = landmarks[159]
        left_eye_bottom = landmarks[145]
        right_eye_top = landmarks[386]
        right_eye_bottom = landmarks[374]
        
        # 计算特征
        mouth_curve = (left_mouth.y + right_mouth.y) / 2 - mouth_center.y
        left_eye_openness = abs(left_eye_top.y - left_eye_bottom.y)
        right_eye_openness = abs(right_eye_top.y - right_eye_bottom.y)
        avg_eye_openness = (left_eye_openness + right_eye_openness) / 2
        
        # 简单的规则分类
        confidence = 0.6
        
        if mouth_curve < -0.01:  # 嘴角上扬
            return EmotionState.HAPPY, 0.7
        elif mouth_curve > 0.01:  # 嘴角下垂
            return EmotionState.SAD, 0.6
        elif avg_eye_openness > 0.03:  # 眼睛睁大
            return EmotionState.SURPRISED, 0.6
        elif avg_eye_openness < 0.015:  # 眼睛疲劳
            return EmotionState.TIRED, 0.65
        else:
            return EmotionState.NEUTRAL, 0.5
    
    def _analyze_posture(self, frame_rgb: np.ndarray) -> tuple[PostureState, float]:
        """分析身体姿态。"""
        if not self.pose:
            return PostureState.UNKNOWN, 0.0
        
        results = self.pose.process(frame_rgb)
        
        if not results.pose_landmarks:
            return PostureState.UNKNOWN, 0.0
        
        landmarks = results.pose_landmarks.landmark
        
        # 提取关键点
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # 计算姿态特征
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        hip_center_y = (left_hip.y + right_hip.y) / 2
        head_shoulder_dist = nose.y - shoulder_center_y
        torso_angle = shoulder_center_y - hip_center_y
        
        # 判断姿态
        posture = PostureState.UNKNOWN
        confidence = 0.0
        
        if head_shoulder_dist < -0.1:  # 头部相对肩膀前倾
            posture = PostureState.LEANING_FORWARD
            confidence = 0.7
        elif head_shoulder_dist > 0.05:  # 头部后仰
            posture = PostureState.LEANING_BACK
            confidence = 0.7
        elif abs(left_shoulder.y - right_shoulder.y) > 0.08:  # 肩膀倾斜
            posture = PostureState.TILTED
            confidence = 0.65
        elif torso_angle < 0.15:  # 驼背
            posture = PostureState.SLOUCHING
            confidence = 0.6
        else:
            posture = PostureState.UPRIGHT
            confidence = 0.6
        
        # 平滑处理
        self.posture_history.append(posture)
        if len(self.posture_history) > self.max_history:
            self.posture_history.pop(0)
        
        from collections import Counter
        posture = Counter(self.posture_history).most_common(1)[0][0]
        
        return posture, confidence
    
    def _calculate_engagement(
        self, 
        emotion: EmotionState, 
        posture: PostureState,
        face_detected: bool,
    ) -> float:
        """计算用户参与度。"""
        if not face_detected:
            return 0.0
        
        engagement = 0.5  # 基础值
        
        # 根据情绪调整
        if emotion in (EmotionState.HAPPY, EmotionState.SURPRISED, EmotionState.FOCUSED):
            engagement += 0.2
        elif emotion in (EmotionState.SAD, EmotionState.TIRED):
            engagement -= 0.2
        
        # 根据姿态调整
        if posture == PostureState.LEANING_FORWARD:
            engagement += 0.3  # 前倾表示专注
        elif posture == PostureState.UPRIGHT:
            engagement += 0.1
        elif posture in (PostureState.SLOUCHING, PostureState.LEANING_BACK):
            engagement -= 0.2
        
        return max(0.0, min(1.0, engagement))
    
    def _calculate_fatigue(
        self, 
        emotion: EmotionState, 
        posture: PostureState,
    ) -> float:
        """计算用户疲劳度。"""
        fatigue = 0.3  # 基础值
        
        # 根据情绪调整
        if emotion == EmotionState.TIRED:
            fatigue += 0.4
        elif emotion in (EmotionState.HAPPY, EmotionState.SURPRISED):
            fatigue -= 0.2
        
        # 根据姿态调整
        if posture == PostureState.SLOUCHING:
            fatigue += 0.3
        elif posture == PostureState.UPRIGHT:
            fatigue -= 0.1
        
        return max(0.0, min(1.0, fatigue))
    
    def get_state_description(self, state: UserState) -> str:
        """生成用户状态的文字描述。"""
        parts = []
        
        if not state.face_detected:
            return "未检测到用户"
        
        # 情绪描述
        emotion_map = {
            EmotionState.HAPPY: "愉快",
            EmotionState.SAD: "沮丧",
            EmotionState.ANGRY: "生气",
            EmotionState.SURPRISED: "惊讶",
            EmotionState.NEUTRAL: "平静",
            EmotionState.TIRED: "疲惫",
            EmotionState.FOCUSED: "专注",
        }
        parts.append(f"情绪: {emotion_map.get(state.emotion, '未知')}")
        
        # 姿态描述
        posture_map = {
            PostureState.UPRIGHT: "端正",
            PostureState.SLOUCHING: "懒散",
            PostureState.LEANING_FORWARD: "前倾（专注）",
            PostureState.LEANING_BACK: "后仰（放松）",
            PostureState.TILTED: "歪头",
        }
        parts.append(f"姿态: {posture_map.get(state.posture, '未知')}")
        
        # 参与度
        if state.engagement_level > 0.7:
            parts.append("参与度: 高")
        elif state.engagement_level < 0.3:
            parts.append("参与度: 低")
        
        # 疲劳度
        if state.fatigue_level > 0.7:
            parts.append("疲劳度: 高，建议休息")
        
        return "；".join(parts)
    
    def __del__(self):
        """析构函数，确保资源释放。"""
        self.stop_capture()

