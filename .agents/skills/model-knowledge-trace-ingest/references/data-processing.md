# 通用 Agent 轨迹归一化

所有来源先归一化，再进入批量挖掘。适用对象是 Agent 运行留下的消息、工具事件、观测与产物，输入可以来自 Codex、Claude Code、OpenCode 或其他 Agent；知识范围仍限定为模型及框架相关场景。

## 输入与转换

```bash
python3 <SKILL_DIR>/scripts/normalize_trace.py <本地导出文件或目录> --output <build>/normalized
python3 <SKILL_DIR>/scripts/normalize_trace.py <build>/normalized --verify
```

自动入口接受 JSON、JSONL/NDJSON、消息数组、messages/events 包装、message/payload 封装和内容块。按记录结构识别角色、调用和返回；不要求来源具有特定会话名、存储目录或远端服务。`--format json|jsonl|text` 可明确文件编码形式。文本和 Markdown 转写缺少机器可确认的结构时整段保留为 unknown，不把标题或 Agent 的文字判断当工具结果。

已覆盖的常见结构包括角色消息、文本块、工具调用/返回块、消息 parts 与工具 state。结构版本发生变化时，未识别部分原样保留为 unknown；自动识别常见结构不等于支持所有客户端所有版本。不得用占位字符串替换未知内容。无效或截断 JSON 保留可读取记录及不完整原文，不补造闭合数据、缺失返回或成功结果。

目录须由调用方给出同一来源的文件边界；文件按相对路径稳定排序、记录保持源序，不能将文件序解释为跨会话的全局时间顺序。只保留显式 session/parent 字段；缺失会话身份以文件局部标识表示，缺失父子关系保持未知。默认 events 模式保留相同文本的每次出现；累积快照按下面的显式布局处理，不能全局按文本去重。

非 UTF-8、二进制、未支持的文件成员和符号链接拒绝处理并报告；不要把忽略成员后的结果当完整来源。已有归一化目录不可覆盖，输出也不得放在原始来源或知识正文中。

## 其他结构：声明式映射

字段映射使用 JSON 的点分路径，从每条记录取值，不执行代码。`event_type` 与 `text` 为必填映射；未知事件类型保留整条原文。映射保存到 manifest 以便复核。例如：

```json
{
  "fields": {
    "event_type": "event.kind",
    "actor": "event.who",
    "text": "event.body",
    "session_id": "run",
    "call_id": "event.call"
  },
  "event_types": {"invoke": "tool_call", "return": "tool_result"}
}
```

```bash
python3 <SKILL_DIR>/scripts/normalize_trace.py <导出.jsonl> --mapping <映射.json> --output <build>/normalized
```

还可映射 `parent_session_id`、`timestamp`、`tool_name`；工具结果可用 `exit_code`、`truncated`、`status`、`metadata` 或 `outcome` 接入嵌套的执行元数据。映射应依据导出格式定义，不能根据正文包含某个词就标为客观观测。复杂导出可先由调用方依据实际格式转换为下面的事件记录，保留原始文件与转换说明；没有足够结构时只交付待判定记录。

## 累积消息快照

若每条记录重传整段消息历史，使用 `--layout snapshots`；不要另写按消息文本去重的转换器。默认读取 `messages`，可用声明式映射指定路径（数字路径段可索引数组）：

```json
{
  "layout": "snapshots",
  "messages_path": "capture.messages",
  "response_path": "reply",
  "session_id": "run.id",
  "parent_session_id": "run.parent"
}
```

```bash
python3 <SKILL_DIR>/scripts/normalize_trace.py <导出.jsonl> --layout snapshots --mapping <映射.json> --output <build>/normalized
```

同一显式会话只消除位置、内容均相同的继承前缀，新增的相同消息仍是新回合。已解析为消息对象的 response 可纳入前缀，避免下一个快照重放；无法解码的字符串、SSE 或其他响应保留 unknown 并记录警告。历史变短或发生分叉时保留整条异常记录为 unknown，不猜测分支时序。缺少会话身份时仅在文件内追踪前缀；跨文件先后须由调用方确认。manifest 记录布局、映射和局限，保留源文件 hash；不执行来源内容。

## 统一事件与来源合同

`normalized_trace.jsonl` 每行一个 `trace.event.v1`：

| 字段 | 语义 |
|---|---|
| sequence | 整个规范化来源内从 1 连续递增的事件位置 |
| session_id / parent_session_id | 来源明确给出的会话与父会话；缺失关系为 null |
| timestamp | 来源时间，缺失为 null；不推断跨文件时序 |
| actor | user、assistant、system、developer、tool 或来源声明的其他角色 |
| event_type | user_message、assistant_message、system_message、tool_call、tool_result、reasoning、error、metric、artifact、session_start、session_end、unknown |
| tool | 可为空，否则含 name 与 call_id；不补造未知调用身份 |
| outcome / result_metadata / limitations | 保留退出码、输出完整性、原始结果状态与元数据；元数据同样脱敏。completed 只是生命周期，非零退出码为 error；截断记 limitation；未识别或矛盾状态保留 unknown |
| message_id / parent_message_id | 显式消息关系；普通消息 info.parentID 不映射为父会话。父会话仅来自明确 session 字段、session 对象/会话声明或声明式映射 |
| content.text | 脱敏后的完整正文，JSON 参数保持可解析；无文本上限裁剪 |
| provenance | 原始相对文件名、逻辑记录号、记录内容 hash、文件字节 hash、内部 locator 与适配版本 |

`session_manifest.json` 使用 `agent.trace-session.v1`，包含原始文件相对路径与 SHA-256 清单、聚合来源 hash、规范化正文 hash、会话表、事件类型计数、脱敏计数、警告及输入局限。记录 hash 基于解析后记录的规范序列化，文件 hash 绑定原始字节，两者不可互换。verify 核对本地产物一致性，不证明远端文件齐全或轨迹未在采集端截断。

孤立 Unicode 代理码元以可见转义保留；原始记录身份与文件 hash 仍区分异常码元和原文中的字面转义。正文、工具参数和事件元数据统一脱敏，原始文件不修改。自动脱敏不是敏感信息审查的替代品；公开卡片仍要去除私有账号、路径和连接信息。

## 阅读与缺口

批量使用 [batch-processing.md](batch-processing.md) 的 prepare 和连续阅读视图。精确补读长事件可执行：

```bash
python3 <SKILL_DIR>/scripts/read_trace.py index <normalized-dir> --start 1 --count 100
python3 <SKILL_DIR>/scripts/read_trace.py batch <normalized-dir> --sequence 1 --offset 0 --characters 6000
python3 <SKILL_DIR>/scripts/read_trace.py read <normalized-dir> --sequence 12 --offset 0 --characters 6000
```

text_parts 按顺序连接得到原始字符区间，按 next_sequence/next_offset 续读。分页完整、索引完整与真实语义阅读分别记账。unknown、未解码媒体、源端截断、缺失子会话和未读正文进入重建 limitations；相关证据不足时暂缓结论，不凭记忆补齐。

脱敏配置、元数据审计及发布前检查见[脱敏流程](privacy.md)。事件正文身份 hash 基于脱敏后的实际正文；原始文件/记录 hash 仍绑定私有原始材料。旧快照不能补标新脱敏版本，须由原始输入生成新目录。
