---
type: Guide
title: torch_npu Meta注册链：npu_patch_meta安装、avoid_fallback与Inductor分解补丁
description: 记录两版npu_patch_meta安装点、Meta接管动作序列、注册清单与主线QR/SVD布局修复的版本边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/_npu_meta_registration.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_npu_meta_registration.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_meta.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_meta.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_inductor_plugin.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_inductor_plugin.py
  role: implementation
created_at: '2026-11-12T11:06:10Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu Meta注册链：npu_patch_meta安装、avoid_fallback与Inductor分解补丁

torch_npu 用 `register_meta_npu`/`npu_patch_meta` 机制改写进程共享的 ATen Meta kernel 与分解表，让 FakeTensor、torch.compile 与 Inductor 在 npu 输出 dtype/shape 与官方实现不同时按 npu 规则推断。两 pin 的实现文件、安装点与注册清单不同。本卡只静态直读源码，不执行任何 patch、构图或编译。

## 两版路径与安装点

| 版本 | 实现文件 | 安装点与时机 |
| --- | --- | --- |
| 主线 ac0e1564 | `torch_npu/_inductor/_npu_meta_registration.py`（273 行） | `torch_npu/_inductor/__init__.py:38` 导入、:43 无条件调用；上方注释原文声明这是所有 inductor backend（triton/mlir/dvm/ascendc）都需要的 NPU 设备级 patch，与 codegen 后端选择无关、在任何 backend loader 之前执行——导入 torch_npu._inductor 即生效，不必等真正编译 |
| 发布 f3ecfe4 | `torch_npu/utils/_npu_meta_registration.py`（108 行） | `torch_npu/utils/__init__.py:25` 导入；`torch_npu/__init__.py:188` 在 `_apply_class_patches()`（:169-188，import torch_npu 的类补丁链）内调用——import torch_npu 即生效 |

两版 `npu_patch_meta` 都套 `run_once`：函数成功返回一次后 `has_run=True`，之后的调用直接返回 None，可手动把 `has_run` 置 False 重置；失败后可重入，但已写入的全局项没有统一回滚，装饰器无锁。

## 注册表与npu_patch_meta动作序列

`register_meta_npu` 装饰器把 fn 登记进 `npu_meta_table`：OpOverload 直接登记，packet 展开全部 overloads（主线版还支持一次传入 op 列表）；同一键重复登记 RuntimeError。`avoid_fallback_flag=True` 的项同时进 `avoid_make_fallback_table`（两版同名）；主线另有 `inductor_decomp_table`（`inductor_decomp=True`）。

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| 表项不在 avoid_make_fallback_table | 写 `torch._decomp.decomposition_table[op] = fn` | avoid_fallback=True 跳过的只是本 patch 这一次 `decomposition_table[op]=fn` 赋值（:131-132）；不是『该算子不会被分解』的全局保证——分解表既有条目未被本 patch 移除，后续是否分解取决于调用时的表内容 |
| 每个表项 | `op.py_kernels.pop(DispatchKey.Meta)` 删除官方 Meta kernel 后 `op.py_impl(DispatchKey.Meta)(fn)` 重挂 npu 版 | 两版相同，对进程全局生效；无按模型/按图隔离 |
| 主线：表项不在 META_BLACKLIST | 再写 `torch._decomp.meta_table[op]`（:137），并仅当拼接的 `aten/<op>/<Meta>` 键已存在于 `torch.library._impls` 时（:145）先移除该键、再经本文件局部 `Library("aten","IMPL","Meta")` 重挂（:146-147）；键不存在时不注册新的 Library impl | 黑名单六项 empty_strided/clone/copy_/constant_pad_nd/rot90/as_strided_scatter 只做前两步；其注释各带一条失败回归名（无限递归、requires_grad mismatch 等），是排除原因，不是已修复声明 |
| 主线：执行末尾 | `inductor_decompo.fast_random_decomps.cache_clear()`；`patch_torch_decomp_decompositions()` 把 FakeTensor 的 `torch_decomp_decompositions` 查询替换为 lru_cache 包装（本地表命中返回 True，否则交保存的原函数）；`patch_torch_inductor_decompositions()` 只把 inductor_decomp=True 的项写入 `torch._inductor.decomposition.decompositions` | 发布版只有 torch_decomp 查询包装，没有 inductor 分解表补丁，也没有 fast_random 缓存清理——inductor 侧分解补丁整层是主线新增 |

