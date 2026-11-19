---
type: Guide
title: all/any布尔归约：Byte直传、兼容回退与不对称整理
description: 区分all/any的aclnn直发与ReduceAll/ReduceAny回退、Byte/Bool输出dtype与空输入分支，并记录两派发路输出dtype可观察差异。
tags:
- task.optimization
- topic.compute.reduction
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AnyKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AllKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AnyKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AnyKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AllKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AnyKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-12T12:10:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# all/any布尔归约：Byte直传、兼容回退与不对称整理

## 固定来源与实际边界

本卡聚合布尔归约all/any的八个Schema条目（全局functional `all(Tensor self)`/`any(Tensor self)`各一 + all.all_out/all.dim/all.out与any同构共六；主线与发布两版本均acl_op+op_api all_version；主线yaml 1046–1060、1116–1130，发布1008–1022、1078–1092，均含各条目末行op_api字段——发布yaml头部的all_version是其枚举的v2.1..v2.12清单，非未来版本承诺）。OpPlugin固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`，全部静态阅读：主线与发布两版本各四个C++文件整文件已读，pin差逐文件核对（见Evidence的review_mode）。未导入上游、执行归约、模型或测试；平台范围未知，保持draft与空平台。归约shape与全轴dim列表推导复用[方差卡](torch_npu_variance_std_correction_and_cpu_roundtrips.md)已核对的reduce_ops_npu_output_size/get_dimlist_for_tensor结论，文档支持表见[原生归约范围](torch_npu_native_torch_index_reduce_scope.md)。CANN内核侧的aclnnAll语义见[all_950](../../../ops/ascendc/operators/aclnn/math/math/all_950.md)（本卡未核对其内核兼容性与语义），图模式all/any的GE lowering行为见[torchair GE归约lowering](../../inference/guides/optimization/torchair/torchair_ge_reduction_lowering.md)；这两卡与本卡分属不同层（CANN内核/图模式 vs op-plugin eager包装双派发路），本卡为op-plugin双派发路（aclnn直发+acl_op回退）层的首个实现卡，不与其重复。

## op_api路：Byte直传、out按自身dtype校验

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| 每个重载先`DO_COMPATIBILITY(aclnnAll/aclnnAny, acl_op::同名)`；functional按`reduce_ops_npu_output_size`推导shape、`apply_tensor_without_format`申请输出后单次`EXEC_NPU_CMD(aclnnAll/aclnnAny,...)` | DO_COMPATIBILITY为函数级static双符号探测（aclnnAll/aclnnAny与其GetWorkspaceSize）：缺失且Aclnn-only模式TORCH_CHECK抛"Current device only support aclnn operators, but ..."，非Aclnn-only则ASCEND_LOGW后整函数return acl_op实现（主线op_api_common.h 94–119、发布96–110，宏体定向读）。单host命令不等于单device kernel |
| functional输出dtype：self为Byte时输出Byte，其余一律Bool（all与any两文件同构） | Byte输入的Byte输出是本地包装的显式选择；与上游torch语义是否一致未运行验证，不写成通用保证，也不外推到其他整数dtype |
| out变体：`check_tensor({self}, out, out, output_size)`——以out自身的dtype与格式为参照校验 | 文件内无显式强制out为Bool/Byte的TORCH_CHECK（check_tensor helper内部未核对，helper可能携带校验）；本地不拒绝不代表任意dtype可执行或执行后不转换，aclnn侧约束路径未核对，不保证host侧无其余校验 |
| 传给aclnn的dims表示不对称：全局all_out传空IntArrayRef，全局any_out与all/any两个functional全局变体传get_dimlist全轴列表；dim变体均传单元素列表 | 空列表与全轴列表两种表示是否等价由SDK决定，未运行验证；知识库方差卡语义中空列表对应标量 shape 推导 |

## acl_op路：ReduceAll/ReduceAny与不对称的dtype整理

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| all：输入非Bool先`custom_ops::_npu_dtype_cast(self,Bool)`（torch_npu 侧实现，来源未核对）；核心OpCommand "ReduceAll"，dim_list以`at::kLong`张量作为第二个Input传入，keep_dims属性透传 | 输入cast是host侧请求，_npu_dtype_cast拷贝/格式行为未核对；ACE命令"ReduceAll"内核语义未核对 |
| all的out：TORCH_CHECK out∈{Bool,Byte}（原文"all only supports bool tensor for out, got: <实际dtype>"）；CheckOut后out非Bool先cast到Bool临时对象执行、再cast回原dtype并`copy_` | Byte out是显式登记例外；非Bool/Byte out直接抛错。cast往返与copy_为host侧多段请求，不作device kernel计数 |
| all的functional空输入分支：numel==0时按`op_infer::infersize_all(self,dim)`（全局变体为{}标量）申请Bool结果并`fill_(1)`——空集全真走本地填充，不下发ReduceAll | infersize_all内部未核对；fill_是aten分派调用，不是免设备成本；该分支对dim与全局两个变体都存在 |
| any：核心OpCommand "ReduceAny"，dim_list直接作为构造参数透传（无at::kLong张量包装）；`dim==LLONG_MIN`哨兵解释为全轴get_dimlist，否则单元素；0-dim输入先unsqueeze(0)+cast Bool再按dim=0归约（全局functional与全局out两处，主线aclops 64–70、113–119） | LLONG_MIN作为"未指定dim"哨兵是包装约定，其调用方约定未核对；0-dim分支对Bool输入cast直传，对非Bool输入先cast Bool |
| any的空输入分支：仅全局any_out有numel==0分支，直接`result.fill_(false)`后返回；any functional（dim与全局）无空输入专用分支，仍按reduce shape推导下发ReduceAny | 空集any为假只在out变体本地实现；functional空输入走SDK命令，其空张量行为未核对；与all的空输入分支不对称，按原文记录不解释 |
| any的输出dtype：dim变体functional按`self.options()`（apply_tensor_with_format取self格式）申请、全局functional非0-dim直发分支按`apply_tensor(self, output_size)`——dtype跟随self而非固定Bool；**例外**：全局functional的0-dim输入先cast Bool再转调dim=0变体，输出为Bool而非原self dtype；0-dim全局out的CheckOut第三实参同样取cast后的Bool self_tmp而非原self。any_out（非0-dim）的CheckOut第三实参为self，all_out的为out自身 | 同一any调用在op_api路（Bool/Byte）与acl_op路（self dtype）输出dtype可观察不同——该对比限于非0-dim输入：0-dim全局变体在acl_op路也先转Bool，两路差异不适用于该分支。CheckOut第三实参差异按原文记录，其内部语义未核对。是否实际到达acl_op路取决于DO_COMPATIBILITY与派发模式 |

## 优化与验收边界

掩码校验、梯度门控里的all/any高频出现：先核对实际派发模式（aclnn符号可用性、Aclnn-only开关）与输入dtype（尤其Byte与非Bool），再分别验证输出dtype预期——两派发路输出dtype不一致是本卡最需复验的点（0-dim全局any在acl_op路也先cast Bool，该例外分支不构成两路差异）。空输入语义不对称（all本地fill 1、any仅out变体fill false、any functional下发ReduceAny），迁移或改写out/functional写法前逐变体核对。host侧cast/fill/copy_整理计入端到端测量；本卡无数值、性能或verified结论，不把任一路径写成推荐配置。

## Evidence

- [AllKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllKernelNpuOpApi.cpp)（primary）：1–99；完整本地小文件。
- [AnyKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AnyKernelNpuOpApi.cpp)（primary）：1–94；完整本地小文件。
- [AllKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AllKernelNpu.cpp)（implementation）：1–154；完整本地小文件。
- [AnyKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AnyKernelNpu.cpp)（implementation）：1–128；完整本地小文件。
- [AllKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllKernelNpuOpApi.cpp)（implementation）：1–91；完整本地小文件；与主线差异仅排版与文件尾`// namespace op_api`注释（去空白字符流除注释外等价，整文件diff -u核对）。
- [AnyKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AnyKernelNpuOpApi.cpp)（implementation）：1–83；同上口径。
- [AllKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AllKernelNpu.cpp)（implementation）：1–153；完整本地小文件，与主线去空白字符流相同（仅排版）。
- [AnyKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AnyKernelNpu.cpp)（implementation）：1–133；同上口径。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：60–160；DO_COMPATIBILITY/DO_COMPATIBILITY_COMMON宏定义与GetOpApiFuncAddr工具定向读。
- [op_api_common.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：90–118；DO_COMPATIBILITY宏定义定向读。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1046–1060、1116–1130；all/any八字条（各含全局functional条目与末行op_api字段）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1008–1022、1078–1092；同口径，与主线逐字相同。
