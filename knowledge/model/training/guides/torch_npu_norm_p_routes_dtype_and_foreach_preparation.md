---
type: Guide
title: 普通范数执行：p路由、dtype与Foreach转换
description: 区分Norm与VectorNorm的p及CANN路由、输出dtype规则，并核对ForeachNorm的类型转换、标量输出与24项分批。并含 linalg_vector_norm 的 acl_op 回退内部：FP32中转、两段LpNorm命令与复数硬拒。并含普通 norm 的 acl_op 回退内部：无复数硬拒、FP32中转与硬 dtype 收口。并含 renorm/renorm.out/renorm_ 的 maxnorm 子张量重归一：FP16 中转、命名剥离版本差与独立原地符号。并含npu_renorm_backward 的 host 组合实现（主线独有）。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NormKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgNormKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ForeachNormKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NormKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgNormKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ForeachNormKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LinalgNormKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LinalgNormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/NormKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/NormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RenormBackwardKernelNpu.cpp
  role: implementation
created_at: '2026-11-12T01:58:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 普通范数执行：p路由、dtype与Foreach转换

普通norm、linalg_vector_norm与_foreach_norm使用不同的p门控和输出类型准备。前两者可能转旧ACL，Foreach还会逐Tensor cast并按24项拆块；慢路线名称不表示本地已转CPU。

| gate/入口 | 实际行为 | 可见准备成本 |
|---|---|---|
| 普通norm/vector_norm，AclnnOnly或版本helper认为CANN>=9.0.0 | p门控不选择旧ACL | 仍有后续兼容检查、输出申请/检查 |
| 较旧CANN，p不在0/1/2/3 | 通常旧ACL；>=8.1.RC1时±inf例外 | 可能切换实现，不能只按算子名估算 |
| Foreach fast失败、整数/Bool/复数输入、p不合条件 | 对应ATen slow | 不是本地统一cast到浮点后执行fast |
| Foreach>=2.4的选定dtype不同于输入 | 检查不窄化，再逐项_npu_dtype_cast | 每项转换与每项标量输出申请 |
| Foreach fast通过 | 每24项一块及余数块 | 一个API入口可能对应多个ACLNN调用 |

## norm与vector_norm的顺序和dtype不能混用

普通norm先做DO_COMPATIBILITY(aclnnNorm,旧ACL表达式)，再计算p门控。calculate_p缺省取2，将Scalar按浮点读取并将±inf映射为float(INT_MAX/INT_MIN)哨兵；比较来自float，不能当作任意高精度Scalar的等价比较。真正传给aclnnNorm的仍是原p Scalar（缺省2），不是这个哨兵。

linalg_vector_norm先按原Scalar的float值做旧ACL选择，然后才执行aclnnLinalgVectorNorm兼容检查；其±inf门使用INFINITY值。两者的版本helper分别缓存IsGteCANNVersion("9.0.0","CANN")与"8.1.RC1"判断，本卡不展开安装版本探测实现。宏地址缺失时仍服从AclnnOnly抛错规则，不能把p门返回“不选ACL”理解为任意p必定执行成功。

普通norm functional按请求dtype申请，复数输入时却将输出改为对应实数：ComplexFloat→Float，其余复数分支→Double；dtype并未作为独立SDK实参传给aclnnNorm。普通norm.dtype_out签名虽含dtype，进入内部函数时使用的实际值是out.scalar_type()，与不带dtype的out一致。不能据参数名保证它先cast self或按传入dtype重建out。

vector_norm functional则按opt_dtype或self dtype申请，out也按此选定类型检查，并将这个dtype显式交SDK。所读局部没有照普通norm写复数转实数输出覆盖；两条路线不能互相补齐类型规则。缺省dim均交空列表，输出shape共用已审[归约shape规则](torch_npu_variance_std_correction_and_cpu_roundtrips.md)，空列表在该helper代表全部轴。

## Foreach范数的版本、p与分配

2.1..2.3入口没有dtype参数，checkData仅准fast p==1或2；2.4及以后入口带opt_dtype，checkDataWithInfinit在缓存的SoC>=Ascend950条件下额外接受正inf，其他SoC仍仅1/2，负inf没有同一例外。scalarProcess只接受isIntegral(false)或浮点Scalar，其他类型在这里报错。

两个入口先check_foreach_api_restrictions，再检查SoC门`(>=Ascend910B1 && <Ascend310B1) || >=Ascend950`，之后兼容/fast检查。不要用其他Foreach算子的`>Ascend310B4`门代替本文件条件。fast还要求can_use_fast_route，且整个列表没有Integral(includeBool=true)或Complex类型。