## 注册清单与两版差异

主线 4 组注册（`@register_meta_npu` 共 4 处）：`aten.sort` 四个 overload（avoid_fallback=True；`device_hint=="npu"` 时返回同 shape/dtype 的 empty values 与 int64 indices，否则委托 `torch._meta_registrations.meta_sort`）；`aten.index_put.default`（返回 `self.new_empty(self.shape)`）；`native_dropout` 与 `native_dropout_backward`（均 inductor_decomp=True，前向 :181-197、反向 :202-211，两向门不同）。前向（:181-197）：`fallback_random` 开启时（:182-193），train 且 p≠0 分支对 meta 张量返回 `empty_like` 输入加 uint8 mask（mask 元素数按输入 numel 向上取整 128 再 //8）、对非 meta 张量直接调 `torch.ops.npu._npu_dropout(input, p)`；其余 train/p 组合返回输入自身别名与 `ones_like` bool mask；`fallback_random` 关闭时回退 `torch._decomp.decompositions` 官方分解。反向（:202-211）：`fallback_random` 开启时（:203-207）没有 train/p≠0 门——meta 张量返回 `empty_like(grad_output)`，否则 p 取 1（scale==0）或 1-1/scale 后调 `torch.ops.npu.npu_dropout_backward(grad_output, mask, p)`；关闭时同样回退官方分解。发布版只有 `index_put.default` 一项。发布版 utils 文件里 `break_fn_table` 与 dynamo 相关导入（symbolic_convert、InstructionTranslatorBase 等）在该固定文件内无消费点（静态观察，不推断用途与历史）。

## 主线QR/SVD fallback布局修复（模块导入即安装）

主线文件尾部模块级执行 `_npu_fix_qr_fallback_layouts()`：包装 `torch._inductor.ir.FallbackKernel.process_kernel`，对 example_output 用 as_strided 按 contiguous 行主序 strides 重写——`linalg_qr`（default/out 两个 overload）的 tuple/list 输出全部成员逐一经 `_rowmajor` 改写；`_linalg_svd` 只重写第一个输出 U（`eo[0]`，:266），其余成员原样保留；`_rowmajor` 对非 Tensor、0 维标量与非 npu 张量原样返回（:240-246）。源码注释给出动机：torch_npu eager 的 aclnn QR 返回行主序 Q/R，而 ATen meta 声明 LAPACK 列主序，Inductor 按 meta 执行构造 fallback 输出布局，下游按转置 strides 读取导致 svd_lowrank/pca_lowrank 谱塌缩（注释引 #5072）；实现兼容 2.13 的位置 5 元组与 2.14+ 的 ProcessKernelResult dataclass 两种上游返回契约。发布版无此修复；该动机描述来自源码注释，未在设备复现谱塌缩。

## 同机制家族与边界

`_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_meta.py` 两版自带同一机制（独立 `npu_meta_table`，与本卡的表互不共享）：主线版 73 行无注册项，发布版 113 行含一条旧式 native_dropout 注册（128 对齐//8 mask 公式）。它由 `npu_inductor_plugin.py` 在 MLIR 插件导入时另行调用（主线 :51、发布 :75），且两个调用点之后都把 `torch._inductor.config.layout_optimization` 与 `config.size_asserts` 置 False（本轮行段所见，两开关的后续语义未深读）。发布 `torch_npu/__init__.py:95` 另行导入 `torch_npu.op_plugin.meta._meta_registrations`，属 op-plugin 侧注册（另仓审计范围）。TorchAir 的同机制卡见[编译前Meta补丁](../torchair/torchair_meta_fake_tensor_and_global_patch_lifecycle.md)——其来源是 torchair/_utils，prose 相似但不能背书 torch_npu 路径；本卡全部结论以 torch_npu 两 pin 源码为准。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/_npu_meta_registration.py)（primary，全文 1–273）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_npu_meta_registration.py)（primary，全文 1–108）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation，30–50）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation，70–120、160–200、285–305）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py)（implementation，全文 1–31）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_meta.py)（implementation，全文 1–73）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_meta.py)（implementation，全文 1–113）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_inductor_plugin.py)（implementation，40–55）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_inductor_plugin.py)（implementation，60–80）
