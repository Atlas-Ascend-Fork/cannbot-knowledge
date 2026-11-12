---
type: Guide
title: MiniMax-M2.5在A3的外部EAGLE3与A2单请求配方
description: 比较 MiniMax QuaRot W8A8 在长前缀、低延迟和高并发下的 DeepEP/fuseep 与调度选择。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/minimax_m2_5.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/minimax_m2_5.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/autoregressive/minimax-m25-deployment.jsx
  role: supporting
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T12:38:11Z'
platforms:
- a2
- a3
---

# MiniMax-M2.5在A3的外部EAGLE3与A2单请求配方

## 固定条件

教程要求SGLang v0.5.18、CANN9.0 A3镜像，后续版本没有被该教程覆盖。目标为W8A8 QuaRot权重约230.82GB，容量起点TP8（4物理卡）；EAGLE3需单独custom eagle checkpoint、其路径加入PYTHONPATH，并设置`SGLANG_EXTERNAL_MODEL_PACKAGE=custom_eagle3`。不能把普通draft模型视为可替代这一外部包。

## 负载决定通信与缓存

32K随机方案TP8、DeepEP auto、ZBAL graph/VMM、chunk=-1、禁用Radix、EAGLE3 steps3/topk1/draft4，max-running18。64K共享前缀改为ascend_fuseep、融合模式2、保留Radix、prefill-delayer、chunk67072，max-running26。128K共享前缀扩到TP16/DP2，prefill-max4/max-running4；文本吞吐方案则TP16/DP16、fuseep、prefill-delayer、禁用Radix。`SGLANG_NPU_FUSED_MOE_MODE=2`与另一命令的`--fuseep-mode 2`是来源保留的不同接口写法，需核对实际版本，不能默认全版本等价。

服务端解析器分别为minimax-append-think和minimax-m2。长序列dispatch token上限最高到数十万，是对应配方值，不可拿其替代其他模型的内存预算或通信容量验证。

## 上游报告

以下均A3 W8A8 INT8，缺重复次数、误差和完整warmup，本次无设备测试。

| 物理卡 | 负载 | 报告TPOT |
|---|---|---|
| 4 | RANDOM32768/1024，并发18、72请求、seed1 | 50ms |
| 4 | 前缀58982+后缀6554/1024，1组104请求、并发26 | 50ms |
| 8 | 前缀117965+后缀13107/1024，1组16请求、并发4 | 24.44ms |
| 8 | RANDOM3500/1500，并发112、448请求、seed1 | 20ms |
| 8 | 同长度，并发320、1280请求、seed1 | 50ms |

共享比例90%是生成工作负载定义，尚需服务侧测命中率。后两行静态内存、max-running、chunk和graph范围也不同，不能把吞吐/延迟差归给单一融合通信开关。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/minimax_m2_5.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/minimax_m2_5.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/minimax_m2_5.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/minimax_m2_5.mdx)（constraint）

## Cookbook生成器的A3参考与A2单请求入口

A3生成器固定8物理卡/16die、TP16/DP16/FuseEP2，EAGLE3 3/1/4 unquant、static0.75/max-running320、chunk196608/max-prefill8192、prefill-delayer passes500、graph1/2/4/8/12/16/20，端口6688。它保留external custom_eagle3包、主draft绝对路径及HCCL/Gloo接口输入，按完整命令复现；生成器明确标A3硬件验证待完成，不能借A2观测消除这一限制。

A2是独立的8×910B4/32GiB入口：TP8/ModelSlim/BF16、无draft、context4096/max-running1、chunk128/max-prefill4096、static0.96/max-total4096、禁图/Radix、端口31216，reasoning parser为minimax而非A3的minimax-append-think。UI将两种NPU的卡数和parser开关锁定，只是这些预设的编辑限制，不是任意部署的能力断言。工具parser配置不等于工具调用测过。详见[上游A2有限观测](../../../optimizations/benchmark_observations/sglang_ascend/sglang_ascend_doc_minimax_m2_5_a2_observation.md)。

- [docs/src/snippets/autoregressive/minimax-m25-deployment.jsx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/autoregressive/minimax-m25-deployment.jsx)（supporting）