新入口选dtype后要求promoteTypes(首项dtype,dtype)==dtype。只有不同类型才为每个输入调用_npu_dtype_cast；相同类型直接用原列表。结果始终逐项申请shape{}、所选dtype的Tensor，而不是一个共同输出buffer；调用aclnnForeachNorm时未另传dtype参数。一次最多24项，超限执行完整块和非零余数块，不能沿用ForeachCopy的48或其他inplace块大小。

## 来源与验收

OpPlugin固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。两版上述完整主体代码与非namespace注释一致；Schema普通norm/vector_norm为acl_op/op_api all_version，Foreach两个签名按2.1..2.3与>=2.4划分。产品文档继续见[原生归约范围](torch_npu_native_torch_index_reduce_scope.md)和[线性代数范围](torch_npu_native_linalg_constraints.md)。

定位梯度裁剪或归一化统计时记录具体入口、p原Scalar、dtype/out dtype、列表长度和CANN/SoC门，再检查ACL切换、逐项cast、输出申请及批数；修改p或dtype前验证数值与梯度。仅静态审阅，未运行上游或设备，未知平台保持draft、空平台，无verified。

## npu_renorm_backward 的 host 组合实现

上文 renorm 节记录了 `npu_renorm_backward` 仅主线登记（opapi [v2.7,newest]）；本节补其实现（主线独有文件 `RenormBackwardKernelNpu.cpp`，93 行）。该入口**无 aclnn/ACE 命令，是纯 host ATen 组合**：`reduce_dims` 取除 dim 外全维（maybe_wrap_dim 包装）；`norm = linalg_vector_norm(self, p, reduce_dims, keepdim=true, dtype=acc)`，acc 把 BF16/Half/Float 提升为 Float；`grad_output = (self.conj() * grad)` 在 acc 为实类型时取 `at::real` 后沿 reduce_dims 求和；`norm_backward_impl` 按 p 分支（0→空梯度、1→`sgn*grad`、2→`grad*(self/norm)` 且 norm==0 掩零、inf→`|self|==norm ∨ isnan` 掩码均分、其余→`sgn*|self|^{p-1} * grad / norm^{p-1}` 带 norm==0 掩零）；最终 `grad_norm = maxnorm * (norm+1e-7)^{-1} * (grad - invnorm*nb)`，`where(norm > maxnorm, grad_norm.to(grad.dtype), grad)`。语义要点：截断只在 norm 超过 maxnorm 的维度生效，阈值判据带 +1e-7；输出 dtype 跟随 grad。多次中间归约/逐元素组合的调度代价与 p 分支数值稳定性未测。

## Evidence

