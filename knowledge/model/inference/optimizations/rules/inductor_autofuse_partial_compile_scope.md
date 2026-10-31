---
type: Optimization
title: inductor(autofuse) 部分图编译：按图结构稳定 / 范围 / pointwise 密度选子模块 + 收益观测
description: 按固定 A3 实践中的图稳定性、Guard 范围和 pointwise/reduce 密度选择 AutoFuse 编译片段；性能数据集中到独立观测，分别验收精度、冷启动与稳态执行。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/365
  role: evidence
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_autofuse_guide.md
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:29:19Z'
platforms:
- a3
---
# inductor(autofuse) 部分图编译：按图结构稳定 / 范围 / pointwise 密度选子模块 + 收益观测

## 适用场景

在含动态结构（条件触发分支、稀疏 topk 等）的大模型上想用 [inductor(autofuse)](../../concepts/frameworks/autofuse.md) 昇腾编译做算子融合，但对整模型 fullgraph 编译代价大、且易因 Guard 叠加频繁重编译。此时**不追求 fullgraph，而是挑"编译收益/代价比"高的子模块加 `@torch.compile`**——本页给选范围的三条规则与一组收益观测。

## 选子模块编译的三条规则

未对模型做过多改造以支持 fullgraph，按下面挑 `@torch.compile` 装饰的范围：

1. **图结构稳定**：编译范围内不含执行时分支选择、`.item()` 内存同步等行为，避免过多断图（Graph Break）。
2. **避免编译范围过大**：范围过大 Guard 叠加，更易触发重新编译。
3. **选含较多 pointwise/reduce 计算的范围**：inductor 对该类计算融合效果好，以较小编译代价获取性能收益。

据此实际加装饰的对象（观测实例落在 `Expert.forward` / `RMSNorm.forward` / `hc_head` / `hc_pre` / `hc_post` 这几个建模函数）。配套：不对输入做 padding 时，输入长度变化可能触发 dynamo 重编译（输入签名稳定见 [graph-mode-stable-input-signature-recompile](../../runbooks/performance/graph_mode_stable_input_signature_recompile.md)）。

## 收益观测（仓自报，无独立复测）

[独立来源观测](../benchmark_observations/autofuse_a3_source_benchmark.md)维护两类计时数据。优化前后须分别核对编译后执行、冷启动及精度，不能把非 Hcom Kernel 总和视为端到端时延。

## 参考实现及其约束

参考实现：DeepSeek-V4-Flash（已用 TileLang-ascend 算子的版本）的 inductor(autofuse) 部分编译（`Expert.forward` / `RMSNorm.forward` / `hc_head` / `hc_pre` / `hc_post` 五处 `@torch.compile`）。装饰的具体函数、baseline 口径是该 recipe 落点；三条选范围规则本身是 torch.compile/inductor 常识，适用面按证据限定到本 recipe 这几个建模函数，不升为整栈通用律。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/365)（evidence）
- [deepseek_v4_autofuse_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_autofuse_guide.md)（supporting）

## 后端接入与回退

固定文档要求先导入 `inductor_npu_ext` 注册后端，再给选定函数添加 `@torch.compile`；模型文件本身没有该导入，不应视为完整启动程序。接入失败、输出不对齐或重复测量无净收益时，恢复原始函数与后端配置；本仓未验证回退效果。
