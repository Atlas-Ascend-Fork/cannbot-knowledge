---
{
  "type": "Runbook",
  "title": "Qwen3-8B OS 调优对照：排除失败基线后未观察到 Decode 改善",
  "description": "来源一份基线推理 RC=1，脚本仍提取到旧结果数字，不能用于 A/B。有效基线为 Prefill/Decode 35.75/15.51ms，v2 为 37.08/15.53ms；样本不足以区分 Prefill 的真实退化与波动。",
  "tags": [
    "task.optimization",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# Qwen3-8B OS 调优对照：排除失败基线后未观察到 Decode 改善

## 适用场景

来源 Atlas A3、单卡 Qwen3-8B BF16、1tp、ge_graph、input_truncated_len=4096、batch=1、max_new_tokens=256 的 OS 参数实验。K8s 云环境为 aarch64 40 核、glibc 2.31。

## 触发与观测

| 运行 | 推理状态 | Prefill ms | Decode ms | 能否比较 |
|---|---|---:|---:|---|
| 最初基线 | RC=1 | 34.81 | 15.53 | 否，脚本仍提取结果但推理失败 |
| 后续有效基线 | 成功 | 35.75 | 15.51 | 来源中可用的基线 |
| v2 参数 | 成功 | 37.08 | 15.53 | 有限样本对照 |

README 或脚本内置基线不混入上述实测比较。

## 探针与操作

先检查推理退出码与本次产物时间，再解析结果。v2 联合调整 khugepaged scan/alloc_sleep 为 1000ms、THP defrag=always、dirty_ratio=5、dirty_background_ratio=3、sched_migration_cost_ns=500000；来源同时变动多项参数，不能单项归因。

## 机制与判别

```
# Re-apply v2 optimizations
echo "=== Re-applying v2 optimizations ==="
echo 1000 | sudo tee /sys/kernel/mm/transparent_hugepage/khugepaged/scan_sleep_millisecs > /dev/null 2>&1
echo 1000 | sudo tee /sys/kernel/mm/transparent_hugepage/khugepaged/alloc_sleep_millisecs > /dev/null 2>&1
echo always | sudo tee /sys/kernel/mm/transparent_hugepage/defrag > /dev/null 2>&1
sudo sysctl -w vm.dirty_ratio=5 2>/dev/null
sudo sysctl -w vm.dirty_background_ratio=3 2>/dev/null
sudo sysctl -w kernel.sched_migration_cost_ns=500000 2>/dev/null
echo "v2 optimizations applied"
```

相对成功基线，Decode 约 +0.13%，Prefill 约 +3.72%。这里只能说没有观察到 Decode 改善；失败运行的 34.81ms 不能用来估计正常噪声范围，也不能据现有重复次数认定 Prefill 变化必是噪声。

## 验证信号

原始推理退出状态用于淘汰 RC=1 基线；后续有效记录给出 35.75/15.51ms 与 37.08/15.53ms。要确认收益或退化仍需同机、同负载的交错多轮重复，并绑定每轮输出。

## 适用与失效边界

这是有限样本的无收益观测，不是 OS 调优普遍无效的证明。未做逐参数消融，不能外推到其他硬件、CPU 预处理占比或多卡负载。
