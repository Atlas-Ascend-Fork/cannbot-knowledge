---
type: Guide
title: SGLang 在 A3 部署 GLM-5.1 的长上下文与前缀复用配方
description: 比较 GLM-5.1 W4A8 混部及 PD 分离中的 CP、DeepEP、推测解码和上游负载指标。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/glm_5_1.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_1.mdx
  role: constraint
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T11:58:59Z'
platforms:
- a3
---

# SGLang 在 A3 部署 GLM-5.1 的长上下文与前缀复用配方

## 适用范围和起点

固定来源描述 GLM-5.1（744B 总参数、40B 激活、MLA/DSA、内置 MTP）的 A3 配方。教程以 SGLang v0.5.16 编写，却提供 CANN 9.1 `a3-B105` 验证构建镜像；这不是稳定发布与任意后续版本的兼容证明。BF16 权重约 1.51TB，W4A8 约 420.17GB；教程给出的容量起点是 TP8、8 个 64GB die，即其 A3 计数中的 4 张物理卡。性能配方使用更多卡，不能把容量起点当吞吐配置。

## 按工作负载选并行组合

混部示例跨两节点 TP32、DP16，静态内存比例 0.65、chunk 65536、max-prefill 280000、graph 最大 batch 16，NEXTN 为 steps3/topk1/draft4，draft 设置 unquant。解析器为 glm45/glm47。这些是一组具体参数，改变精度、并行或负载后需重新验证。

PD 长上下文的 P 端采用 TP32/CP32 interleave、DeepEP normal、禁用图；D 端 TP32/DP32/EP32、DP attention、DeepEP low_latency、graph batch 1/2/3。128K 配方 P 使用 ZBAL 分配和 send/recv，P NEXTN 为 1/1/2、D 为 3/1/4；16K 配方使用分轮 combine、每轮 1024 token、16 轮，P/D 静态比例 0.75/0.87。不能把 P/D 的队列模式、通信缓冲、graph 或 speculative 参数互换。

64K 的另一种 P 配方使用 TP4/PP8/CP4 zigzag，D 保留 TP32/DP32/EP32。前缀复用专用方案保留 Radix cache，采用共享前缀数据集；一般随机长序列方案中的 `--disable-radix-cache` 不应直接复制到该方案。

## 上游报告的观测

来源将以下数据列为 A3、W4A8 INT8 的结果，均没有说明独立重复次数、误差区间与统计聚合方法；本次没有运行设备测试。

| 方案 | 物理卡数 | 输入/输出 token 与请求 | 报告 TPOT/TTFT |
|---|---:|---|---|
| 混部 | 16 | 3.5K/1.5K | TPOT 50ms；具体请求参数以来源命令为准 |
| PD | 32 | RANDOM 131072/1024，32 并发、32 请求、seed1 | TPOT 56.4ms，TTFT 13.1s |
| PD | 32 | RANDOM 16384/1024，128 并发、512 请求、seed1 | TPOT 50ms |
| PD，TP32 P | 32 | RANDOM 65536/1024，1 并发、1 请求、seed1 | TPOT 55.2ms，TTFT 7.58s |
| PD，TP4/PP8 P | 32 | RANDOM 65536/1024，32 并发、64 请求、seed1 | TPOT 50ms |
| PD，90% 共享前缀 | 32 | 59904 共享+6656 后缀/1536 输出，1 组、480 请求、并发100、rate=inf | TPOT 25ms |

这些行工作负载和资源安排不同，不能相减得到 CP、PP、缓存或 PD 的独立加速比。复现应记录 warmup、服务端实际配置、checkpoint 含 MTP 情况以及平均和尾延迟。

参见[参数调优边界](../../optimization/sglang_ascend/sglang_ascend_doc_parameter_tuning.md)和[安装版本组](../../deployment/sglang_ascend/sglang_ascend_doc_installation_version_sets.md)。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/glm_5_1.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/glm_5_1.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_1.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_1.mdx)（constraint）
