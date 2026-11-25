---
{
  "type": "Runbook",
  "title": "MindSpeed-MM 多进程数据分片 Arrow schema 冲突：异构角色消息致 `_response` 类型推断不一致，合并时对齐失败",
  "description": "框架/任务：MindSpeed-MM agentic LoRA SFT，`preprocessing_num_workers: 4`，HF `datasets` 多分片 map + 合并路径。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# MindSpeed-MM 多进程数据分片 Arrow schema 冲突：异构角色消息致 `_response` 类型推断不一致，合并时对齐失败

## 适用场景

- 框架/任务：MindSpeed-MM agentic LoRA SFT，`preprocessing_num_workers: 4`，HF `datasets` 多分片 map + 合并路径。
- 触发：16 卡训练启动时 rank14/rank2 在 `Trainer.__init__` → `align_dataset()` → `_concatenate_map_style_datasets` 抛错。

## 触发与观测

- 原始报错（source 0 seq 2596 逐字）：`ValueError: The features can't be aligned because the key _response of features {'_prompt': List(Json(decode=True)), '_response': List(Json(decode=True)), ...} has unexpected type - List(Json(decode=True)) (expected either List({'role': Value('string'), 'content': Value('string')}) or Value("null").`
- 报错 rank 均在 dataloader 构建（`build_mm_dataset` → `align_dataset`）阶段，未进入训练。

## 探针与操作

1. 根因（source 0 seq 2649、2873）：assistant 消息多 `reasoning_content` 与 `loss` 字段，工具返回只有 `role/content`；`datasets` 在各分片内独立推断字段类型——某分片 `_response` 全是工具返回则推断为 `role/content` 结构，另一分片混有 assistant 则推断为 `Json`；合并分片时两种类型不兼容。
2. 修复（source 0 seq 2873，convert.py `align_dataset()` 新增 18 行）：固定每条消息结构——

```text
role:              string
content:           string
reasoning_content: string 或 null
loss:              bool 或 null
```

   缺失字段在 Arrow 存储时补 `null`；工具、媒体等列表列也固定类型，避免分片自行推断。
3. 漏测原因与补测（source 0 seq 2873）：此前全量标签校验没走实际的多进程 `align_dataset()`；这次补上 4 个 spawn 进程处理全部 221 条数据并逐 token 核对标签。

## 机制与判别

- 机制：HF `datasets.map` 的分片并行 + 特征独立推断 → 异构消息结构（agentic 数据特有）触发 schema 分裂；单进程路径不会复现（source 0 seq 2649、2873）。
- 判别：修复只改中间存储类型，监督逻辑不变（真实 thinking/正文/tool call 参与 loss，工具返回与 `loss:false` 屏蔽）（source 0 seq 2873）。

## 验证信号

- tool_observed：4 spawn 进程处理全部 221 条数据 + 逐 token 标签核对通过（source 0 seq 2873）。
- tool_observed：81 项回归测试通过（source 0 seq 2873）。
- tool_observed：全量 42,076,340 token 输入与 loss 标签与独立参考一致、监督 token 数不变（source 0 seq 2826，同轨迹）。

## 适用与失效边界

- 适用：任何在 HF `datasets` 多进程预处理中产出异构消息结构（agentic/多角色对话、含可选字段）的训练数据管线——固定 Arrow 字段类型是通用防御。
- 失效/限制：字段结构清单绑定本数据 schema（role/content/reasoning_content/loss）；新增可选字段需同步固定类型声明；该修复不覆盖单进程路径的其它问题。

## 附：断言存档

- MindSpeed-MM 多进程预处理分片 Arrow schema 冲突：assistant 带 reasoning_content/loss 字段而 tool 返回只有 role/content，分片独立推断类型合并时报 _response features can't be aligned；convert.py align_dataset() 固定字段类型(string/string/string|null/bool|null)后 4 进程 221 条逐 token 核对+81 项测试通过
