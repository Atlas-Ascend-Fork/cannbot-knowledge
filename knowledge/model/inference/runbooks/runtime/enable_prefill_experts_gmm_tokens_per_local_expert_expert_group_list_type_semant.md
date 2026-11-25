---
{
  "type": "Runbook",
  "title": "hy3_preview prefill MoE EP 专家计算 F.linear 循环 → GMM（npu_grouped_matmul）替换：功能闭合与贪心统计等价验证",
  "description": "模型/任务：hy3_preview（295B MoE，192 experts top-8 + 1 shared）SOTA decode 场景，1k input / batch16 / bf16 / ge_graph / Atlas A3 16 die（attn_tp4 + moe_ep16）。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# hy3_preview prefill MoE EP 专家计算 F.linear 循环 → GMM（npu_grouped_matmul）替换：功能闭合与贪心统计等价验证

## 适用场景

- 平台范围依据：source 0 seq 96的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/任务：hy3_preview（295B MoE，192 experts top-8 + 1 shared）SOTA decode 场景，1k input / batch16 / bf16 / ge_graph / Atlas A3 16 die（attn_tp4 + moe_ep16）。
- 症状背景：round0 profiling 显示 prefill `MatMulV3 ×1336 = 603ms` 占 prefill Cube 主体，根因为 `HYV3Experts.forward_ordered` 对 EP re-routing 后的 ordered tokens 用 Python 逐专家两次 F.linear 计算。
- 改动位置：`modeling_hy_v3.py` `HYV3MoE._moe_ep_manual`（prefill EP 路径；decode `_moe_ep_mc2_decode` 不动，ge_graph 编译缓存不受影响）。

## 触发与观测

- 实施（source 0 seq 45）：按 `enable_prefill_experts_gmm` 开关（默认开）分支调用 `self.experts.forward_gmm(hidden_states_ordered, tokens_per_local_expert, group_list_type=1)`，False 回退原 `forward_ordered` 循环。
- 语义核对：`npu_moe_re_routing` 输出 `tokens_per_local_expert` 为 per-local-expert COUNT，与 decode MC2 路径 `expert_token_num` 同语义（group_list_type=1）；qwen3_moe 参考实现 re_routing→GroupedMatMul 衔接同构。
- 功能验证（均 tool_observed，source 0）：16 rank 无 crash；prefill warmup 成功（GMM 路径实际执行）后进入 GE decode 编译；3 次完整运行输出连贯、无乱码/早停。

## 探针与操作

1. 单一 tracked 代码改动（git diff --stat：modeling_hy_v3.py +20/-3）；`loopfb` 回退 YAML（`enable_prefill_experts_gmm: False`）+ 独立 launcher 做对照运行。
2. 同机同会话三连跑：GMM run1 / GMM run2 / LOOP 回退，共享暖 decode 编译缓存。
3. 逐 Request 全文提取 + 首行答案对照 + 全 body 首分叉点计算（Python 脚本，非目测）。

## 机制与判别

- 机制：GMM（npu_grouped_matmul ×2 + swiglu）与逐专家 F.linear 数学等价、kernel 融合度不同；预期 prefill 专家计算从 1336 次小 MatMul 收敛到 ~2 GMM/层。
- 性能本次观测（同 workload：1k/b16/bf16/ge_graph/16die；metric `Inference time (prefill)` ms）：
  - LOOP 回退（seq 139）：2540.14 ms；
  - GMM run2（seq 147）：2193.44 ms；GMM run1（seq 109，digest 完整日志行）：2267.39 ms；
  - ≈11-14% prefill 时延下降（单样本，未做统计重复）；decode 平均 31.77 → 31.53/35.94 ms 在运行噪声内（符合 prefill-only 改动预期）。
- 精度判别：GMM-vs-loop 输出分叉（首分叉点 63-168 字符）落在同配置 GMM 重跑噪声带（9-214 字符）内 → 分叉不可归因于算子替换（详见 本卡草稿）。
- MatMulV3 1336→0 的算子计数验收未采集（TR3 profiling 职责），精确收益待 profiling 复核。

## 验证信号

- 实施+语法（source 0 seq 45，tool_observed，逐字工件见「探针与操作」小节）；三组运行指标 seq 107/139/147（tool_observed）；分叉对照 seq 142/150（tool_observed）。
- 功能完成度：16 rank、warmup 过、3 运行输出连贯、git diff 范围受控。

## 适用与失效边界

- 适用：同框架（executor 统一流程）MoE EP prefill 路径、已具备 decode forward_gMM 实现的模型（qwen3_moe/deepseek_r1 同构路径）。
- 失效/不覆盖：性能数字为单次观测非统计基准；算子计数收益未直接采集；非 EP（moe_ep=1）路径不走 `_moe_ep_manual` 不适用；贪心逐 token 严格对齐在该 EP 路径上不可达（受固有非确定性约束，须统计等价判定）。

## 附：断言存档

- hy3_preview prefill MoE EP 路径把 _moe_ep_manual 内 re-routing 后的专家计算由 forward_ordered（Python 逐专家两次 F.linear 循环，round0 实测 MatMulV3×1336=603ms）替换为 decode 现成 forward_gmm（npu_grouped_matmul，tokens_per_local_expert 以 group_list_type=1 语义直接喂 GMM，与 qwen3_moe 参考实现同构），加 enable_prefill_experts_gmm 开关（默认开，False 回退循环）。
- 功能验证闭合：16 rank 无 crash、prefill warmup 成功（GMM 路径执行）、3 次运行输出全部连贯；本次观测同 workload 下 prefill 时延 loop 2540.14ms → GMM 2193.44ms（run2）/2267.39ms（run1，digest 完整日志行），decode 平均 31.77 → 31.53/35.94ms（prefill-only 改动，decode 在运行间噪声内）。

```text
        if self.enable_prefill_experts_gmm:
            # tokens_per_local_expert is per-LOCAL-expert COUNT (group_list_type=1),
            # same semantics as the decode MC2 path's expert_token_num.  forward_gmm
            # collapses the 1336 per-expert F.linear calls into ~2 GroupedMatMul/layer.
            hidden_states_ordered = self.experts.forward_gmm(
                hidden_states_ordered, tokens_per_local_expert, group_list_type=1
            )
        else:
            hidden_states_ordered = self.experts.forward_ordered(
                hidden_states_ordered, tokens_per_local_expert
            )
```

```text
393:[INFO][2026-06-25 18:56:31.914][scheduler.py:482] [Main] Inference time (prefill): 2540.14 ms
```

```text
390:[INFO][2026-06-25 18:58:20.119][scheduler.py:482] [Main] Inference time (prefill): 2193.44 ms
```
