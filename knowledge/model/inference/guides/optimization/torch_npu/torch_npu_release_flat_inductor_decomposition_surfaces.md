---
type: Guide
title: torch_npu 发布版 Inductor 分解注册的三处表面与主线公式级差异
description: 记录发布 pin 分解注册的三个表面（后端分支互斥、表面可叠加）：default 分支 decomposition.py（erfc 的 1-exp 公式、native_dropout npu 路由）、mlir/dvm 插件 npu_decomp.py 模块级副作用（排除表、batch_norm py_impl、恒 tanh 的 gelu）、dvm/decomp.py patch_decomp，及主线整合为 per-backend registrar 后的 erfc/rms dgamma/gelu 近似族差异。
tags:
- task.implementation
- topic.compilation
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/decomposition.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_decomp.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_inductor_plugin.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/decomp.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/decomposition.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_inductor_plugin.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/decomp.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
created_at: '2026-11-12T08:00:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 发布版 Inductor 分解注册的三处表面与主线公式级差异

## 固定版本与适用范围

发布 pin（f3ecfe4a）的后端顶层分支 mlir/dvm/default（`__init__.py:8-20`）互斥；分解表面并不互斥：default（Triton）分支 `__init__.py:37/:109` 调 `decomposition.py` 的 `_register_npu_inductor_decompositons()`（拼写如此）；mlir（`:14`）与 dvm（`:18`）分支经 `npu_inductor_plugin.py:124` `from ..npu import npu_decomp` 触发 `npu_decomp.py` 的模块级副作用；dvm 分支另由 `dvm/mlir_fusion.py:318` 调 `dvm/decomp.py:118` `patch_decomp()`（`:25` 导入；外层函数未逐行读）——即 dvm 分支同时消费插件 npu_decomp 与 patch_decomp 两个表面。default 分支 rg 零命中 npu_decomp——分支级接线互斥是结构事实，表面叠加不构成互斥。主线把后两处并入 `_inductor/decomposition.py`（1221 行）的 per-backend registrar；主线共享分解的数学合同已由[MLIR/DVM 共享分解卡](../../../../training/guides/torch_npu_mlir_dvm_decomposition_registry_and_training_math.md)建卡、主线 triton 分支由[矩阵分解与 BatchNorm 卡](../../../../training/guides/torch_npu_triton_matmul_backward_and_batchnorm_decomposition.md)建卡，本卡只写 release 侧事实与两 pin 差异。纯静态阅读；draft、platforms 为空。

## 表面一：default 分支（`decomposition.py`，63 行全文读）

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| 后端加载即注册（`:109`），无开关 | DECOMPOSITION_OVERLOAD_OP（`:10-22`，9 项：_log_softmax、nll_loss_forward/backward、_log_softmax_backward_data、embedding_dense_backward、addmm、gelu、native_dropout(+backward)；`:13-14` 有注释掉的 gelu_backward/gelu 重复行）先从 torch decompositions 删除（`:29-31`），阻止 torch 隐式分解 | 删除表是 release 清单；主线 triton 分支另扩 native_layer_norm、repeat_interleave.Tensor（带 perf 注释）、slice_backward、matmul(+backward)、条件 embedding_dense_backward、is_ascend950 的 max_pool2d_with_indices、expm1、erfc |
| `register_decomposition([aten.expm1])`（`:33-36`） | `exp(x) - ones_like(x)` | 与主线 triton 分支（主线 `:259-262`）相同 |
| `register_decomposition([aten.erfc])`（`:38-41`） | **`ones_like(x) - exp(x)`** | 与数学 erfc(=1-erf(x)，erfc(0)=1) 不同族：该式在 0 处给 0。主线已改为 `ones_like(x) - erf(x)`（主线 `:264-267`）——`1-exp(x)` 公式是 release-only 差异，只记录公式不推断数值影响 |
| `register_decomposition(aten.native_dropout)`（`:43-52`，`@out_wrapper("out0","out1")`） | `torch._inductor.config.fallback_random` 为真且 train 且 p≠0 → `torch.ops.npu._npu_dropout`；否则函数体内运行时 import 上游 `torch._decomp.decompositions.native_dropout` | npu 路由带 train/p≠0 门槛；否则回上游分解 |
| `register_decomposition(aten.native_dropout_backward)`（`:54-63`） | fallback_random 时 `p = 1 if scale == 0 else 1-1/scale` 后调 `torch.ops.npu.npu_dropout_backward(grad, mask, p)`；否则上游 | scale→p 换算只存在于这条 npu 路上；主线 triton 分支清单无 native_dropout，主线以 `_npu_decomp_override` 属性另行接线（主线 `:1042-1044`，rg 未逐行） |

