---
type: Guide
title: SGLang 昇腾功能选型与支持矩阵冲突
description: 合并新旧 NPU 功能表，保留平台特例、GPU专用项、计划功能和同版本矛盾。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/reference/support_features.mdx
  role: primary
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/Support%20Features%20on%20Ascend%20NPU.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/server_arguments.mdx
  role: supporting
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/advanced_features/server_arguments.mdx
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/utils.py
  role: implementation
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-09T04:30:20Z'
platforms:
- a2
- a3
- '950'
---

# SGLang 昇腾功能选型与支持矩阵冲突

## 使用方法

支持表中的单项勾选是框架功能声明，不证明任意模型、精度与特性组合可用。新表大多数基础加载、tokenizer/HTTP/TLS、内存调度、TP/多节点、日志/指标、grammar、Mamba状态、multimodal、编码器拆分、权重loader和memory-saver等项列A2/A3/950；旧表仅列A2/A3。最终应以目标模型配方和实现约束交叉核对，不能把安装整包范围作为所有子功能的证据。

## 平台与实现专属项

- attention/prefill/decode backend列ascend，多模态列ascend_attn；sampling为pytorch或ascend，quantization列ModelSlim、dtype为FP16/BF16。量化格式和KV dtype应再查专门量化指南，不把普通GPU FP8 GEMM选项搬到NPU。
- 新表`dp-size`、LoRA overlap loading、fuseep-mode、DeepEP dispatcher输出dtype、speculative MoE a2a、hierarchical cache enable、prefill CP/strategy等仍只标A2/A3；其余相关开关即使有950也不能补齐缺失产品声明。LoRA标题限定Qwen系列；lora-backend新增ascend/torch_native/csgmv等，不意味着这些后端都可跨任意模型。
- fuseep-mode1注明batch≤256；ascend_fuseep注明与EPLB不兼容。dispatcher输出int8需相应量化checkpoint并配DEEP_NORMAL_MODE_USE_INT8_QUANT=1；enable-quant-communications要求设置dispatcher output dtype。
- HiCache明确不支持Mamba cache；IO后端列kernel_ascend/direct，布局page_first_direct/page_first_kv_split，存储file。CPU/group offload要求禁用graph，group选项限定DeepSeek，sharded_gpu模式还限定TP1/DP>1，不能从参数名称推断普通NPU路径都支持。
- GPU专用项包括ModelOpt、GPU DSA/GEMM backend、NVLS/symmetric-memory、FlashInfer/MXFP4、MSCClpp、LMCache、elastic EP等；Ngram是experimental，TBO与部分draft-window/gRPC项是planned。Ktransformer/checkpoint-engine依赖不兼容，tool-server有已知功能缺口。它们不是“加开关即可启用”的NPU优化。

## 必须保留的冲突

1. 新表PP行写“PP2不支持、不能与TP同用”，但同快照GLM5.2/5.3等配方明确组合TP和PP。它可能针对未说明的子路径，不能上升为全部NPU并行契约。
2. CP行写CP=TP、prefill CP行又称仅DeepSeek V4；同快照Qwen235教程给TP16/CP2且其他GLM配方也启用CP。不要依据表格单独否定或放宽模型路径。
3. 新推测正文支持target-only线性/树候选，非greedy按temperature/top_k/top_p构造target分布；rejection采样限EAGLE3/NEXTN、eagle-topk1且不能与非默认接受阈值/确定性推理组合。但表格又把eagle-topk写成只支持1、rejection写planned。区分请求top_k与draft分支topk，并核对实际实现，不能只选有利的一条。
4. 新表PD transfer要求显式ascend，并称默认mooncake不支持NPU；通用PD文档却仍给NPU Mooncake路径。按传输构建、版本和实际后端核对，不宣称两者任意互换。

## 新旧迁移

旧表的graph-bs/max-bs、piecewise/torch.compile开关与新表prefill/decode分开的接口不同；新表prefill backend只列disabled并明确移除tc_piecewise。旧Mamba full-memory ratio默认0.2、scheduler-strategy在新表变成ratio0.9和radix-cache-strategy；gRPC、SBO、确定性推理的支持状态也发生变化。旧脚本应逐项核对CLI/配置解析和启动日志，不能只替换镜像继续使用。表中默认值是来源快照，不是统一推荐性能值；本次未执行任何上游验证。


## 通用参数页补充与冲突

通用参数页把enable-quant-communications说明为仅NPU Qwen3系列的INT8 TP通信；专门NPU表却用DeepEP dispatcher输出dtype解释同一开关。它们涉及不同通信路径，不能仅凭名称当作所有TP/EP统一量化能力。DeepEP dtype选择说明的优先级为CLI、deprecated env、input_global_scale、quant config、部分backend、NPU BF16默认；显式int8只标A2/A3，不能借此扩展950。

通用页还有实验ascend_ops后端：prefill可allgather/alltoallv，decode在文档和 choices 中列low_latency/fused_op，但固定实现 AscendOpsConfig.__post_init__ 无条件拒绝 fused_op 并要求使用 low_latency，故当前可用配置应选 low_latency；使用推测模型时target和draft须都选ascend_ops，并共用moe-ascend-ops-config。该入口未列于专门支持表的允许值，不能依据旧表否定其源码入口，也不能据“experimental NPU”宣称所有芯片已验证。phase attention覆盖优先于总attention-backend；LoRA/HiCache/PD的候选值存在于通用CLI不等于全部选项可在NPU使用。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/reference/support_features.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/reference/support_features.mdx)（primary）
- [sgl_docs：docs/hardware-platforms/ascend-npus/Support Features on Ascend NPU.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/Support%20Features%20on%20Ascend%20NPU.mdx)（primary）
- [sglang：docs/docs/advanced_features/server_arguments.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/server_arguments.mdx)（supporting）
- [sgl_docs：docs/advanced_features/server_arguments.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/advanced_features/server_arguments.mdx)（supporting）
