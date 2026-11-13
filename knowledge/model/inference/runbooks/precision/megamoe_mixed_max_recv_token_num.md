---
{
  "type": "Runbook",
  "title": "A3 MegaMoE 在 P/PD-mixed 节点 max_recv_token_num 取配置值仅告警（接收容量配置风险（静态审查））",
  "description": "vllm-ascend DeepSeek-V4.1 的 moe_comm_method.py 中，decode-only 节点 max_recv_token_num 用绝对安全上界（num_max_tokens_per_rank × ep_world_size × min(topk, expert_per_rank)），而 P/PD-mixed 节点直接取 get_ascend_config().mega_moe_max_tokens 配置值并仅 logger.warning_once。专家负载倾斜时本 rank 实际接收 token 可超配置值，若实际接收量超过容量，存在精度劣化风险；具体溢出行为本轨迹未实测；PD-mixed 生产（同时做长 prefill）是最易触发场景。这是 bca6b8ff8 修复只覆盖 kv_transfer_config is None 分支后残留的风险敞口。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# A3 MegaMoE 在 P/PD-mixed 节点 max_recv_token_num 取配置值仅告警（接收容量配置风险（静态审查））

## 适用场景

- 模型/框架：DeepSeek V4.1 适配（MegaMoE 融合算子 + MC2 通信），vllm-ascend 硬件插件，分支 releases/v0.27.1rc，审查区间 `git log 09220f435~1..HEAD`。
- 平台：Ascend NPU（A3 MegaMoE 路径）；生产为 PD 分离（MooncakeHybridConnector）、enable_fused_mc2=1、expert parallel、dspark、fp8。
- 工作负载：PD-mixed 生产（同时做长 prefill 与 decode）+ 专家负载倾斜；用户背景为"精度波动 + 长稳退化"。
- 缺失信息：生产 additional_config 中 mega_moe_max_tokens 的实际取值与各 rank 实际接收 token 的分布统计未在轨迹内提供。

## 触发与观测

触发 = A3 MegaMoE 部署于 P/PD-mixed 节点 + 专家负载倾斜使本 rank 实际接收 token 超过 `mega_moe_max_tokens` 配置值。

审查观测到的客观代码事实（事件 28，moe_comm_method.py 读取，404-444 行，逐字）：

```
415:         num_topk = self.moe_config.experts_per_token
416:         num_experts = self.moe_config.num_experts
417:         expert_per_rank = max(1, num_experts // int(self.token_dispatcher.ep_world_size))
418:         absolute_safe_max_recv_token_num = max(
419:             1,
420:             num_max_tokens_per_rank * int(self.token_dispatcher.ep_world_size) * min(num_topk, expert_per_rank),
421:         )
422:
423:         if is_decode_only_node:
424:             max_recv_token_num = absolute_safe_max_recv_token_num
425:         else:
426:             # P nodes and PD-mixed nodes use the configured value. This keeps
427:             # the existing memory/performance tradeoff for prefill workloads.
428:             max_recv_token_num = get_ascend_config().mega_moe_max_tokens
429:             logger.warning_once(
430:                 "MegaMoe symm buffer: max_recv_token_num is set from "
431:                 "mega_moe_max_tokens=%d (reference value) on a P or PD-mixed "
432:                 "node. If the actual per-rank received token count after "
433:                 "dispatch exceeds this value, precision degradation will "
434:                 "occur. The absolute safe upper bound is %d "
435:                 "(num_max_tokens_per_rank=%d, ep_world_size=%d, num_topk=%d, "
436:                 "expert_per_rank=%d). Please tune mega_moe_max_tokens in "
437:                 "additional_config based on actual expert load distribution.",
438:                 max_recv_token_num,
439:                 absolute_safe_max_recv_token_num,
440:                 num_max_tokens_per_rank,
441:                 int(self.token_dispatcher.ep_world_size),
442:                 num_topk,
443:                 expert_per_rank,
444:             )
```

## 探针与操作

核查命令（审查会话实际执行，事件 350）：

```
grep -n "max_recv_token_num = get_ascend_config().mega_moe_max_tokens" vllm_ascend/ops/fused_moe/moe_comm_method.py
```

以及读取 `vllm_ascend/ops/fused_moe/moe_comm_method.py` 第 388-463 行（MegaMoE symm buffer 分配段）。本条为只读审查发现，未实施修复；"运行时用 ep_recv_counts 做上限校验并报错（或自动按安全上界分配），取代一次性告警"的修复建议未经验证，不能当作已验证修法采用。

## 机制与判别

结论 1：decode-only 节点 max_recv_token_num 用 absolute_safe_max_recv_token_num（num_max_tokens_per_rank × ep_world_size × min(num_topk, expert_per_rank)），P/PD-mixed 节点直接取 get_ascend_config().mega_moe_max_tokens 并仅 logger.warning_once。
- 证据：事件 28 逐字代码（415-444 行）；日志文案自身即承认"precision degradation will occur"。

结论 2：专家负载倾斜时本 rank 实际接收 token 可超配置值，若实际接收量超过容量，存在精度劣化风险；具体溢出行为本轨迹未实测；这是 bca6b8ff8 "Fix A5 MegaMoE buffer sizing for PD-mixed mode" 只修 kv_transfer_config is None 分支后残留的风险敞口（代码级推断）。
- 可区分解释分支：
  - PD-mixed 节点出现与专家负载分布相关的精度劣化、decode-only 节点正常 → 指向本条（配置值 vs 安全上界的差异）。
  - 劣化与节点角色无关、随时间加剧 → 指向 sleep/wake HCCL 或慢性泄漏类根因。
- 未验证推断：MegaMoE 算子溢出后的具体行为（静默截断/错写）未在轨迹内实测；"仅一条 warning_once"意味着生产日志中该告警易被忽略。

## 验证信号

- 信号等级：代码事实（read/grep 工具结果），非运行验证。
- 本轨迹内观测到的客观信号：事件 28（moe_comm_method.py 415-444 行完整原文，含 warning_once 全文与安全上界公式）、事件 352（grep 确认 428 行行号）。
- 平台：Ascend NPU（A3 MegaMoE 路径；生产 enable_fused_mc2=1）。
- 无性能/精度数值结论（只读审查，未运行专家倾斜负载验证）。

## 适用与失效边界

- 适用：A3 MegaMoE + P/PD-mixed 节点（同时承担长 prefill）；专家负载倾斜（热点专家集中在少数 rank）时最易触发。
- 不适用：decode-only 节点（使用绝对安全上界）；A5 路径（A5 MegaMoE 走 mega_moe.py 的独立 buffer 逻辑，bca6b8ff8 已修 PD-mixed sizing）。
- 版本边界：bca6b8ff8（"Fix A5 MegaMoE buffer sizing for PD-mixed mode"）之后本敞口仍存在于 A3 的 moe_comm_method.py 路径。
- 停止/回退条件：若 additional_config 中 mega_moe_max_tokens 已按实际专家负载调大到安全上界以上，则本条不触发；排查时应先取该配置值与 absolute_safe_max_recv_token_num 对比（日志 431-437 行会打印两者）。
- 修复方向（未验证）：运行时用 `ep_recv_counts` 做上限校验并报错（或自动按安全上界分配），取代一次性告警。
