---
type: Guide
title: LongCat-Flash A3 部署与优化验收流程
description: 串联固定版本 LongCat 的权重、配置、图缓存与优化案例，区分已撤回 KVP 和来源性能观测。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/longcat_flash_optimization.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/runner_longcat_flash.py
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/config/longcat_flash_densetp8_ep32.yaml
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/config/longcat_flash_densetp8_ep32_gegraph_mtp.yaml
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/config/longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/config/longcat_flash_densetp8_ep128_gegraph_mtp_eplb_w8a8.yaml
  role: supporting
created_at: '2026-10-21T09:02:43Z'
updated_at: '2026-10-23T09:41:54Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - moe
        - mla
---


# LongCat-Flash A3 部署与优化验收流程

## 目标、输入与产物

面向固定 cann-recipes-infer `2f82d10467e6fe8dae81c97a2cdac78d733a6703` 的 Atlas A3 LongCat-Flash 实践，串联已有机制、规则、案例与故障入口。输入包括平台/卡数、权重精度、实际 YAML、prompt 和目标指标；产物包括有效配置、输出验收、计时与 profiling 记录，以及可恢复的开关和缓存配置。

这里描述固定历史实践，不声称当前软件包已运行验证。模型结构见[LongCat 模型](../../concepts/models/longcat_flash.md)，完整历史 KVP 条件见[KVP 机制](../../concepts/parallelism/kvp.md)。

## 1. 固定版本并准备权重

先保存源码 commit、CANN/PyTorch/torch_npu 实际版本、节点 IP 与卡数，按固定 README 准备依赖；不能把安装示例版本当作测量环境。BF16 转 W8A8 的源入口是 `models/longcat-flash/utils/convert_model.py`：

```bash
python models/longcat-flash/utils/convert_model.py \
  --input_bf16_hf_path /data/models/LongCat-Flash-Chat \
  --output_hf_path /data/models/LongCat-Flash-Chat-W8A8
```

记录原始权重与输出路径，核对实际量化布局；不要仅凭目录名认定转换成功。转换路径选择见[权重转换指南](../deployment/quant_weight_conversion_path_selection.md)。

## 2. 按实际配置选择并行与执行模式

以下是旧模型总览中的配置示例，不是任意卡数的自动推荐；`world_size` 沿用 YAML 单位，不能直接当作物理 Chips。

| 配置 | world_size | 固定实践中的差异 |
| --- | --- | --- |
| `longcat_flash_densetp8_ep32.yaml` | 32 | BF16、dense TP8、o_proj TP1、MoE EP32；eager，MoE chunk 1024 |
| `longcat_flash_densetp8_ep32_gegraph_mtp.yaml` | 32 | BF16、o_proj TP8、GE、`next_n=1` |
| `longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml` | 128 | W8A8、AFD、MTP2、perfect EPLB、SuperKernel 与预取的组合 |
| `longcat_flash_densetp8_ep128_gegraph_mtp_eplb_w8a8.yaml` | 128 | 非 AFD 的 W8A8/GE/MTP/EPLB 组合 |

核对权重路径、实际加载的 YAML 和各并行组，按[局部 TP 案例](../../optimizations/cases/longcat_dp_tp_projections.md)检查 Attention DP 与投影/MLP TP 的布局边界。AFD 的 rank 配对、互斥关系与关闭方式由[AFD 规则](../../optimizations/rules/afd_attn_ffn_disaggregation.md)维护。

`perfect_eplb` 是[性能上界测试设置](../../optimizations/rules/perfect_eplb_profiling_upper_bound.md)，精度验收时不能直接复用。KVP 配置已在后续固定版本撤回，当前流程不提供启用步骤；历史配置及守卫只从[KVP 历史入口](../deployment/kvp_longseq_decode.md)查阅。

## 3. 准备 prompt 并运行固定入口

按固定 README 修改 `model_path`、`infer.sh` 的 `YAML_FILE_NAME`，核对 `executor/scripts/set_env.sh` 中节点 IP 与 CANN 路径。内置 prompt 位于 `dataset/default_prompt.json`；长序列路径使用 README 指定的 LongBench 数据准备方式，不将两种输入混成一次受控对比。

```bash
cd models/longcat-flash
bash infer.sh
```

多机需要各节点按同一配置执行。保存原始输出、退出状态与实际加载的配置；本次知识迁移没有执行该命令或模型。

## 4. 按规范入口逐项验收优化

| 任务 | 规则或实现证据入口 |
| --- | --- |
| GE 编译与缓存 | [图模式流程](../optimization/graph_mode_decode_only_compile_backends.md)、[缓存规则](../../optimizations/rules/torchair_cache_compile_persisted_graph.md) |
| ScMoE 多流与控核 | [多流规则](../../optimizations/rules/decode_multi_stream_overlap_core_balance.md)；核数和 stream 参数不在本 Guide 重复定义 |
| QBMM/MLAProlog 预取 | [LongCat 预取案例](../../optimizations/cases/longcat_a3_decode_weight_prefetch.md) |
| SuperKernel 范围与布局修复 | [LongCat SuperKernel 案例](../../optimizations/cases/longcat_a3_superkernel_layout_fusion.md) |
| MTP 状态与计时 | [MTP 接入](../integration/mtp_speculative_decode_model_onboarding.md)、[计时规则](../../optimizations/rules/mtp_decode_timing_two_metric_split.md) |
| 长序列 Prefill OOM | [MoE 峰值内存诊断](../../runbooks/performance/moe_prefill_oom_peak_memory.md)；固定 README 的 chunk 开关只针对 Prefill，可能影响其性能 |

固定 runner 用 `CASE_NAME` 组织图缓存；主模型目录与 MTP 的 `_spec` 目录分开，MTP 选择 `mtp_compile_decode` callable。这里保留 LongCat 的路径差异，缓存失效、版本与后端限制统一读取缓存规则；旧文档“不支持 acl_graph”只限定当时的 LongCat 路径。

## 5. 验证、停止与回退

逐项改变开关，保持 prompt、卡数、精度与计时口径相同，同时验收输出和性能，保存重复次数与波动。缓存修改前保存对应配置和路径；失败时恢复匹配的一组配置与缓存，再按关联 Runbook 排查，不以旧缓存混配新部署。

来源自报性能集中在[LongCat A3 观测](../../optimizations/benchmark_observations/longcat_a3_afd_source_benchmark.md)。本 Guide 不宣称完成精度、性能或回退实验；遇到平台、权重或后端不符时停止套用该实践。

## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/README.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/longcat_flash_optimization.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/runner_longcat_flash.py)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/config/longcat_flash_densetp8_ep32.yaml)
- [固定来源 5](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/config/longcat_flash_densetp8_ep32_gegraph_mtp.yaml)
- [固定来源 6](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/config/longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml)
- [固定来源 7](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/config/longcat_flash_densetp8_ep128_gegraph_mtp_eplb_w8a8.yaml)

本次核对固定来源及必要配置，不将文档自报、来源固定或 Lint 通过记作硬件验证事件。
