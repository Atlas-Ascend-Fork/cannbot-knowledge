---
type: Guide
title: FlexAttention eager autocast 补丁：注册链与设备校验替换
description: 闭合 patch_flexattention 的真实安装点、AutocastPrivateUse1 语义与 _validate_device 替换后果，区分 inductor 侧同名 patch。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/patch_flexattention.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/npu_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/patch_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/transfer_to_npu.py
  role: implementation
created_at: '2026-11-12T03:58:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FlexAttention eager autocast 补丁：注册链与设备校验替换

## 模块本身不注册：真实安装点是 import torch_npu

固定 TorchNPU 主线 ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf 的 `torch_npu/utils/patch_flexattention.py`（137 行，全文）。模块只定义 4 个函数；模块级除 import 语句外不调用任何注册/patch 函数：单独 `import torch_npu.utils.patch_flexattention` 不会注册任何 kernel，模块 docstring 的"Import this module ... to register"按当前代码不成立。

真实安装链（rg 全树闭合）：`import torch_npu` → `__init__._initialize()` 第 3 步 `_apply_all_patches()` → PatchManager 按固定组序（monkey、api、distributed、dynamo、profiler、npu、warning、asd）执行 → 自动发现并 import `torch_npu/_init/patches/npu_patches.py` → `apply_flex_attention_patch()` 依次调用 `_patch_flex_attention_device()` 和 `_register_npu_flex_attention_autocast()`。即主线下 import torch_npu 会在初始化时**尝试安装**这两项改动，但不是无条件必然生效：`_patch_flex_attention_device` 在 `torch.nn.attention.flex_attention` 导入失败时静默返回（不 patch），已置 `_npu_device_patched` 标志时跳过；`_register_npu_flex_attention_autocast` 对两个 HOP 分别用 `has_kernel_for_dispatch_key(AutocastPrivateUse1)` 判重，已有 kernel 时跳过注册。

docstring 提到的 transfer_to_npu 与 inductor 两条导入路径：本固定树内 `transfer_to_npu.py` 未 import 该模块（其 flex 相关内容是把 `torch.utils._triton.has_triton` 置 False 以短路 `IS_FLEX_ATTENTION_CUDA_PLATFORM_SUPPORTED` 等 CUDA 门控，属另一机制）；`torch_npu/_inductor` 也没有 import 该 utils 模块。docstring 的"两条路径共用、幂等"是设计说明，不是本树实际调用点清单。

## AutocastPrivateUse1 kernel 语义

`_register_npu_flex_attention_autocast` 对 `flex_attention` / `flex_attention_backward` 两个 higher-order op 用 `py_impl(DispatchKey.AutocastPrivateUse1)` 注册 NPU 内核，注册前用 `has_kernel_for_dispatch_key` 判重，可安全重复调用。

| kernel | 行为 |
| --- | --- |
| 前向 | 按 `query.device.type` 取 `torch.get_autocast_dtype`，用 `torch.amp.autocast_mode._cast` 只 cast Q/K/V（score_mod、block_mask、scale、kernel_options 及 other buffers 均不动），再在 `_ExcludeDispatchKeyGuard(AutocastPrivateUse1)` 下重派发避免递归 |
| 反向 | 不做任何 cast，仅排除 autocast key 后原样重派发；依据"backward 在 autocast 上下文外运行、前向图已在 AOTAutograd 捕获时记录 cast"的约定，saved tensor 不被重新 cast |

边界：cast 覆盖面只有 Q/K/V 三个输入；autocast dtype 取当前设备类型的全局设置；本卡静态阅读，未在设备上验证 eager 前反向数值。torch.compile 内的 FlexAttention 路线见 [Inductor FlexAttention 接口](torch_npu_inductor_flex_attention.md)与[前向分派](torch_npu_flex_attention_forward_dispatch.md)。

## _validate_device 替换不保留 CUDA 白名单

`_patch_flex_attention_device` 把 `torch.nn.attention.flex_attention._validate_device` 整体替换为 `_npu_valid_device`：`query.device.type != "npu"` 时直接 return（不报错）；npu 时仅检查 q/k/v 三者同设备。用模块级 `_npu_device_patched` 标志保证幂等。

后果：上游对 CUDA 白名单的设备校验不再保留——非 NPU 设备（含 CUDA）的输入一律放行，设备合法性的实际约束后移到后续算子/lowering 层。`from torch.nn.attention import flex_attention` 失败时静默跳过（不 patch），适用于 torch 版本无该模块的场景。

## 与 inductor 侧同名 patch 的区分

`torch_npu/_inductor/kernel/flex_attention.py` 自带另一个同名 `patch_flex_attention`（改写 score-mod 路由与 streaming BlockMask 创建，见[前向分派卡](torch_npu_flex_attention_forward_dispatch.md)）和一个 no-op `_validate_device`。`torch_npu/_inductor/__init__.py` 在加载 Triton 后端时调用的是后者，DVM 路径还会把 `flex_attention._validate_device` 指到该 no-op 版本。两个 patch 机制独立、名字相同：eager autocast 注册（本卡）与 inductor 元数据改写不能互相推断，一边生效不代表另一边已应用。实验 Triton 适配器对共享 patch 的委托见[实验适配器卡](torch_npu_experimental_flex_attention_source_adapter.md)。

## 发布版状态

发布 f3ecfe4a7ef7395754da7ca2e35661a7132b519b：同路径 `torch_npu/utils/patch_flexattention.py` 不存在；对整个发布 `torch_npu/` 树检索 `flex_attention`/`flexattention`（含不区分大小写的 `flex`）无任何 FlexAttention 相关命中（`flex` 命中仅为 `FlexibleLayout`、图树注释等无关符号），`_inductor` 亦无 flex_attention kernel。据实记录：该发布树内未发现任何 FlexAttention 支持路径；这只是本固定树的检索结论，不推断其他发布分支或后续版本全局缺失该能力。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/patch_flexattention.py)（primary，全文 1–137）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/npu_patches.py)（implementation，全文 1–60）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/patch_manager.py)（implementation，全文 1–216）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/__init__.py)（implementation，全文 1–77）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py)（implementation，1–40、745–775、1300–1320）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation，160–240）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/transfer_to_npu.py)（implementation，340–380）
