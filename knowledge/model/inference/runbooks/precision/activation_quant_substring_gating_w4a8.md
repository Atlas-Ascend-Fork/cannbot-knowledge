---
type: Runbook
title: 激活 8bit 量化分支按精确 == 'W8A8' 门控会漏掉 W4A8：改 'a8' 子串判断，否则该量化模式静默不生效
description: 激活 8bit 量化分支按精确 == 'W8A8' 门控会漏掉 W4A8：改 'a8' 子串判断，否则该量化模式静默不生效。启用了某个「激活 8bit」量化模式（典型 W4A8 = 权重 int4 + 激活 int8），推理不报错、但精度像没量化激活 / 收益不对——该量化模式名义上开了，但激活 int8 的融合算子路径（MoE dispatch 量化、init_routing 动态量化、dequant_swiglu_quant、MLA 的 mm_quant）根本没走，等于该模式静默失效。
tags:
- task.debugging
- topic.attention
- topic.mixture_of_experts
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/187
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 激活 8bit 量化分支按精确 == 'W8A8' 门控会漏掉 W4A8：改 'a8' 子串判断，否则该量化模式静默不生效

## 信号（现象）

启用了某个「激活 8bit」量化模式（典型 W4A8 = 权重 int4 + 激活 int8），推理不报错、但精度像没量化激活 / 收益不对——该量化模式名义上开了，但激活 int8 的融合算子路径（MoE dispatch 量化、init_routing 动态量化、dequant_swiglu_quant、MLA 的 mm_quant）根本没走，等于该模式静默失效。

## 触发条件

- 建模代码用**精确字符串相等**门控激活量化分支：`mm_quant_mode == "W8A8"` / `gmm_quant_mode == QUANT_MODE_W8A8`（常量值 `"W8A8"`）。
- quant_mode 由逐张量位宽拼成的小写串（W8A8 → `"w8a8"`、W4A8 → `"w4a8"`、无量化 → `"w16a16"`；小写因开源模型 quant_config 的 `type` 字段为小写）。
- 实际跑 W4A8（或任何 `!= "W8A8"` 的激活 8bit 模式）。

## 根因

激活量化分支门控写死为 `== "W8A8"`（甚至大小写都不匹配拼出的 `"w8a8"`）。W4A8 的 mode 是 `"w4a8"`，精确比较为 False → 不进 A8 分支，所有依赖它的激活 int8 算子被跳过、悄悄回落到非 A8 路径：

- [MoE dispatch](../../concepts/techniques/moe_dispatch_combine_v2.md)：`quant_mode` 取 0（应 2）、`scales=None`（应传 `smooth_scale`）；
- `npu_moe_init_routing_v2`：`quant_mode=-1`（非量化，应 1 动态量化）、`scale=None`；
- all_to_all 不传 `gathered_pertoken_scale`；
- shared-expert 不走 `npu_dequant_swiglu_quant`；
- [MLA](../../concepts/modules/mla.md)：`enable_mm_quant_a8w8=False` → 不做 `npu_dynamic_quant`、不传 MLA-Prolog 的 `dequant_scale`。

即门控只认一种字面量，把「同属激活 8bit」的其它模式排除在外，且无任何报错。

## 修法

把激活量化分支门控从精确相等改为**子串判断** `"a8" in mode`，使任何激活 8bit 模式（w8a8 / w4a8）都进 A8 路径：

```python
# 各激活量化分支统一改法
"quant_mode": 2 if "a8" in self.gmm_quant_mode else 0
quant_mode = 1 if "a8" in self.gmm_quant_mode else -1
enable_mm_quant_a8w8 = "a8" in self.mm_quant_mode
```

**刻意保留的例外**：只有 w8a8 需要走的分支（DenseMLP / SharedExpert 的 `down_proj_forward` 选择）仍用精确 `== "w8a8"`——维护者确认目前只有 w8a8 需走该分支，故此处不放宽为子串。即「按能力维度门控」而非「按单一字面量门控」：激活是否 8bit 用 `"a8" in`，某个只有 w8a8 支持的具体路径才用精确等于。

## 可迁移原则

- 量化模式门控要按**能力维度**判断，而不是枚举某个具体组合字面量。「是否激活 8bit」用 `"a8" in mode` 这类子串 / 位宽字段判断，才能让 W8A8、W4A8 等同族模式共用同一激活量化内核路径；写死 `== "W8A8"` 会在新增一个激活 8bit 权重档时静默漏路由。
- 这类失效**不报错、只是量化不生效**：新增 / 启用一个量化档后，要验证激活量化算子路径确实被走到（而非只看跑通），否则收益 / 精度会像没量化。

## 参考实现及其约束

参考 cann-recipes-infer DeepSeek 系三份同源 modeling（DeepSeek-R1 / DeepSeek-V3.2-Exp / Kimi-K2-Thinking）的 MLA 与 MoE 分支：门控由 `== QUANT_MODE_W8A8` 改为 `"a8" in mm_quant_mode/gmm_quant_mode`，涉及 [W4A8](../../concepts/quantization/w4a8c8.md) / [W8A8](../../concepts/quantization/w8a8c8.md) 与 MoE dispatch/combine、shared-expert；quant_mode 串在 `CompressedTensorsConfig._get_quant_mode` 拼出。范围限本仓这几份 DeepSeek modeling 的量化门控，不外推整栈。

## 相关经验

- compressed-tensors 加载器侧的方案识别门控（别假设总有激活量化、MX vs fp8 靠 weight_block_size、AWQ int4 走 W4A16）见 [compressed-tensors-scheme-gating-pitfalls](compressed_tensors_scheme_gating_pitfalls.md)——那是加载器路由 LinearMethod 的门控，本页是 modeling 侧激活量化分支门控，两处都属「量化 mode 门控写太窄导致误命中 / 漏路由」。

## Evidence

- `diff 事实` + `维护者确认`（@6293961c1089）：`compressed_tensors.py` 删常量 `QUANT_MODE_W8A8`/`QUANT_MODE_W16A16`、`_get_quant_mode` 拼小写串；DeepSeek-R1 / V3.2-Exp / Kimi-K2-Thinking 三份 `modeling_deepseek.py` 把 `== QUANT_MODE_W8A8` → `"a8" in`，`DenseMLP`/`SharedExpert` 保留精确 `== "w8a8"` 例外；维护者答复小写来源（开源 `type` 字段小写）与「只有 w8a8 需走 down_proj 分支」。W4A8 修后能进 A8 内核路径，源未给 before→after 性能 / 精度数字。溯源下探：[cann-recipes-infer-pr-187-fix-w4a8-a8](https://gitcode.com/cann/cann-recipes-infer/merge_requests/187)