## 表面二：mlir/dvm 插件（`npu_decomp.py`，204 行全文读，导入即副作用）

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| npu_inductor_plugin 模块导入（mlir/dvm 分支） | `:19` `remove_decompositions(inductor_decomp.decompositions, anir_config.decomps_to_exclude_npu)` | release anir 排除表 27 项（`config.py:228-255`：gelu(+backward)、embedding 三项、upsample nearest1d/2d/3d+bilinear2d 前反向、nll_loss 家族、triu、convolution_backward、_softmax_backward_data、max_pool2d_with_indices(+backward)、slice.Tensor、reflection_pad2d(+backward)、grid_sampler_2d(+backward)）；主线同表 28 项，仅新增 `aten.expm1`（两 pin config.py 文本比对） |
| 同上 | `:22-52` `batch_norm_decomposition` 以 `py_impl` 挂 `DispatchKey.Autograd` 与 `AutogradPrivateUse1` 两键；numel==0 快路径 clone 后仅乘 `weight[0]`/加 `bias[0]`；非空转 `_batch_norm_impl_index` 取 `[0]` | 与主线整合版（主线 `:302-332`）逐行等价；注释称修复动态 shape dynamo 追踪问题 |
| 同上 | `:195-198` 注册 4 个分解：convolution_backward（bias 梯度自拆 `sum(grad,[0]+range(2,dim))`，其余经 `[mask0,mask1,False]` 原算子）、_softmax_backward_data.default、gelu.default、gelu_backward.default | 前两者与主线 `:334-382` 逐行等价；gelu 见下行 |
| gelu/gelu_backward（`:161-193`） | 恒走 tanh 近似：`kBeta=√2·(2/√π)·0.5`、`kKappa=0.044715`，`0.5a(1+tanh(kBeta(a+kKappa·a³)))`；**approximate 形参被忽略** | 主线整合版重写为非 fp32 先转 fp32 + `are_compatible_impl_enabled` 兼容开关 + erf PADE 有理近似（主线 `:447-570`，见共享分解卡）；release 版无 erf decomp、无显式 fp32 上翻、无近似模式分路——公式族差异记录，不做精度结论 |
| npu_rms_norm_backward（`:115-121`） | `dgamma = (grad*x*rsqrt).sum(0)` | 主线改为对 `range(dim-1)` 全前缀维归约（主线 `:402-406`，带 gamma 广播注释）：release 版 rank>2 时中间维不归约——静态差异记录 |
| 注释掉的注册（`:199-204`） | npu_rms_norm/swiglu/rotary_mul 前反向 6 行注册被注释 | 函数体仍在（`:104-159`）但未注册（dead）；主线同样保持注释状态 |

相邻插件行为（同文件选段阅读，非逐行）：`disable_implicit_decomposition`（插件 `:128-144`）对 8 个 upsample vec/default 算子从 `decomposition_table` 弹出 Autograd/CompositeImplicitAutograd 内核；`_patch_run_node` 的 FA 追踪补丁（`:158-162`）对 `npu.npu_fusion_attention` 的 `actual_seq_qlen/kvlen` kwargs 转 list。插件路径另有固定 `FALLBACK_LIST`（`config.py:193-225`，29 项：头 7 项为 mm/bmm/addmm/convolution/convolution_backward/_adaptive_avg_pool2d/max_pool2d_with_indices，尾部另含 max_pool2d_with_indices_backward、avg_pool2d 前反向、lookup_seed/random/device_put、upsample_nearest2d 前反向、embedding、`npu._npu_dropout` 等；`npu_lowering.py:27` 遍历全表消费），与[lowering 白名单卡](torch_npu_release_flat_inductor_lowering_whitelist_fallback.md)的 default 分支运行时记录表是两张表。

## 表面三：dvm（`dvm/decomp.py`，123 行）

排除表 `decomps_to_exclude_npu`（`:10-30`，19 项：gelu(+backward)、nll_loss 前反向、linalg_vector_norm、_log_softmax(+backward)、embedding_dense_backward、batch_norm 家族 5 项（_batch_norm_with_update/_batch_norm_with_update_functional/_batch_norm_no_update/native_batch_norm/batch_norm_backward）、native_group_norm、convolution_backward、_softmax(+backward)、`npu.npu_rotary_mul(+backward)`）。`patch_decomp()`（`:118-123`）先 `remove_decompositions` 再注册 sigmoid/gelu_backward/gelu/tanh 四个分解（`:120-123`）；函数体 `:30-110` 不在逐行范围（`:110-114` 可见 sigmoid 为 fp32 上翻 `1/(1+exp(-x))` 形）。主线 dvm/decomp.py（332 行）的 `patch_decomp`（主线 `:305-332`）重写为幂等 guard + matmul fold override + CIA 分解禁用 + dvm_decompositions 表 + enable/disable 列表 + extra_random_decomps 清理，排除表（主线 `:13-55`）扩为 41 项：`npu.npu_rotary_mul(+backward)` 仍保留（`:53-54`，与 release 同项），另加入 dropout/index_select/max_pool/reflection/grid_sampler 等条目——dvm 表面两 pin 差异显著，不可互推。

## 主线整合与顺序约束

- 主线插件目录无 `npu_decomp.py`（ls/rg 零命中）；插件改为调 `_register_mlir_dvm_decompositions()`（主线插件 `:102-104`，行读确认），release npu_decomp 内容并入主线 `decomposition.py:289+`；主线另有 `_register_triton_experimental_decompositions`（主线 `:1146+`，结构索引）与[实验 Triton 数学分解卡](torch_npu_experimental_triton_gelu_rmsnorm_dropout_rng_decompositions.md)覆盖的隔离树表面。
- 顺序约束：release `__init__.py:112` 注释要求 fx pass 注册放在 decompositons 注册之后（`:109` → `:152` 调用序相符），与[fusion attention 图模式卡](torch_npu_release_flat_inductor_fusion_attention_pattern.md)互链；静态注释不构成运行时依赖证明。
- release default 分支的 `_log_softmax/nll_loss` 系删除与[lowering 白名单卡](torch_npu_release_flat_inductor_lowering_whitelist_fallback.md)的 `make_fallback(aten._log_softmax/nll_loss_forward)`（`lowering.py:318-320`）配合：分解删除后走 extern fallback，不重复生成。

## 失效边界与静态口径

- 后端顶层分支（mlir/dvm/default）互斥；分解表面可叠加：dvm 分支同时吃 npu_decomp 副作用与 patch_decomp（双表面叠加，叠加后果未运行验证，只记录结构）。
- erfc/rms dgamma/gelu 近似族差异均为公式级静态记录，不据此对任何版本的数值精度或性能下无条件结论；实际 kernel 行为按对应 CANN 版本核对。
- 与[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)（`:37/:109` 接线行与拼写）边界互链；[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)不涉及分解表面。
