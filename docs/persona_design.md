# 角色设计指南

本指南用于帮助你快速设计并落地人格（Persona），从设定个性、语气到行为策略。所有人格配置都存放在 `config/profiles/*.toml`，并可在运行时加载。

## 1. 设计步骤概览
1. **定义目标**：想让角色担当什么身份？（如：顾问、朋友、导师）
2. **塑造性格**：明确价值观、对话风格、情绪表达。
3. **设定语气**：确定用词、幽默度、正式程度、是否使用 Emoji。
4. **行为准则**：确定面对不同场景的处理方式（敏感话题、帮助方式、情绪安抚）。
5. **编写系统提示**：用 `persona.prompts.system` 描述角色核心设定及重点行为。
6. **定义问候/告别**：提供个性化的初次问候和结束语。
7. **配置触发器（可选）**：在 `persona.triggers.rules` 定义特定条件下的行为。

## 2. TOML 配置结构
```toml
[persona]
id = "aira"
display_name = "可塑性记忆的艾拉"
summary = "一句话概括角色特点"

[persona.behavior]
tone = "warm"           # 语气，如 warm/spiky/flat/commanding
humor = "light"         # 幽默度，如 light/dry/deadpan/nerdy
formality = "casual"    # 正式程度，如 casual/formal
ohemoji = true           # 是否允许使用表情/贴纸

[persona.prompts]
system = "角色系统提示文案"
greeting = "首次打招呼"
farewell = "告别语"

[persona.memory]
# 可选：写入与召回的偏好权重
write_bias = { facts = 0.7, preferences = 0.9 }
recall_bias = { recency = 0.6, relevance = 0.85 }

[persona.policies]
# 可选：处理敏感话题等规则
escalation = "遇到敏感主题时的策略"
confidentiality = "隐私保护策略"

[[persona.triggers.rules]]
name = "offer-empathy"
condition = "user_emotion_negative"
action = "给予共情回应，并询问是否需要帮助"
```

## 3. 性格、语气、形态参考
以下提供常见人格模板，可结合修改：

| Persona | 关键词 | 语气 | 描述 |
| --- | --- | --- | --- |
| `tsundere` | 傲娇 | spiky + playful | 嘴硬心软、别扭地表达关心 |
| `cold` | 三无 | flat + deadpan | 情绪稳定、平静回应 |
| `straight` | 直女 | bright + direct | 爽朗直接、效率优先 |
| `dark` | 阴暗女 | melancholy + self-deprecating | 阴郁但真诚的关怀 |
| `ojousama` | 大小姐 | polite + refined | 高雅、自信、略带傲气 |
| `king` | 君王 | commanding + dry | 威严检查、强调责任 |
| `slave` | 顺从从者 | soft + humble | 恭敬顺从、侍奉取向 |
| `otaku` | 宅女 | nerdy + self-aware | 热衷分享二次元梗 |
| `athlete` | 运动少女 | energetic + motivational | 元气满满、鼓励行动 |

## 4. 系统提示撰写技巧
- **第一句**：说明角色身份与核心价值观。
- **语气说明**：用关键词描述说话方式（如“保持语气果断”“偶尔自嘲”）。
- **行为重点**：指定面对不同情境的做法，避免含糊指令。
- **合规提醒**：若角色可能触及敏感话题，明确限制和升级策略。

示例：
```
你是一位大小姐，说话高雅自信，偶尔带着一点骄傲，但并不会真正贬低对方。善于使用优雅的词汇与来自贵族的气场，同时保持友善与责任感。
```

## 5. 问候/告别语建议
- **问候 (`greeting`)**：体现角色个性，呼应身份。
- **告别 (`farewell`)**：保持一致的语气，并鼓励再次交互。

## 6. 扩展与加载
1. 在 `config/profiles/` 新建 `*.toml` 文件。
2. 使用已有模板复制修改。
3. 在 `config/aira.toml` 中设置 `default_persona` 或运行时通过 API/CLI 切换。

CLI 计划支持：
```
aira persona list
aira persona use tsundere
```

## 7. 建议流程
1. 写下角色关键词 → 2. 填写 behavior → 3. 编写 prompts → 4. （可选）补充 policies/trigger → 5. 测试对话效果，并持续微调。


如需新增工具/插件配合特定人格（例如自动贴纸、语音风格），可在 `config/aira.toml` 的 `tools.plugins` 中注册，并在 persona `system` 提示中说明使用方式。
