---
{
  "type": "Runbook",
  "title": "小专家数 MoE 基准：先核对实际 rank 负载与 gating 覆盖",
  "description": "均衡 fixture 的目标分布不能替代实际 routed counts；阶段时长偏斜和分块覆盖只作诊断线索，不能据此裁定实际路由或性能收益。",
  "tags": [
    "task.debugging",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# 小专家数 MoE 基准：先核对实际 rank 负载与 gating 覆盖

## 适用场景

mega_moe 的小专家数基准；记录讨论每卡 3 专家档、总专家数 24 和 GATE_TILE_N=128。具体设备未知。

## 触发与观测

同一 balanced 样本的跨 rank stage-timing 存在阶段时长偏斜；这些时长不是实际路由行数。hotspot fixture 属于另一工作负载，不能混入对照。

## 探针与操作

并列核对 intended 分布、实际每 rank routed counts 和阶段 trace。若循环使用 floor(total_experts/tile_n)，计算覆盖数并检查尾块是否另有处理。

静态分块算式；需另查真实循环及尾块路径：

```python
total_experts = 24
tile_n = 128
n_tiles = total_experts // tile_n
assert n_tiles == 0
```

## 机制与判别

总专家数 24 按 128 宽度做整数除法得到 0；只有确认当前执行路径确实用该值控制循环且没有尾块路径，才能推出 gating 未覆盖输入。阶段时长偏斜不能证明实际路由集中，更不足以证明 logits 必然为零或 topk 必选前六个专家。

## 验证信号

原始 balanced 目标计数计算与同一 balanced 采样的跨 rank 阶段记录分别给出目标和时序观测；后者存在偏斜，但尚无实际 routed counts 对照。热点目标打印属于另一 fixture，不与本样本合并；不采纳精确 clamp 数值、全部 token 路由或根因裁决。

## 适用与失效边界

在补齐真实路由计数、gating 输出及循环覆盖前，不将该档结果外推为均衡负载收益；其他专家数档也需各自验证，不能因本档异常就宣称它们健康。