- [NormKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NormKernelNpuOpApi.cpp)（primary）：1–160。
- [LinalgNormKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgNormKernelNpuOpApi.cpp)（primary）：1–87。
- [ForeachNormKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ForeachNormKernelOpApi.cpp)（primary）：1–179。
- [OpUtils.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）：186–195、460–466、498–502。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：213–217、3041–3047、3875–3897。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：77–113、127–142。
- [NormKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NormKernelNpuOpApi.cpp)（implementation）：1–172。
- [LinalgNormKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgNormKernelNpuOpApi.cpp)（implementation）：1–87。
- [ForeachNormKernelOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ForeachNormKernelOpApi.cpp)（implementation）：1–171。
- [OpUtils.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）：184–193、416–422、454–458。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：213–217、2942–2948、3767–3789。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：80–110、127–143。


- [RenormBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RenormBackwardKernelNpu.cpp)（implementation）：全文 93 行；发布 yaml/源树零登记（上文 renorm 节负向记录）。
## linalg_vector_norm的acl_op回退内部：FP32中转、两段LpNorm命令与复数硬拒

上文核对的是op_api层的p门控（check_use_aclop）与dtype准备；该包装的回退目标`acl_op::linalg_vector_norm(_out)`（LinalgNormKernelNpu.cpp）本节补齐。主线与发布两版本该文件逐字节相同（diff -u零输出），行号共用。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| functional（141–150）：opt_dim缺省空列表→reduce shape→**opt_dtype有值时先`self.to(opt_dtype)`做ATen级输入cast**→`ApplyTensorWithSizes`按(self_val).options()申请→进nocheck | 输入预处理与op_api路不同：op_api把原始self与dtype实参一起交SDK、host侧不预转（上文已核对），acl_op路先cast——`.to`本身是ATen派发调用，其最终路径未核对 |
| nocheck核心（99–138）：TORCH_CHECK `!self.is_complex()`（原文“linalg_vector_norm does not support complex numbers.”）→非Float输入`_npu_dtype_cast`到Float（FP32中转）→ACE命令"LpNormReduceV2"（attrs p/axes/keepdim/epsilon=0）→ACE命令"LpNormUpdateV2"（attrs p/epsilon=0）→result按FP32 options申请，与目标dtype不同时按`dtype.value_or(self.scalar_type())`cast回→`out = out.copy_(result)` | 复数硬拒仅在acl_op路：op_api包装无该检查，复数self直发aclnnLinalgVectorNorm，行为未核对——不能据回退路拒绝断言op_api路同样拒绝或相反；两段ACE是host命令数，不等于device kernel数；LpNormReduceV2/LpNormUpdateV2内核语义未核对（Update段形状收尾作用不据命名断言）；calculate_p（87–97）把±inf映射为float(INT_MAX/INT_MIN)哨兵，与上文普通norm的calculate_p同模式；host侧可见的计算输入是FP32（内核内部精度未核对），Double/BF16输入在该路不保持原dtype参与计算 |
| out变体（152–162）：CheckOut({self}, result, ACL_FORMAT_ND, **self.scalar_type()**, output_size)后以原始self（无预转）进nocheck | CheckOut声明参照是self dtype而非opt_dtype——与functional的opt_dtype预转、op_api out的opt_dtype参照三处不一致，按原文记录；CheckOut内部未核对；源注释自述“can not support resize shape of out correctly, so the shape of out must be equal to output_size” |
| 文件内matrix_norm遗留（24–85） | create_dim_backshift_permutation/_linalg_matrix_norm_checks/create_reverse_permutation三个static helper无本文件调用者；linalg_matrix_norm主线与发布两版本 yaml零登记——helper存在不构成matrix_norm的NPU能力证据，也不据此断言matrix_norm不可用 |

check_use_aclop为真（较旧CANN且p不在0/1/2/3，±inf在CANN>=8.1.RC1例外）或aclnnLinalgVectorNorm符号缺失时落到本节路径；梯度裁剪等FP32统计场景不受影响，Double精度统计在该路会被降为FP32计算后再cast回，需要原精度时先核对实际派发。

### linalg_vector_norm acl_op 回退补充证据

- [LinalgNormKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LinalgNormKernelNpu.cpp)（primary）：1–163；完整本地小文件。
- [LinalgNormKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LinalgNormKernelNpu.cpp)（implementation）：1–163；与主线逐字节相同（diff -u零输出）。
- [LinalgNormKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgNormKernelNpuOpApi.cpp)（primary）：24–86；check_use_aclop与linalg_vector_norm(_out)段复读（1–87整文件已在上文已读清单）。
- 负向证据：`linalg_matrix_norm`/`_linalg_matrix_norm`在主线与发布两版本 yaml零登记；三 helper在本文件与op_plugin/ops/全树无调用者（rg）。

## 普通 norm 的 acl_op 回退内部：无复数硬拒、FP32 中转与硬 dtype 收口

上文核对的是普通 norm 的 op_api 层（p 门控与 dtype 准备）与 linalg_vector_norm 的 acl_op 回退；`DO_COMPATIBILITY(aclnnNorm, ...)` 的回退终点`acl_op::norm(_out)`（NormKernelNpu.cpp）本节补齐，norm 家族 aclops 实现就此读完。主线与发布两版本 该文件去空白字符流相同（diff -u 仅排版与换行差异；主线 146 行、发布 156 行），行号按主线。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| nocheck 核心（40–79）：**无复数硬拒**（本文件没有 linalg_vector_norm aclops 路的`TORCH_CHECK(!self.is_complex())`）→非 Float 输入`_npu_dtype_cast`到 Float（FP32 中转）→output_size 按**cast 后的 fp32_self**经`reduce_ops_npu_output_size`推导→result_temp 与 result 两份`ApplyTensorWithSizes`按 FP32 options 申请→ACE"LpNormReduceV2"（attrs p/axes/keepdim/epsilon=0）→ACE"LpNormUpdateV2"（attrs p/epsilon=0）→result 与目标 dtype 不同时`_npu_dtype_cast(result, dtype)`→`out = out.copy_(result)` | 复数输入在本路不在此层拒绝：第一个消费者是 FP32 cast，`_npu_dtype_cast` 是否接受复数未核对（torch_npu 仓实现），不能与 linalg 路的硬拒互推，op_api 路复数直发 aclnnNorm 的行为也仍未核对；与 linalg 路的差异按原文记录——那里 reduce shape 按原始 self、目标 dtype 用`dtype.value_or(self.scalar_type())`软收口，这里按 fp32_self、**dtype 是硬参数无 value_or**；两段 ACE 是 host 命令数，不等于 device kernel 数；源注释同款"can not support resize shape of out correctly, so the shape of out must be equal to output_size" |
| calculate_p（25–38）：±inf 映射为 float(INT_MAX/INT_MIN) 哨兵、缺省 2.0 | 与 op_api 层同名函数同模式，但语义位置不同：op_api 路哨兵只用于 p 门控、真正交给 aclnnNorm 的仍是原 p Scalar（上文已核对）；aclops 路的 pvalue 哨兵**就是**实际传入两段 LpNorm 命令的 p attr——±inf 在该路不会以字面 inf 进入 ACE 命令 |
| `norm_out` 无 dtype 重载（82–99）：`CheckOut({self}, result, ACL_FORMAT_ND, self.scalar_type(), output_size)`→check_match 不匹配时 format_contiguous 执行+format_fresh_view 回写，否则原 result 进 nocheck；nocheck 以 **self.scalar_type()** 为目标 dtype | 声明参照=self dtype；与上文普通 norm dtype_out 的 op_api 实参口径（out.scalar_type()）不同路，不互推 |
| `norm_out` 带 dtype 重载（101–120）：同结构，CheckOut 与 nocheck 均以显式 **dtype** 为参照 | 同文件两个 out 重载的声明参照显式不对称（self dtype vs 请求 dtype），按原文记录；CheckOut/check_match 内部未核对 |
| functional `norm(self, p, dim, keepdim, dtype)`（122–132）：按`self.options().dtype(dtype)`申请 out 后进 nocheck；nocheck 在 FP32 temp 中计算、cast 到 dtype 再 copy_ 进 out | **host 侧可见的计算输入恒为 FP32**（内核内部精度未核对）：Double/BF16 在该路不保持原 dtype 参与计算，与 linalg 路同型；与 linalg functional 的`.to(opt_dtype)`前置输入 cast 不同——本 functional 不预转 self，只对结果收口 |
| 三个委托重载（134–144）：`norm(self, p, dtype)`→空 dim 列表；`norm(self, Scalar p)` 与`norm(self, p, dim, keepdim)`→`self.scalar_type()` | 空 dim 列表在 reduce 推发内代表全部轴（上文已核对口径）；两个简签名的目标 dtype 固定为 self dtype，不经过请求 dtype |

触发面：op_api 层 `DO_COMPATIBILITY(aclnnNorm, ...)` 符号缺失时落到本节路径；p 门控（较旧 CANN 且 p 不在 0/1/2/3）只影响 op_api 层的旧 ACL 选择，不构成本文件的独立入口。梯度裁剪等 FP32 统计场景与上文结论一致；需要原精度统计时先核对实际派发落到 aclnnNorm 还是本回退路。

### 普通 norm acl_op 回退补充证据

- [NormKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/NormKernelNpu.cpp)（primary）：1–146；完整本地小文件。
- [NormKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/NormKernelNpu.cpp)（implementation）：1–156；与主线去空白字符流相同（diff -u 仅排版差异）。
- 负向证据：本文件无`is_complex`/`INFINITY`门（对 aclops LinalgNormKernelNpu.cpp 99–138 的对照）；norm 家族 aclops 剩余文件零——主线与发布两版本 `op_plugin/ops/aclops/` 下 Norm* 仅 LinalgNormKernelNpu.cpp 与本文件（全树 rg）。

## renorm/renorm.out/renorm_：maxnorm 子张量重归一的 FP16 中转与命名剥离版本差

本节核对g17账本renorm/renorm.out/renorm_三名（此前仅有[数学范围页](torch_npu_native_tensor_math_scope.md)的支持表行）。主线与发布两版本 yaml三条目逐字相同（主线4254–4264、发布4139–4149）：均`acl_op: all_version`+`op_api: all_version`，无gen_opapi规格、无dimname变体（主线与发布两版本全文rg零命中）。相邻custom名`npu_renorm_backward`仅主线登记（主线5644–5646，`op_api: [v2.7, newest]`，对应主线独有文件opapi/RenormBackwardKernelNpuOpApi.cpp；发布yaml与ops/树零登记），本节不展开其实现。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| op_api renorm_out/renorm（主线RenormKernelNpuOpApi.cpp 23–64、发布23–70，去空白字符流等值）：DO_COMPATIBILITY(aclnnRenorm, acl_op对应实现)后host规范化负dim——dim_post_expr=self.dim()，<=0时取1，dim<0时加dim_post_expr（规范化后的dim传入命令）；out变体`check_tensor({self}, out, out.scalar_type(), input_same_output_size(self))`（dtype参照**out自身**），functional按self options经apply_tensor_without_format申请；单次EXEC_NPU_CMD(aclnnRenorm, self, p, dim, maxnorm, out/result) | 本层无dtype检查（支持面交aclnnRenorm）；p/maxnorm原样Scalar透传、不收窄；check_tensor内部未核对 |
| op_api renorm_（主线66–78、发布74–87）：DO_COMPATIBILITY(**aclnnInplaceRenorm**, acl_op::renorm_)后同一负dim规范化，单次EXEC aclnnInplaceRenorm(self, p, dim, maxnorm) | 原地路使用独立符号aclnnInplaceRenorm——与functional/out的aclnnRenorm是两个ACLNN入口，符号可用性分别核对；无输出申请 |
| acl_op nocheck（主线RenormKernelNpu.cpp 52–91、发布59–106同构）：TORCH_CHECK self dtype∈{Half, Float}（原文"Renorm only support float16 or float32 type."）且result dtype必须等于self（原文"result's type must be equal to input's."）→make_warp_dim归一化dim→renorm_npu_output_size（仅保留dim轴长度、其余轴置1）→result_bak按**Float** options+get_tensor_npu_format(self)申请→Half分支self/result先`_npu_dtype_cast`到Float→ACE命令"Renorm"（attrs p/maxnorm经get_scalar_float_value收窄float、dim）→result_bak经npu_broadcast展开到self.sizes()后at::mul_out与self相乘；Float分支直接Renorm+broadcast+mul_out | ACE"Renorm"输出是缩减形状（dim轴保留、其余为1）的Float中间结果，包装层用broadcast+mul_out组合成最终输出；host命令数≠device kernel数；p/maxnorm收窄float意味着acl_op路对超浮点表示的Scalar有截断（op_api路原样透传，两路不互推）；`_npu_dtype_cast`的注册/实现/跨仓所有权见[dtype转换卡](../../inference/guides/optimization/torch_npu/torch_npu_dtype_cast_backend_allocation_and_aliases.md)补充小节 |
| V2R13命名剥离版本差 | 主线Half分支的rename(c10::nullopt)包在`#if !VERSION_BETWEEN(V2R13, VERSION_NEWEST)`内（主线70–76：>=V2R13不剥离命名直接用self/result，<V2R13剥离）；发布（80–81）无条件剥离。与max/min dim族的NamedTensorCompat.h机制同族（见[旧极值卡](../apis/torch_npu/legacy_min_max_and_sort.md) dim族节），但这里是文件内联#if而非共享头 |
| acl_op入口（主线renorm_out 94–111/renorm 113–117/renorm_ 119–121，发布109–139同构）：renorm_out先CheckOut({self}, result, self)，check_match(&self)不匹配时format_contiguous临时执行+format_fresh_view回写；functional apply_tensor(self)直入nocheck；renorm_是renorm_out(self,...,self)的委托 | CheckOut/check_match内部未核对；renorm_在acl_op路经CheckOut检查self作out的合同 |

renorm在梯度裁剪类训练里与norm/clip组合出现：核对实际派发先分三路——op_api functional/out（aclnnRenorm）、op_api原地（aclnnInplaceRenorm）、acl_op回退（dtype硬门FP16/FP32+Half全程Float中转+Renorm+broadcast+mul_out组合）。混合精度下把FP16 renorm在两路间迁移时，Float中转与命名剥离差异不外推。本节静态口径，未运行任何派发或数值验证。

### renorm补充证据

- [RenormKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RenormKernelNpuOpApi.cpp)（primary）：1–80；完整本地小文件。
- [RenormKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RenormKernelNpuOpApi.cpp)（implementation）：1–89；完整本地小文件，与主线去空白字符流等值（仅排版）。
- [RenormKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RenormKernelNpu.cpp)（primary）：1–122；完整本地小文件。
- [RenormKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RenormKernelNpu.cpp)（implementation）：1–140；完整本地小文件；与主线差异=Half分支rename的V2R13 `#if`保护（主线有、发布无条件）+排版（剔除该#if/#else/#endif段后去空白字符流等值）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：4254–4264、5644–5646；renorm三条目与npu_renorm_backward条目完整字段（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：4139–4149；renorm三条目与主线逐字相同；npu_renorm_backward全文rg零命中（负向）。
- 负向证据：主线与发布两版本 yaml无renorm.dimname/renorm.names变体（rg零命中）；canonical知识树rg renorm仅[数学范围页](torch_npu_native_tensor_math_scope.md)支持表行与npu_moe_gating_top_k*卡的`renorm`形参（不同算子命名空间，不混计）。
