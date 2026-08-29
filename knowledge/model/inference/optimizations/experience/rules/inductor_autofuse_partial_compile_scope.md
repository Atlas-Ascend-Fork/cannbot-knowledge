---
type: Optimization
title: inductor(autofuse) 部分图编译：按图结构稳定 / 范围 / pointwise 密度选子模块 + 收益观测
description: inductor(autofuse) 部分图编译：按图结构稳定 / 范围 / pointwise 密度选子模块 + 收益观测。在含动态结构（条件触发分支、稀疏 topk 等）的大模型上想用 inductor(autofuse) 昇腾编译做算子融合，但对整模型 fullgraph 编译代价大、且易因 Guard 叠加频繁重编译。此时不追求 fullgraph，而是挑"编译收益/代价比"高的子模块加 @torch.compile——本页给选范围的三条规则与一组收益观测。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/365
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a3
---

# inductor(autofuse) 部分图编译：按图结构稳定 / 范围 / pointwise 密度选子模块 + 收益观测

## 适用场景

在含动态结构（条件触发分支、稀疏 topk 等）的大模型上想用 [inductor(autofuse)](../../../concepts/frameworks/autofuse.md) 昇腾编译做算子融合，但对整模型 fullgraph 编译代价大、且易因 Guard 叠加频繁重编译。此时**不追求 fullgraph，而是挑"编译收益/代价比"高的子模块加 `@torch.compile`**——本页给选范围的三条规则与一组收益观测。

## 选子模块编译的三条规则

未对模型做过多改造以支持 fullgraph，按下面挑 `@torch.compile` 装饰的范围：

1. **图结构稳定**：编译范围内不含执行时分支选择、`.item()` 内存同步等行为，避免过多断图（Graph Break）。
2. **避免编译范围过大**：范围过大 Guard 叠加，更易触发重新编译。
3. **选含较多 pointwise/reduce 计算的范围**：inductor 对该类计算融合效果好，以较小编译代价获取性能收益。

据此实际加装饰的对象（观测实例落在 `Expert.forward` / `RMSNorm.forward` / `hc_head` / `hc_pre` / `hc_post` 这几个建模函数）。配套：不对输入做 padding 时，输入长度变化可能触发 dynamo 重编译（输入签名稳定见 [graph-mode-stable-input-signature-recompile](../../../runbooks/performance/graph_mode_stable_input_signature_recompile.md)）。

## 收益观测（仓自报，无独立复测）

环境：昇腾 Atlas A3；torch_npu PTA 2.8 + CANN nightly。baseline = **已替换 TileLang-ascend 算子、但未启用 inductor 编译**的模型（非纯原始模型）；统计口径只算 Device 上**非 Hcom 类算子**的 Kernel 耗时总和（Hcom Kernel 显著受 host 调度影响故剔除）；未使能 aclgraph 下沉调度（模型含未消除动态结构）。

| 模型级（非 Hcom Kernel 总耗时） | 未编译 | 编译后 | 提升 |
|---|---|---|---|
| Step 2（无 Compressor） | 49.8 ms | 39.5 ms | 20.6% |
| Step 4（触发 Compressor） | 52.8 ms | 42.0 ms | 20.4% |

| 片段级 hc_post | 未编译 | dynamic=False | dynamic=True |
|---|---|---|---|
| 耗时 | 30 us | 7.5 us（4x） | 10 us（3x） |

- **不外推单调规律**：模型级仅 2 个受控测点、片段级 1 个——只陈述在报告的这几组配置下的观测值，不外推"越大越…"。
- 收益量级对可比性依赖 baseline 口径（已上 TileLang 算子、非 Hcom、未开 aclgraph）——迁移评估时对齐 baseline。

## 参考实现及其约束

参考实现：DeepSeek-V4-Flash（已用 TileLang-ascend 算子的版本）的 inductor(autofuse) 部分编译（`Expert.forward` / `RMSNorm.forward` / `hc_head` / `hc_pre` / `hc_post` 五处 `@torch.compile`）。装饰的具体函数、baseline 口径是该 recipe 落点；三条选范围规则本身是 torch.compile/inductor 常识，适用面按证据限定到本 recipe 这几个建模函数，不升为整栈通用律。

## Evidence

- diff 事实 + doc 披露（@eb1092ac074f）：五处 `@torch.compile` 装饰器与 README 选范围三规则一致；规则依据（Graph Break / Guard 叠加 / 融合收益）为 README doc 披露。溯源下探 [cann-recipes-infer-pr-365-add-add-deepseek-v4-flash-model-and-tilelang-sfa-mhc-kernel-inductoraf-a](https://gitcode.com/cann/cann-recipes-infer/merge_requests/365)
- doc 披露（仓自报、无独立复测，@eb1092ac074f）：非 Hcom Kernel 总耗时 −20.6%/−20.4%、hc_post 片段 4x/3x；baseline 与统计口径按 README 原文保留。溯源下探 [cann-recipes-infer-pr-365-add-add-deepseek-v4-flash-model-and-tilelang-sfa-mhc-kernel-inductoraf-a](https://gitcode.com/cann/cann-recipes-infer/merge_requests/365)

<!-- cannbot:related:start -->
## 相关

- [AutoFuse（Inductor NPU 自动融合编译组件）](../../../concepts/frameworks/autofuse.md)（`related`）：“优先选择含较多 Pointwise / Reduce 计算的范围，Inductor 对这类计算的融合效果好，编译代价小、收益高。”给出 AutoFuse 的选域原则；“此时**不追求 fullgraph，而是挑"编译收益/代价比"高的子模块加 `@torch.compile`**——本页给选范围的三条规则与一组收益观测。”把该原则落实为动态模型的部分图编译和收益验证。
- [稳定图模式输入张量签名（shape/stride/dtype）避免 dynamo 重编译与缓存 miss](../../../runbooks/performance/graph_mode_stable_input_signature_recompile.md)（`related`）：“据此实际加装饰的对象（观测实例落在 `Expert.forward` / `RMSNorm.forward` / `hc_head` / `hc_pre` / `hc_post` 这几个建模函数）。配套：不对输入做 padding 时，输入长度变化可能触发 dynamo 重编译（输入签名稳定见 ［graph-mode-stable-input-signature-recompile］(../../../runbooks/performance/graph_mode_stable_input_signature_recompile.md)）。”；“图模式按输入张量的 **shape + dtype + stride 签名** 缓存/守卫（guard）已编译图；decode 每步输入的 shape/dtype/stride 只要有一维不稳，dynamo 就把它当新形态触发重编译或 guard 失效。”。部分编译范围的 Guard 风险与输入签名漂移的诊断规则相接，可从选范围继续定位重编译原因。
<!-- cannbot:related:end -->
