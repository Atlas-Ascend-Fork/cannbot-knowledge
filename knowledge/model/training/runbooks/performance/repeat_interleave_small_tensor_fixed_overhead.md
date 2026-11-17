---
{
  "type": "Runbook",
  "title": "小张量 RepeatInterleave 回退：分开训练内观测与隔离微基准",
  "description": "记录 metadata tensorize 路径中的 RepeatInterleave 观测；隔离 CPU/NPU/searchsorted 数字只解释各自用例，没有可信基线统计时不作调用次数增幅比较。",
  "tags": [
    "task.debugging",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# 小张量 RepeatInterleave 回退：分开训练内观测与隔离微基准

## 适用场景

torchtitan-npu CP metadata：训练内 kernel 输入含 167/175 个元素；隔离微基准另用 shape=(4,) 的 counts，值为 1..5，两者不是同一输入。

## 触发与观测

修改版训练 profiling 报告 RepeatInterleave 200 次；没有绑定真实基线计数，不采用 16→200 的增幅。隔离微基准没有复现训练内约 9ms 的长尾。

## 探针与操作

逐项对照 op_statistic 与 kernel_details 的次数、shape 和执行核心；再将纯算子、数据移动及逐次 .item() 同步分开计量。

分开列示训练与隔离微基准；不把含 D2H 的路径标为纯 CPU：

```text
training kernel input: 167/175 elements
training RepeatInterleave: 200 calls; sum=438.7 ms; p50=0.129 ms; max=9.10 ms
isolated counts: shape=(4,), values in [1,5], original tensor on NPU
NPU: 0.071 ms
CPU path including counts.cpu() each call: 1.927 ms
CPU path including transfers back: 1.928 ms
searchsorted path: 0.049 ms
25-call segment: 1.72 ms; segment with extra item(): 4.46 ms
host-only CPU latency: not measured by these paths
```

## 机制与判别

本次仅记录修改版的小算子次数，没有真实基线计数时不能裁定增幅。隔离微基准的 CPU/NPU 结果不能解释所有训练内长尾，也不能据一个 searchsorted 用例就宣称其普遍最优。

## 验证信号

训练输出报告 200 次 AI_VECTOR_CORE RepeatInterleave、合计 438.7ms、p50 0.129ms、最大 9.10ms。另一个四元素微基准为 NPU 0.071ms、含每轮 counts.cpu() 的 CPU 计算路径 1.927ms、含回传的路径 1.928ms、searchsorted 0.049ms；前两条 CPU 路径都含 D2H，不是 host-only 测量。连续 25 次与附加 .item() 的两个段观测分别为 1.72ms 与 4.46ms。

## 适用与失效边界

这些是各自口径的观测，不构成已落地的模型加速方案。同步、warmup、重复次数和输入形状须与待迁移场景匹配；训练内长尾的原因在记录中尚未裁定。
