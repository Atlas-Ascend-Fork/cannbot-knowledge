---
type: Guide
title: MLIR/DVM共享分解：训练梯度、GELU选择与未注册辅助
description: 区分MLIR/DVM共享分解的真实安装、空BatchNorm/卷积bias/softmax梯度、GELU精度和未注册RMS/SwiGLU/Rotary辅助；补后端lowering接线、快照恢复与设备分派机制。
tags:
- task.optimization
- topic.compilation
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/decomposition.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_inductor_plugin.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering_patch.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering_common.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
created_at: '2026-11-11T09:28:22Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# MLIR/DVM共享分解：训练梯度、GELU选择与未注册辅助

## 固定主线与已有代码生成指南的区别

本文依据TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的_register_mlir_dvm_decompositions完整函数及相邻模块声明，只另核必要imports、anir配置排除列表与插件的真实调用点。它补充[DVM代码生成/FX回退](../../inference/guides/optimization/torch_npu/torch_npu_dvm_mlir_codegen_and_fallback.md)没有展开的数学注册层，不以整文件引用代替1221行全部完成。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`没有在本卡建立同一数学合同，不将主线改写直接外推。

没有导入后端、注册dispatch、调用兼容开关、运行Tensor数学、生成/编译kernel或设备实验；平台未知，保持draft和空平台。MLIR加载另有弃用与依赖门槛，沿[后端配置与加载](../../inference/guides/optimization/torch_npu/torch_npu_inductor_config_parsing.md)核对，不从函数存在推导当前产品已验收或所有DVM子图采用这些分解。

## 真正调用点、共享排除表与非事务安装

npu_inductor_plugin在模块级导入并调用这个registrar；decomposition.py的583–608相邻块只是实验Triton的说明及_te_python_dispatcher_lib=None声明，并未在该块调用MLIR/DVM注册。函数进入时才导入anir config，后者模块体有共享Inductor config.allow_buffer_reuse=False赋值；不能把这一层buffer复用开关解释为设备allocator不缓存或所有输出永不复用，也不把每次import语句都视为重新执行模块体。

exclude_list直接引用anir_config.decomps_to_exclude_npu，没有先复制。只有os.getenv('TORCHINDUCTOR_NPU_BACKEND','default')**精确等于'mlir'**时才append aten._safe_softmax；这里不strip、casefold，也没有改为读取torch.compile的options字典。环境值与外部实际loader选择是否一致仍需核对。

配置列表含GELU前反向、embedding三项、nearest1d/2d/3d及bilinear2d前反向、NLLLoss各列出的前反向、triu、convolution_backward、_softmax_backward_data、max_pool2d_with_indices及反向、slice.Tensor、reflection_pad2d及反向、grid_sampler_2d及反向和expm1。remove_decompositions作用于共享Inductor分解字典；**同一函数随后又注册其中部分项**，不能把排除列表直接当作最终所有原生fallback清单。

该registrar没有本地完成标志、统一锁或回滚try/finally。列表可先被原地修改，之后双py_impl或分解注册再失败；重复调用也没有本地去重保证。外部注册器的覆盖/冲突和真正native fallback执行独立，不能概括为任何安装失败都会原子恢复或静默改走CPU。

## 当前实际安装的训练与数学入口

| 入口 | 本地实际处理 |
|---|---|
| aten.batch_norm.default | py_impl绑定Autograd与AutogradPrivateUse1两键；不是在这里枚举全部device kernel。 |
| convolution_backward | 仅在请求bias梯度时拆出bias求和，随后调用原aten、把bias mask改False；否则返回NotImplemented。 |
| _softmax_backward_data.default | 用乘法、sum、减法表达梯度，再按条件转dtype并contiguous；没有显式FMA调用。 |
| erf.default、gelu.default、gelu_backward.default | 安装下述FP32中间路径与兼容开关选择。 |
| expm1 | 实际为exp(x)-ones_like(x)，不以专用原生expm1算法或小值误差已验收解释。 |

BatchNorm的空输入分支先clone input；weight非None时只用weight[0]相乘，bias非None时只用bias[0]相加，然后返回临时out。它不是直接返回原input，也没有在这条分支逐通道重建完整统计；不能为少一次copy就删除clone或从这段推导任意空shape/Optional/训练状态都等价。非空时把原输入、weight/bias、running_mean/var、training/momentum/eps/cudnn_enabled直接交_batch_norm_impl_index.default，只取返回[0]；running统计的完整更新/别名合同在外部实现。

卷积bias梯度为sum(grad_output,[0]+range(2,grad_output.dim()))，保留channel轴；另外两项通过带[mask0,mask1,False]的aten.convolution_backward取得。NotImplemented不是本地执行CPU fallback的证明，递归dispatch/其他分解如何接手仍独立。这里没有单独验证所有卷积rank、输出mask长度、dtype、转置/分组或底层算法。

softmax反向先p=grad_output*output，s=sum(p,dim,keepdim=True)，再算p-output*s；当grad_output.dtype与input_dtype不同才转回input_dtype，最后contiguous。这里没有像[实验softmax覆盖](../../inference/guides/optimization/torch_npu/torch_npu_experimental_triton_softmax_decomposition_and_mask_domain.md)那样在这个函数上挂同一个pw_cast_for_opmath装饰器，不能直接并成相同计算dtype路线。实数表达式相同也不保证所有浮点逐位一致；contiguous可能带来的存储工作应与算术一起检查。

## GELU/erf的近似选择和dtype时点

approximate='tanh'走近似路线；'none'取not are_compatible_impl_enabled()。兼容API导入或查询抛任意Exception时回False，因此查询不可用时none也走近似。其它值报RuntimeError，没有在这些wrapper再按NPU device进行门控；安装到共享表后实际适用范围需结合调用路线。

前向对非FP32输入先转FP32：近似式为x/(1+exp(-beta*(x+kappa*x³)))，beta=1.595769121605730711759、kappa=0.044715；另一式为(1+erf_pade(x/√2))*(0.5*x)。erf_pade先将输入限制在[-3.92,3.92]，再用固定x²的P/Q Horner有理近似；单独erf也沿该路径。最后恢复原输入dtype，不能据FP64输出称中间保留了全FP64精度。

反向以grad.dtype决定转换：grad非FP32才把grad和self都转FP32，grad已经FP32则没有对self单独cast。近似分支构造px/div/resp，仅把resp中的NaN替成0，再返回grad*(resp+div)；erf分支返回grad*(cdf+self*pdf)。最终按原grad dtype恢复。局部NaN替换不是所有输入特殊值、混合dtype或前后向整体数值的认证。

这组常量/表达式可与[实验GELU数学指南](../../inference/guides/optimization/torch_npu/torch_npu_experimental_triton_gelu_rmsnorm_dropout_rng_decompositions.md)对照，但本卡仍保留MLIR/DVM安装上下文，不把同公式理解成相同注册时机、原生kernel或任意模型误差已经相同。无本地输入值域、正数epsilon或完整dtype组合证明。

## 定义存在但六条注册仍被注释

以下辅助函数在registrar内完整定义，却没有由末尾被注释的六条register_decomposition安装。本卡不能把它们作为本次已启用的RMSNorm/SwiGLU/Rotary优化推荐，也不据此否定其他后端/其他注册入口。

| 辅助函数 | 所写数学与未闭合条件 |
|---|---|
| npu_rms_norm及反向 | 前向x.float后按最后轴mean(x²)+epsilon求rsqrt，乘x与weight后转原x dtype，返回output/rsqrt；weight不统一cast。反向直接写dx公式，dgamma沿tuple(range(grad_output.dim()-1))归约，没有统一cast-back。空tuple、任意rank、实际weight广播仍按外部Tensor.sum合同另核。 |
| npu_swiglu及反向 | chunk(x,2,dim)后silu(first)*second，反向用sigmoid导数并cat两半；没有在这里独立检查dim、偶数长度或所有广播shape。 |
| npu_rotary_mul及反向 | 最后轴chunk两半并cat(-second,first)旋转，再做t*cos+rotate(t)*sin；反向返回grad_t、t*grad、rotate(t)*grad。cos/sin梯度没有在本函数按广播轴sum_to_size，不能当作任意广播完整梯度合同。 |

这些函数没有因为定义在同一个安装器里就变成被调用的分解，也不能用内部返回类型注解替代实际tuple和输入校验。选择后端优化时应核最终表项、环境与options、可变排除表、安装完成点、近似/兼容状态、实际dtype及空输入/广播/梯度需求，再独立验收模型数值和性能；本次没有新增verified。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/decomposition.py)（primary）：1–17,289–608行；仅所列完整registrar/相邻声明或必要配置/模块调用点，不提升整文件资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/config.py)（implementation）：7–7,11–11,22–22,298–327行；仅所列完整registrar/相邻声明或必要配置/模块调用点，不提升整文件资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/npu_inductor_plugin.py)（implementation）：102–104行；仅所列完整registrar/相邻声明或必要配置/模块调用点，不提升整文件资格。

## MLIR/DVM 后端的 lowering 接线与快照恢复

本节记录「后端如何挂上/摘下 torch inductor lowering」接线层，依据主线 `torch_npu/_inductor/lowering_patch.py`（348 行全文）、`lowering_common.py`（492 行全文）与 `_inductor/__init__.py`（475 行全文）。发布 pin 全树（含 torchnpugen/）无 lowering_patch.py/lowering_common.py（find 零命中），发布版扁平 lowering.py 的另一套白名单回退机制已由[发布版 lowering 白名单卡](../../inference/guides/optimization/torch_npu/torch_npu_release_flat_inductor_lowering_whitelist_fallback.md)闭合，两版不可互推；loader 层的环境与入口合同见[配置解析卡](../../inference/guides/optimization/torch_npu/torch_npu_inductor_config_parsing.md)，本节只覆盖 patch 本体。

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| import torch_npu._inductor（`__init__.py:474` 模块级 `_load_backend()`） | `_load_backend`（:455-472）先 `restore_inductor_baseline()`（:459），再按 `TORCHINDUCTOR_NPU_BACKEND`（缺省 default，:87-88）从 `_BACKEND_LOADERS`（:431-437：mlir/dvm/ascendc/default/triton_experimental）取 loader，未知名字 get 回退 Triton loader；loader 返回后统一 patch_overlap_scheduling、`fast_random_decomps.cache_clear()` 并记录 `_loaded_backend` | 恢复只覆盖本节所列面；模块级更早执行的顶层 patch（如 :43 `npu_patch_meta()`、:44-45 设备接口注册）不在恢复清单内，是否需要恢复未在本卡核对 |
| backend 精确为 `mlir` | `_load_mlir_backend`（:117-138）：FutureWarning 弃用提示 + `_apply_common_patches()` + 要求 torch_mlir 可导入，然后 `apply_mlir_inductor_patch()`（:137）与 `register_mlir_codegen_backend()`（:138） | 弃用与依赖门槛已在配置解析卡记录，此处不重复；torch_mlir 本体不在本卡范围 |
| backend 精确为 `dvm` | `_load_dvm_backend`（:141-177）：`_configure_dvm_compile_threads()`（backend 精确 'dvm' 时把 TORCHINDUCTOR_COMPILE_THREADS 与 config.compile_threads 置 1）后，执行与 mlir 相同的 `apply_mlir_inductor_patch()`（:156）+ `register_mlir_codegen_backend()`（:157） | DVM 与 MLIR 共用同一条 apply 链；has_triton 分支的 FlexAttention 补丁属[DVM 融合执行卡](../../inference/guides/optimization/torch_npu/torch_npu_dvm_mlir_codegen_and_fallback.md)范围 |
| backend 为 default/triton（或未知回退） | `_load_triton_backend` 末尾 `install_device_lowering_dispatch(LOWERING_OVERRIDE_OP)`（:305，位于 allfallback 分支之外，两种 fallback 模式下都执行） | 该调用点的分支语义已在[Triton matmul 卡](../../inference/guides/optimization/torch_npu/torch_npu_inductor_triton_matmul_kernel_family.md)记录；本节补 dispatcher 本体（下文） |

### 快照与恢复

`capture_lowering_baseline`（lowering_patch.py:68-86）首次调用时把 `torch._inductor.lowering` 的本模块函数表（`get_module_functions` 只收 `inspect.getmodule(func) is module` 的函数，导入来的不算）、`lowerings` 字典（引用 + 浅拷贝）、`LOWERING_REGISTRY_ATTRS` 七个注册表属性（lowering_common.py:49-57：`lowerings`/`_maybe_layout_constraints`/`fallbacks`/`needs_realized_inputs`/`foreach_ops`/`inplace_foreach_ops`/`inplaceable_foreach_ops`）与 `make_reduction` 存入模块级 `_BASELINE`，之后重复调用幂等返回同一快照。当前接线中首次 capture 发生在 `_load_backend` 开头的 restore（:459 → :244），即 import 时、任何 loader 之前；docstring 声明的「captured before any NPU patch」是该调用顺序的结果，不是运行时强制——若别的路径在首次 capture 前已改 lowering，快照会冻结已改状态。

`restore_lowering_baseline`（:242-268）只写回快照中存在且当前仍存在的函数名（`hasattr` 门）；快照之后**新增**的函数名不会被删除。`lowerings` 若被整体替换过则先换回原 dict 对象再 clear+update 快照拷贝；七个注册表属性按 clear+update（有该能力时）或 setattr 拷贝恢复；`make_reduction` 恢复。`restore_inductor_baseline`（:297-305）在此之上再恢复 7 个调度/IR 属性（:275-294，经 `inspect.getattr_static` 快照）：`GraphLowering.propagate_mutation`、`ir.Layout._stride_expr_ge_or_false`、`Scheduler._codegen`、`Scheduler.compute_ancestors`、`inductor_scheduler._prune_redundant_deps`、`Scheduler.can_fuse_vertical`、`Scheduler._get_unmet_dep_nodes`；基线中不存在的属性若当前存在则 delattr。这 7 个属性与各 patch 家族实际触碰面的逐一对账未做（patch 模块本体不在本卡范围），不能说恢复覆盖了所有 loader 的全部全局修改。

### apply 的替换与合并

`apply_mlir_inductor_patch`（:337-348）从 `ascend_npu_ir` 包导入 `inductor_patch.lowering`（NPU lowering 模块）与 `inductor_patch.scheduler._patch_scheduler`，并副作用导入 `inductor_patch.ir`（源码注释：注册 TracedGraph 钩子），随后执行 `apply_mlir_lowering_patch(npu_lowering)` 与 `_patch_scheduler()`；ascend_npu_ir 包内部实现不在本卡闭合范围。

`apply_mlir_lowering_patch`（:316-334）按序做四件事：同名函数 setattr 覆盖（只覆盖 NPU 模块内定义的函数）；`merge_missing_lowerings`（:307-313）把 inductor `lowerings` 中 NPU 侧缺少的键补进 NPU lowerings——方向是**把 fork 缺失的键从上游补入**，fork 未声明的 op 由此保留上游 handler；七个注册表属性整体替换为 NPU 模块对象；`importlib.reload(torch._inductor.graph)`。reload 会重执行 graph 模块体，其对已存在 graph 实例与缓存的所有副作用未在本卡核对，不能当成无操作。

### 设备分派 dispatcher

`install_device_lowering_dispatch`（:212-239）对每个目标 op（OpOverloadPacket 先展开成全部 overload，:89-100；overload 总数取决于上游 torch schema，本卡不报数）从**快照**取 upstream_handler、从**当前** lowerings 取 device_handler，跳过四类：快照无该 op、当前无 NPU handler、两者同一对象、或当前已是 dispatcher（`_torch_npu_device_lowering_dispatch` 标记判定）。包装器（:176-196）以 `functools.wraps(device_handler)` 生成，每次调用按 `_uses_device_lowering`（:148-173）选边：layout kwargs 的 device type 优先；`INDUCTOR_ASCEND_DUMP_FX_GRAPH` 或 `INDUCTOR_ASCEND_CHECK_ACCURACY` 环境下 device kwarg 可解析时接受 npu/cpu；再按 args/kwargs 的 pytree 叶子 `get_device()` 类型命中；最后查 extra 谓词。默认谓词表（:141-145）只有 `prims.convert_element_type`：目标 dtype 非 float64、源是 CPU fp64 0-dim 且 npu ∈ `V.graph.device_types` 时走设备 lowering（源码注释原义：把 CPU fp64 标量 cast 挡在生成的 NPU kernel 外）。该机制只被 Triton loader 调用；MLIR/DVM 路径不走 dispatcher，直接整体替换 lowering。

### lowering_common 的共享辅助

`run_once`（:34-46）的语义已由[meta 注册链卡](../../inference/guides/optimization/torch_npu/torch_npu_meta_registration_patch_chain.md)等记录（成功一次后 has_run=True、可手动重置、无锁），`_apply_common_patches`（`__init__.py:47-48`）即用之，此处不重复。`fallback_ops_with_meta`（:99-129）与 `enable_full_lowering_fallback`（:132-150）是 allfallback 策略的公共实现：先对 lowerings 中不在 decompositions 的 OpOverloadPacket/OpOverload/HigherOrderOperator（减 excluded_ops）逐个 make_fallback，再对全 dispatch 表中有 Meta 或 CompositeImplicitAutograd kernel 且未覆盖的 op 补 fallback；其消费点与发布版的逐字等价对照已在发布版 lowering 白名单卡闭合，本卡不重复。`TracedGraph` 家族（:153-492：`TracedGraph` 包装、`fetch_graphs`（跳过三层嵌套内的 ConcatKernel；`use_npu_meta=True` 时 fake_input 经 `.npu()`）、`merge_traced_graphs`/`merge_fx_graphs`/`subtract_graph`、`process_ir_constant`（ExpandView/IndexingConstant 的 fp32/fp16/bf16 转 float 或符号图，ir.Constant 取 value，其余 skip））与两组算符编码表（TRITON：前缀 `_`、单字母；MLIR：前缀 `_uwu_`、`xvx?` 且含逗号）用于把 sympy 表达式编码成 FX placeholder 名，canonical 此前零引用；其消费者（ascend_npu_ir inductor_patch.ir 的钩子）不在本卡闭合范围，不能据此推导 DVM 融合的图构建行为。

## 补充来源

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering_patch.py)（primary）：1–348 行全文逐行。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering_common.py)（primary）：1–492 行全文逐行。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）：1–475 行全文（四个连续窗口读毕）；接线结论以 `_load_backend`/`_BACKEND_LOADERS`/各 loader 与 restore 调用点为限。
