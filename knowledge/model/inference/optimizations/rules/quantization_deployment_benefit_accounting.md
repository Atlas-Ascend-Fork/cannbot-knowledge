---
type: Optimization
title: 量化权重变小仍 OOM：部署收益与峰值显存分账
description: 量化后额外 dynamic quant/dequant 开销变大、W8A8 显存不降或端到端变慢时，分账 FFN、KV、激活、workspace、通信与 host overhead，按相同部署条件验证。
tags:
- task.optimization
- topic.precision
- topic.memory
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-fusion-and-benefit.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md
  role: supporting
created_at: '2026-11-09T09:23:47Z'
updated_at: '2026-11-10T01:14:22Z'
platforms:
- agnostic
---

# 量化权重变小仍 OOM：部署收益与峰值显存分账

## 适用场景与信号

W8A8 量化显存不降，或 matmul 变快但 TPOT 无收益甚至劣化，或权重体积减少而峰值显存仍 OOM。固定 exec_mode、batch/每专家 token、TP/EP/DP 与 KV 量化策略后再比较，不能把不同部署或输入的结果相减。

## 优化规则与机制

将 Decode 的可见开销拆为 Attention、FFN GEMM、dispatch/通信与额外调度/同步。量化可能减少权重和 INT8 通信的搬运、改变 matmul 吞吐，也会增加 dynamic quant/dequant 及 host launch；未量化 KV 时不能声称 KV 带宽同步减半。多流重叠时不能直接累加 kernel Duration 得到 wall time，需观察关键路径。

memory-bound、compute-bound 和 launch/comm/sync-bound 的收益上限不同。图模式可摊薄下发，但不保证额外开销为零；小 batch、高 EP 下每专家 token 少时可能由调用开销主导。来源的固定百分比和阶段占比仅是示意，不作为其他硬件或模型的预测常数。

显存至少分为权重、KV cache、activation、GMM/workspace、通信预分配。估算量化后权重可用 W_quant = W_bf16 × (coverage × bit_ratio + 1 - coverage) + scale_metadata；实际还可能有布局副本与分配对齐。这个公式不估算整网峰值。GMM 的 int32 中间结果、通信区和未量化 KV 不一定下降，不能写“权重量化后所有 buffer 不变”或“总显存必减半”。

## 实施、收益与代价

先证明目标量化分支真实生效，再用 profiling 解释局部变化；最终收益用关闭 profiler 的同条件测量，分报 TTFT、TPOT/吞吐、峰值显存、部署卡数及精度。eager 与 graph 分别在各自匹配基线下测量，不能只准 graph 数据、也不能把 graph 结果称为剥离所有调度影响的纯量化收益。

LongCat-Flash-Lite README 的 W8A8 行同时使用多流且输入长度不同，只可作组合部署的绝对性能参考，不能直接与 BF16 行计算量化 speedup。内存 OOM 先区分权重驻留和 Prefill chunk/GMM workspace 峰值，再选择对应措施；没有降低后者时，权重已省仍可 OOM。

## 验证、回退与适用边界

保持实际权重、输入、warmup、卡数和其他优化开关一致，重复测量并保存波动；若无法控制变量，明确证据缺口，不归因到单一优化。精度失败回退原权重和相应执行路径；无时延收益但显存收益成立时，按部署目标权衡，不隐藏代价。来源自报性能没有独立真机复测。

相关：[量化接线](../../guides/integration/w8a8_mlp_and_moe_scale_flow.md)、[profiling 指标](../../guides/optimization/npu_profiling_collection_and_metrics.md)。

## Evidence

- [.agents/skills/model-infer-quantization/references/quantization-fusion-and-benefit.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-fusion-and-benefit.md)
- [models/longcat_flash_lite/README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md)
