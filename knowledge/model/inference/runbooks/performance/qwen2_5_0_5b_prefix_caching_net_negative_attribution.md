---
{
  "type": "Runbook",
  "title": "Qwen2.5-0.5B 短序列 prefix caching 的 Gather 收支与 MTE2 观测",
  "description": "来源两组短序列 profiling 中，Gather 与注意力额外耗时超过 FFN 节省，总算子时间约增加 4.1%/3.3%。MTE2 上升而 MAC 近似不变是数据搬运压力线索，尚不能确认 L2 污染因果或线性盈亏平衡点。",
  "tags": [
    "task.optimization",
    "topic.kv_cache"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# Qwen2.5-0.5B 短序列 prefix caching 的 Gather 收支与 MTE2 观测

## 适用场景

atb qwen2.5-0.5b（seq_len 150/218、batch 10）prefix vs no-prefix profiling 对比：prefix 引入 Gather 固定开销（+101,363us/150req）；FIA 变慢 +6.1%/+10.5% 的观测是 aic_mte2_time 37.7→42.1us（+11.7%）而 aic_mac_time 3.2us 不变（L2 污染只是待验证解释）；FFN 收益 -63,406us 仅为 Gather 开销的 63%，总 op 时间 +4.1%，361 token 只是未验证的线性外推估计。

适用于 atb/GE 推理框架中评估 prefix caching（KV cache 复用）在短序列小模型上的净收益，以及 profiling 数据驱动的算子级收支归因（Gather 开销 vs FFN 节省 vs 注意力污染）。

## 触发与观测

prefix 与 no-prefix 两份 msprof profiling（op_summary.db sqlite 三表 JOIN + task_time.csv + api_statistic）对比任务。

### 结论与证据边界

FusedInferAttentionScore 的观测表现为 MTE2 时间增加、MAC 时间近似不变，提示检查数据搬运：prefix_150 aic_mte2_time 37.7→42.1us（+11.7%，mte2_ratio 0.3592→0.3748）、prefix_218 34.0→41.2us（+21.2%），而 aic_mac_time 3.2/4.8us 完全不变、输入 shape 相同（Q/K/V 1500,14,64/1500,2,64）——Gather_expand 把 1320 行写回 1500 行 tensor 的额外 GM 写（每层每请求 +2.6MB）可能影响后续缓存与搬运，但没有缓存计数或独立消融证明 L2 污染；分布是系统性的（min/avg/max 同步上移，n=3600）。

### 结论与证据边界

净效应与判别：seq_len=150 场景 FFN 收益 -63,406us（token 1500→1320，Gate/Up proj -9.1%、Down -6.4%）仅为 Gather 开销 +101,363us 的 63%，注意力侧再亏 +28,200us（FIA +25,385），总计 +64,901us（+4.1%）；218 场景 FFN -86,299us 覆盖 Gather 99,039us 的 87%、注意力亏 +52,882us，总计 +65,376us（+3.3%）；累计差距除以 150 请求=433us/req 与端到端 Execute 差距 385us 吻合；若额外假设 Gather 成本固定且 FFN 节省随复用 token 线性变化，可得到 361/395 token 的外推估计；这些假设及更长 prefix 未验证，数字不是实测盈亏点。

## 探针与操作

1) sqlite：ge_summary JOIN task_time 按 op_type/task_type 聚合（n/total/avg/wait）；2) 按 input/output shape 把 MatMulV3 分类为 Q/KV/O/Gate_Up/Down/lm_head 角色、GatherV2 分类为 expand/compress/attn_out/final_token；3) ai_core_metrics 取 FIA 的 aic_mte2/mte2_ratio/aic_total/mac/scalar 及 min/avg/max 分布；4) 层内 task_id 顺序还原数据流。

## 机制与判别

见上方结论原文与下方机制片段；判别性证据与边界适用讨论见“适用与失效边界”节。

### 补充机制片段

```
=== FIA aic_mte2 detail ===
  no-prefix_150       : aic_mte2_time=37.7us  mte2_ratio=0.3592  aic_total=105.1  mac=3.2  scalar=52.9
  prefix_150          : aic_mte2_time=42.1us  mte2_ratio=0.3748  aic_total=112.5  mac=3.2  scalar=55.0
  no-prefix_218       : aic_mte2_time=34.0us  mte2_ratio=0.3132  aic_total=108.5  mac=4.8  scalar=52.4
  prefix_218          : aic_mte2_time=41.2us  mte2_ratio=0.3435  aic_total=120.0  mac=4.8  scalar=57.8
```

### 补充机制片段

```
  FFN收益:        -63,406 us  (token 1500→1320, -12%)
  Gather开销:    +101,363 us  (每层2个Gather×24层, 固定成本)
  注意力侧变化:   +28,200 us  (FIA L2 cache驱逐 +25385, Q/K/V微增 +2631)
  其他变化:        -1,256 us  (Embedding/Sub等小幅节省)
  ────────────────────────
  净变化:         +64,901 us  (+4.1%)
```

## 验证信号

全部数字来自 sqlite 查询输出：FIA mte2 37.7→42.1us 而 mac 3.2us 不变；FFN/Gather/注意力收支数字见机制片段：2。

## 适用与失效边界

适用：qwen2.5-0.5b（24 层、1500/1320 token、batch 10、Atlas 推理卡）。核心判别：361/395 token 只是固定成本与线性节省假设下的估计，不是已验证阈值。局限：未验证更长 prefix 或 batch 变化下的外推；Gather 优化建议（合并小 Gather、减少 host-device 传输）未实施。
