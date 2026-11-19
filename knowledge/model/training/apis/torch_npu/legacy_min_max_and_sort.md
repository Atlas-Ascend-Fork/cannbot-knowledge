---
type: API
title: 旧极值与排序：INT32索引、返回元组及轴差异
description: 区分npu_max/min的双输出和sort_v2仅值输出，保留命名维版本限制。并含 torch.max/min pairwise out= 的发布独有注册边界。并含 amax/amin 的 gen_opapi 登记与 acl_op ReduceMax/ReduceMin 回退。并含 torch.max/min dim 族的 Long 索引、ArgMax/ArgMinWithValue 回退与 Dimname 编译边界。并含 argmax.out/argmin/argmin.out 三名：无 dim 展平、keepdim 不对称与 ArgMaxV2/ArgMin 命令差异。并含 max 系 sparse 标记消费路径：SparsePrivateUse1 生成链与 to_dense 后重分发。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_max.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_max.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_max.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_min.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_sort_v2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SortWithoutIndicesKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SortWithoutIndicesKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaxV1KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaxV1KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MinV1KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MinV1KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MinKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MinKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MinKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MinKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/model.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/NamedTensorCompat.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ArgmaxKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ArgminKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ArgmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ArgminKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ArgmaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ArgminKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ArgmaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ArgminKernelNpu.cpp
  role: implementation

- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/sparse/SparseMaxKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/sparse/SparseMaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/gen_backend_stubs.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torchnpugen/gen_backend_stubs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/gen.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/gen_op_plugin_functions.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/gen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/gen_op_plugin_functions.py
  role: implementation

created_at: '2026-11-09T20:27:55Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# 旧极值与排序：INT32索引、返回元组及轴差异

## 固定版本及消费边界

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda实际收录的中英文页。发布对应ascend_26_0_pt28；TorchNPU实现发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b、独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf分别消费，不将两个main当配套发行。

默认平台A2/A3仅指各页所列范围；主线新增产品或参数另明确版本，旧Atlas不自动映射新型号。beta及计划废弃是上游接口状态，知识卡stable不表示推荐新模型使用或运行verified。本卡未做上游导入、模型加载、设备执行、反向或性能实验；注册all_version不是全硬件保证，底层Kernel实现不在本卡结论范围。


## npu_max和npu_min

沿dim规约，keepdim决定是否保留长度1轴，返回(values,indices)。两版实际索引分配为INT32，不从torch.max/min惯例推为INT64；值dtype跟随输入。反向通过零Tensor和scatter恢复，max另有Long索引转INT32路径，min不能由此自动继承任意Long输入容忍。

min发布页计划废弃、建议torch.min；max页没有同样废弃声明，不把两者生命周期合并。主线命名维重载只注册于2.13以前的PyTorch范围并有对应编译保护，普通整数dim不因此消失；接口在某份文档存在不证明当前任意编译版本都含Dimname重载。

## npu_sort_v2

计划用torch.sort替换，但只返回排序后的values，不返回indices。旧文档只称最后一轴，实际包装对其他轴用前后两次transpose恢复；这只说明包装路径存在，不是所有轴/布局组合的运行保证。

descending控制方向。旧样例FP32外观数值出现FP16样精度，包装没有据此强制转FP16的逻辑，不能将样例抄成精度规则。替换torch.sort后显式取values并核对axis、稳定性需求、dtype和反向，而不是把二元组直接当原返回。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_max.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_max.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_max.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_min.md)（primary）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_sort_v2.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SortWithoutIndicesKernelNpu.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SortWithoutIndicesKernelNpu.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaxV1KernelNpu.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaxV1KernelNpu.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MinV1KernelNpu.cpp)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MinV1KernelNpu.cpp)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [MaxKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaxKernelNpuOpApi.cpp)（implementation）：1–109；完整本地小文件。
- [MaxKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaxKernelNpuOpApi.cpp)（implementation）：1–139；完整本地小文件。
- [MinKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MinKernelNpuOpApi.cpp)（implementation）：1–119；完整本地小文件。
- [MinKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MinKernelNpuOpApi.cpp)（implementation）：1–127；完整本地小文件。
- [MaxKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaxKernelNpu.cpp)（implementation）：36–62,125–157；pairwise nocheck helper与pairwise max_out入口，其余行段未核对。
- [MaxKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaxKernelNpu.cpp)（implementation）：29–64,137–166；同上口径。
- [MinKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MinKernelNpu.cpp)（implementation）：45–58,158–192；pairwise nocheck helper与pairwise min_out入口，其余行段未核对。
- [MinKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MinKernelNpu.cpp)（implementation）：46–51,125–155；同上口径。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3292–3296,3313–3317,3380–3388,3439–3442,3459–3462；max/min与maximum/minimum家族所选条目，其余注册行未核对。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3398–3402,3481–3490,3541–3548,3561–3569；主线家族所选条目（主线全文无max.out/min.out），其余注册行未核对。

## torch.max/min的pairwise out=注册边界

上文“建议torch.min”的替换建议多一层注册边界：对照同一固定主线与发布，发布的OpPlugin YAML登记`max.out`/`min.out`（pairwise带out的schema）而主线同名yaml不登记（该yaml全文diff核实、rg零命中）；该缺席限定在已扫描的这份OpPlugin YAML，未核对的生成/跨仓注册面不外推为主线NPU整体无覆盖。非out的pairwise `torch.max(a,b)`/`torch.min(a,b)`在该两份yaml均无独立登记，`maximum`/`minimum`则主线与发布两版本的yaml都有登记；ATen把pairwise max/min实际路由到何处未核对，不在此断言由`maximum`/`minimum`承担。本节静态阅读，未运行任何分发、导入或数值验证。

| 实际门槛→动作 | 结果与边界 |
| --- | --- |
| 发布注册面 | `max.out(Tensor self, Tensor other, *, Tensor(a!) out)`（3313–3317行，`sparse: [v2.1, newest]`+`acl_op: all_version`+`op_api: all_version`）；`min.out`（3459–3462行，`acl_op`+`op_api`，无sparse标记）。sparse标记只按登记原文记录，其消费语义未核对。主线版本的这份OpPlugin YAML不登记这两个schema（全文rg零命中；主线两份opapi整文件读亦无pairwise重载），未核对的生成/跨仓注册面不外推，ATen侧默认分发路径未核对、不在此断言其行为。 |
| 发布op_api包装`max_out(self, other, result)`（MaxKernelNpuOpApi.cpp 86–93行） | `DO_COMPATIBILITY(aclnnMaximum, acl_op::max_out(...))`后，按broadcast尺寸推导，`check_tensor({self, other}, result, result.scalar_type(), output_size)`，单次`EXEC_NPU_CMD(aclnnMaximum, self, other, result)`。同文件`maximum_out`（22–34行）有IsCPUScalar(other)标量拷贝分支，本包装没有——pairwise max.out的CPU标量other不在此层拷贝，与maximum.out路径形成可观察差异。 |
| 发布op_api包装`min_out(self, other, result)`（MinKernelNpuOpApi.cpp 90–100行） | 入口先TORCH_CHECK梯度守卫：out=参数与requires_grad/GradMode开启组合即报错，报错原文写“minimum(): functions with out=... arguments don`t support automatic differentiation, but one of the arguments requires grad.”（挂在min_out上的原文措辞，按原文记录不修正）。随后`DO_COMPATIBILITY(aclnnMinimum, acl_op::min_out(...))`、broadcast尺寸、`check_tensor({self, other}, result, result.scalar_type(), output_size)`、单次`EXEC_NPU_CMD(aclnnMinimum, self, other, result)`。同样没有`minimum_out`（33–49行）的other优先else-if标量拷贝。 |
| acl_op旧路径主线与发布两版本都在 | 发布/主线aclops均有同名pairwise入口（发布Max 133–157、主线Max 145–166；发布Min 165–183、主线Min 133–146，行段已读，主体结构一致仅排版差异）：max侧先按result_type升位dtype_cast、CheckOut、check_match不匹配时临时连续回写，底层ACE“Maximum”命令；min侧CheckOut以self.sizes()为参照，本地入口未显式dtype_cast、未计算result_type升位，底层ACE“Minimum”命令——CheckOut内部未核对，本地无显式升位不等于下游无promotion。就已核对的OpPlugin YAML而言主线不登记该schema，这两份aclops函数不由该schema登记到达；未核对的生成/跨仓注册核对不外推为绝对不可达。 |
| 同文件相邻版本差异 | 主线Max/Min opapi（139/127行整文件已读）无pairwise重载，其maximum/maximum_out对self、other各独立判断IsCPUScalar并带`is_ascend950_path()+prepare_binary_tensors`分支（minimum族为other优先else-if）；发布maximum只拷贝other。主线`max(self)`/`min(self)`另有numel>0 TORCH_CHECK、dim族zero_numel_check_dims，发布文件没有这些检查；主线Dimname族置于`!VERSION_BETWEEN(V2R13, VERSION_NEWEST)`编译条件。这些只属同名文件版本差，不构成发布整体更宽松或更严格的结论。 |

替换npu_min为torch.min、或迁移max/min输出式写法时按pin分别核对：发布登记面下`torch.min(a,b,out=)`有NPU包装且min_out入口自带梯度守卫；就已扫描的OpPlugin YAML而言主线下该schema无登记（未核对的生成/跨仓注册面不外推），ATen默认分发路径未核对、行为不在此断言，不把发布登记外推到主线。check_tensor/CheckOut/check_match/format_fresh_view等工具内部未展开；静态口径，无数值或分发验证。


## amax/amin：gen_opapi登记与acl_op的ReduceMax/ReduceMin回退

极值家族补上规约入口`amax`/`amin`（含`.out`）的实现层路由。主线与发布两版本的yaml登记逐字相同（主线1062–1094、发布1024–1056，四条目各含`acl_op: all_version`+`op_api: all_version`+gen_opapi完整规格）：functional的`out`为size=`reduce_ops_npu_output_size(self, dim, keepdim)`、dtype=`self`，`.out`条目只有size（dtype缺省），exec为`aclnnAmax`/`aclnnAmin`。aclnnAmax/aclnnAmin符号在主线与发布两版本全树rg仅命中该yaml的gen_opapi exec登记，无手写op_api包装文件；生成体由gencode产出且不随仓提交——本节重读主线与发布两版本生成器模板段静态推导，未运行gencode。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| 生成op_api functional（模板推导）：`DO_COMPATIBILITY(aclnnAmax/aclnnAmin, acl_op::amax/amin(self, dim, keepdim))`后按reduce size与`self.scalar_type()`经`apply_tensor_without_format`申请result，单次`EXEC_NPU_CMD(aclnnAmax/aclnnAmin, self, dim, keepdim, result)` | DO_COMPATIBILITY仅在登记acl_op时生成（门控`if struct.acl_op`，主线与发布两版本同）；宏为static双符号探测，符号缺失且Aclnn-only模式TORCH_CHECK抛错、否则ASCEND_LOGW后return acl_op实现（主线op_api_common.h 94–119、发布96–110定向读）。Schema默认`dim=[]`直传推导函数，空列表语义不在本节单独核对 |
| 生成op_api `.out`（模板推导）：`check_tensor({self}, out, out.scalar_type(), output_size)`后单次`EXEC_NPU_CMD(..., out)` | `.out`无dtype规格时ResInfo缺省解析为out自身（`out.scalar_type()`），与acl_op路CheckOut以self为参照形成声明参照差异；check_tensor内部语义未核对，不写成强制约束，也不断言host层无其余检查 |
| acl_op amax/amin functional（主线Max 204–213、Min 198–204；发布Max 195–205、Min 232–239，对应段与主线去空白字符流相同）：reduce shape推导后`apply_tensor_with_format`申请，ACE命令"ReduceMax"/"ReduceMin"（dims作第二个Input、keep_dims属性透传） | 输出格式跟随self的NPU格式；归约到标量输出（`output_size.empty()`即shape列表为空，0维标量结果而非numel==0）时amax改用ACL_FORMAT_ND、amin改用ACL_FORMAT_NCHW——标量输出的格式不对称按原文记录。"ReduceMax"/"ReduceMin"为host侧ACE命令名，不据此计device kernel |
| acl_op amax_out/amin_out（主线Max 220–233、Min 211–223；发布Max 213–227、Min 247–269等值）：`CheckOut({self}, out, ACL_FORMAT_ND, self.scalar_type(), output_size)`，check_match不匹配时format_contiguous临时执行+format_fresh_view回写 | CheckOut以`self.scalar_type()`为参照dtype；CheckOut/check_match内部未核对。两文件其余差异行段（dim族zero_numel_check_dims、Dimname族V2R13保护、include替换）不属本节范围、未核对 |
| acl_op全局`max(self)`/`min(self)`（主线Max 215–218、Min 206–209；发布207–211、241–245）：`get_dimlist_for_tensor(self)`全轴后委托`acl_op::amax/amin(self, dims, false)` | acl_op路的全局极值复用规约入口——本节所读仅证明这一层委托关系；全局max/min的op_api生成路未在本节展开（上文pairwise小节只覆盖发布pairwise `max.out`/`min.out`（a,b,out）注册面，不覆盖全局变体），不能据此称全局max/min已有生成路或两路等价，两路不互推 |

aclnnAmax/aclnnAmin内核语义与dtype支持范围在CANN侧未核对；生成推导未经gencode运行认证；check_tensor/CheckOut/check_match/get_tensor_npu_format内部未核对（torch_npu侧）；`reduce_ops_npu_output_size`定义于同一OpPlugin仓的op_plugin/utils/KernelNpuOutputSize.cpp:127，其推导规则已由[方差卡](../../guides/torch_npu_variance_std_correction_and_cpu_roundtrips.md)核对、本卡不重复展开。本节静态口径，无运行验证。

### amax/amin 补充证据

- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1062–1094；amax/amax.out/amin/amin.out四条目完整字段（各含acl_op/op_api/gen_opapi至末行exec），其余注册行未核对。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1024–1056；同口径，与主线逐字相同。
- [MaxKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaxKernelNpu.cpp)（implementation）：52–56、204–233；ReduceMax nocheck helper与amax/max(self)/amax_out整段（其余行段见本卡前节已读范围，不重复计）。
- [MinKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MinKernelNpu.cpp)（implementation）：52–56、198–223；ReduceMin nocheck helper与amin/min(self)/amin_out整段。
- [MaxKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaxKernelNpu.cpp)（implementation）：48–53、195–227；发布对应段，与主线同名段去空白字符流相同（整段diff -u+去空白字符流核对）。
- [MinKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MinKernelNpu.cpp)（implementation）：59–73、232–269；同口径。
- [struct_codegen.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py)（implementation）：33–100、132–157、178–186、295–476；模板、filt_gen_opapi、gen_size_dtype_map、compute_op_api_definition组装段。
- [struct_codegen.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py)（implementation）：33–100、176–200；发布模板与DO_COMPATIBILITY门控段（`if struct.acl_op else ""`）。
- [model.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py)（implementation）：30–37、59–105、150–272；filt_input_tensor、ResInfo缺省解析、cmd_args展开。
- [model.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/model.py)（implementation）：60–96、190–249；同口径。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119；DO_COMPATIBILITY宏定义定向读。
- [op_api_common.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–110；同口径，语义相同仅排版差异。

## torch.max/min dim 族：Long索引合同、ArgMax/ArgMinWithValue回退与Dimname编译边界

上文pairwise与amax/amin小节核对了二元与规约入口，本节补齐极值家族最后一组Schema：`max.dim`/`max.dim_max`/`max.names_dim`/`max.names_dim_max`及min镜像共10名（g16账本mapped_support_only）。int dim族主线与发布两版本均`acl_op+op_api all_version`；names_dim族主线登记`[v2.1,v2.12]`、发布`all_version`（=发布yaml头部枚举的v2.1..v2.12清单，非未来版本承诺）——上文npu_max页“主线命名维重载只注册于2.13以前”的口径在torch入口复现。主线opapi/aclops的Dimname重载都包在`!VERSION_BETWEEN(V2R13, VERSION_NEWEST)`编译保护内，发布无保护；机制锚点是主线专有头op_plugin/utils/NamedTensorCompat.h（1–105整读）：PyTorch 2.13移除named tensor后，<v2.13转发ATen/NamedTensorUtils.h，>=v2.13提供no-op的namedinference stubs让残留引用继续编译，Dimname重载本体在v2.13+被gated out；发布树无此头、直接include ATen头。dimname_to_position为op-plugin侧helper、zero_numel_check_dims为ATen侧helper（主线opapi经ATen/native/ReduceOpsUtils.h引入、主线aclops同include），两者内部未核对。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| op_api dim包装（主线Max 93–119/Min 82–108；发布Max 62–84/Min 62–88）：先`zero_numel_check_dims(self,dim,"max()"/"min()")`（仅主线）→`DO_COMPATIBILITY(aclnnMaxDim/aclnnMinDim, acl_op::max/min(_out)(...))`→reduce shape推导→out变体`check_tensor({self},output,self.scalar_type(),output_size)`+`check_tensor({self},indices,at::ScalarType::Long,output_size)`；functional按self options申请values、Long申请indices，单次EXEC | 发布opapi同族无zero_numel检查（同文件全局`max(self)`/`min(self)`的numel>0 TORCH_CHECK同样仅主线，见上文版本差行）；zero_numel_check_dims的ATen内部语义未核对，只记录包装层的调用存在性；check_tensor内部未核对，不写成强制约束；aclnnMaxDim/aclnnMinDim内核侧未核对 |
| acl_op dim functional（主线Max 115–137/Min 96–116；发布同构仅去zero_numel）：zero_numel→输入提升（max：Bool或Int都`_npu_dtype_cast`到Float；min：仅Bool）→`apply_tensor_with_format(...,ACL_FORMAT_ND)`申请values、**Int**申请indices（max用ND、min用NCHW，格式不对称按原文记录）→ACE命令"ArgMaxWithValue"/"ArgMinWithValue"→indices cast回Long→提升过的values cast回原dtype | ACE命令以`.Output(indices).Output(output)`先索引后值；host命令数≠device kernel数；`_npu_dtype_cast`实现在torch_npu仓（torch_npu 仓实现，本卡来源未核对，相关卡同口径）；Bool/Int提升面不对称，不互推 |
| acl_op dim out（主线Max 65–102/Min 59–94；发布同构）：zero_numel→`CheckOut({self},values,self.scalar_type(),ND)`+`CheckOut({self},indices,at::ScalarType::Long,ND)`→indices先Long→Int供内核→check_match不匹配走format_contiguous执行+format_fresh_view回写→Int结果cast回Long后`copy_`写回调用方indices张量 | max_out对**cast后的Int张量**做check_match（主线Max 80–81）、min_out对**原始Long张量**做（主线Min 74–75）——同族参照不对称按原文记录；CheckOut/check_match内部未核对 |
| Dimname路由（主线与发布两版本同构）：opapi Dimname两个重载先DO_COMPATIBILITY再`dimname_to_position`转int后委托同文件int重载（int重载自带zero_numel与第二次DO_COMPATIBILITY）；aclops Dimname out委托acl_op int重载；aclops max Dimname functional调`at::max`重入ATen分发器（主线141、发布130），min镜像调`acl_op::min`直连（主线129、发布162） | `at::max`重分发后落到哪个后端kernel由分发键决定，未核对；不能据Dimname入口名断言最终执行路径 |
| 注册差 | int dim族条目（max.dim/dim_max、min.dim/dim_min）主线与发布两版本逐字相同；names_dim族版本字段不同（主线`[v2.1,v2.12]`+编译保护 vs 发布`all_version`无保护），其余字段一致 |

从npu_max/npu_min迁移到torch.max(dim)/min(dim)时按三路区分索引dtype合同：legacy接口直接返回INT32索引（卡首节）；torch dim族的acl_op路host侧以INT32参与ACE命令后cast回Long、op_api路声明与申请全程Long——三路可观察面不同，不能按其一推断其余，迁移脚本应显式核对indices dtype与既有INT32消费者的兼容性。

### torch.max/min dim 族补充证据

- [MaxKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaxKernelNpuOpApi.cpp)（implementation）：80–137；全局max(self)与dim/Dimname族整段。
- [MaxKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaxKernelNpuOpApi.cpp)（implementation）：52–107；发布全局与dim/Dimname族整段。
- [MinKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MinKernelNpuOpApi.cpp)（implementation）：69–125；全局min(self)与dim/Dimname族整段（文件其余行段见上文已读清单，本卡未重读全文头部）。
- [MinKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MinKernelNpuOpApi.cpp)（implementation）：52–117；同上口径。
- [MaxKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaxKernelNpu.cpp)（implementation）：1–143；include段与ArgMaxWithValue nocheck/dim族/Dimname族整段（52–56、204–233已在上文已读清单）。
- [MaxKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaxKernelNpu.cpp)（implementation）：16–28、63–131；发布include段与dim族/Dimname族整段（48–53、195–227已在上文已读清单）。
- [MinKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MinKernelNpu.cpp)（implementation）：1–129；include段与ArgMinWithValue nocheck/dim族/Dimname族整段（52–56、198–223已在上文已读清单）。
- [MinKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MinKernelNpu.cpp)（implementation）：16–28、76–163；发布dim族/Dimname族整段（59–73、232–269已在上文已读清单）。
- [NamedTensorCompat.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/NamedTensorCompat.h)（implementation）：1–105；完整本地小文件，主线专有（发布树无此文件，负向核实）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3398–3419、3541–3557；max/min全局与dim/dim_max/names_dim/names_dim_max族条目完整字段（含各末行版本标记）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3292–3312、3439–3455；同口径（int dim族与主线逐字相同；names_dim族`all_version`与主线`[v2.1,v2.12]`不同，按原文记录）。

## argmax.out/argmin/argmin.out：无 dim 展平、keepdim 不对称与 ArgMaxV2/ArgMin 命令

上文 max/min dim 族补齐的是双输出族；本节核对极值家族最后三个 g16 登记名：`argmax.out`、`argmin`、`argmin.out`。主线与发布两版本 yaml 三条目逐字相同（主线 1152–1162、发布 1114–1124，均`acl_op: all_version`+`op_api: all_version`、无 dimname 变体、无 gen_opapi）。**负向（主线与发布两版本 yaml 全文 rg 零命中）：`argmax` functional（不带 out 的 `argmax(Tensor self, int? dim=None, bool keepdim=False)`）在主线与发布两版本 均无登记**——torch.argmax 无 out 调用的框架侧路由不在来源源码集内，不外推为不可用或可用。四个手写文件主线与发布两版本 逻辑结构一致（排版与匿名 namespace 尾注释差异；去空白字符流在去除尾注释后相同）；主线行号引用如下。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| op_api `argmax_out`（主线 49–75）：dim 有值时`maybe_wrap_dim`；0 维 self 限定 dim==0 或 -1（TORCH_CHECK_INDEX 原文"argmax(): Expected reduction dim -1 or 0 for scalar but got "），否则`self.size(dim_) != 0`；无 dim 时`self.numel() != 0`（原文"argmax(): Expected reduction dim to be specified for input.numel() == 0."）→`DO_COMPATIBILITY(aclnnArgMax, acl_op::argmax_out(...))`→`argmax_exec` | dim 合法性检查全部在 DO_COMPATIBILITY 之前——缺符号回退 acl_op 路时这些检查已经跑过；maybe_wrap_dim/TORCH_CHECK_INDEX 内部未核对 |
| op_api `argmax_exec`（主线 23–47）：无 dim 时`self.reshape({-1})`展平、realDim=0，**realKeepDim 保留调用方 keepdim**；有 dim 时原 self + dim.value()；`reduce_ops_npu_output_size`→out 模式`check_tensor({self}, result, result, output_size)`、functional 模式`apply_tensor_without_format(output_size, self.options().dtype(at::kLong))`→单次`EXEC_NPU_CMD(aclnnArgMax, input, realDim, realKeepDim, result)` | **out 模式的 dtype 参照是 result 自身**——本层不强制 Long 声明，传入非 Long out 的检查深度取决于 check_tensor 内部（未核对）；functional 恒按 Long 申请 |
| op_api `argmin`（主线 60–68）与`argmin_out`（70–78）：`DO_COMPATIBILITY(aclnnArgMin, acl_op::argmin/argmin_out(...))`→`argmin_exec` | argmin 的入口处没有 argmax 那组 dim 包装检查；检查收敛到 exec 内部（下一行） |
| op_api `argmin_exec`（主线 23–58）：`TORCH_CHECK(!(self.numel() == 0 && !(dim.has_value())))`（原文"Expected reduction dim to be specified for input.numl()==0"，**numl 拼写按原文记录**，ErrCode::PARAM）→无 dim 展平、real_dim=0、**real_keep_dim 恒 false**（仅 dim 有值时取 keepdim）→同 argmax 的 check_tensor/Long 申请→单次 EXEC aclnnArgMin | **无 dim 时 keepdim 丢弃**：与 argmax_exec 保留 keepdim 显式不对称——全局 argmax(keepdim=True) 与全局 argmin(keepdim=True) 在 op_api 路的输出形状约定不同（reduce 推导规则见方差卡，空列表/0 维合同不在此重开）；单 host 命令≠单 device kernel |
| acl_op `argmax_out`（主线 42–70）：**无 numel/dim 检查**；无 dim 展平、keepdim 强制 false；`CheckOut({self}, out, get_tensor_npu_format(out), at::kLong, output_size)`（**Long 硬声明**）→`_npu_dtype_cast(out, at::kInt)`→ACE **"ArgMaxV2"**（dim 以 at::kInt 第二输入，`MEMORY_HOST_COMPILE_DEPENDENT`编译标记；keep_dims attr）→结果 cast 回 Long；`check_match(&out)`不匹配时 format_fresh_view 回写、否则直接`out =` 赋值 | **acl_op 路无 dim 检查**与 op_api 入口前置检查形成分层差异——经 DO_COMPATIBILITY 落入时检查已在 op_api 跑过、直连 acl_op 时无此层；keepdim 无 dim 时强制 false（两侧一致，与 op_api argmax 的保留不同）；"ArgMaxV2"命令名与 argmin 的"ArgMin"不对称按原文记录 |
| acl_op `argmin`（主线 39–60）与`argmin_out`（62–91）：`TORCH_CHECK(self.numel() > 0)`（原文"cannot perform reduction function argmin on a tensor with no elements because the operation does not have an identity"，ErrCode::PARAM）→无 dim 展平、keepdim 强制 false→functional`apply_tensor_with_format(output_size, self.options().dtype(at::kInt), ACL_FORMAT_ND)`、out 变体`CheckOut(..., at::kLong, ...)`后`_npu_dtype_cast(result, at::kInt)`→ACE **"ArgMin"**（dim 第二输入 at::kInt、无 compile-dependent 标记）→cast 回 Long | argmin 的 numel>0 检查在 acl_op 也有、argmax 没有——同族镜像不对称按原文记录；**argmin_out 无 check_match 分支**（直接`result =` 赋值），argmax_out 有分支——回写路径不对称；"ArgMin"非"ArgMinV2" |
| 索引 dtype 合同 | 三路并存：op_api 全 Long（functional 申请/out 声明参照自身）；acl_op 以 Int 参与 ACE 后 cast 回 Long（与上文 dim 族 ArgMaxWithValue 的 Int→Long 同型）；legacy npu_max/min 直接 INT32（卡首节）。互相不推导，迁移脚本显式核对 |

从 npu_max 迁移到 torch.argmax/argmin 时按三路核对：indices dtype（INT32/Long/Int-计算-Long-返回）、全局调用（无 dim）在 op_api 路的 keepdim 语义（argmax 保留、argmin 丢弃）、空张量输入的拒绝文本（argmax_out 与 acl_op argmin 都有、acl_op argmax_out 无）。Dimname 变体两名均无注册（argsort.dimname 是 argsort 家族的，不外推）。

### argmax/argmin 补充证据

- [ArgmaxKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ArgmaxKernelNpuOpApi.cpp)（primary）：1–76；完整本地小文件（argmax_out + argmax_exec）。
- [ArgminKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ArgminKernelNpuOpApi.cpp)（primary）：1–79；完整本地小文件（argmin + argmin_out + argmin_exec）。
- [ArgmaxKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ArgmaxKernelNpu.cpp)（implementation）：1–72；完整本地小文件（argmax_out + ArgMaxV2 nocheck）。
- [ArgminKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ArgminKernelNpu.cpp)（implementation）：1–92；完整本地小文件（argmin + argmin_out + ArgMin nocheck）。
- [ArgmaxKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ArgmaxKernelNpuOpApi.cpp)（implementation）：1–59；完整本地小文件，与主线逻辑结构一致（排版+匿名 namespace 尾注释差异）。
- [ArgminKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ArgminKernelNpuOpApi.cpp)（implementation）：1–67；同口径。
- [ArgmaxKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ArgmaxKernelNpu.cpp)（implementation）：1–62；同口径。
- [ArgminKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ArgminKernelNpu.cpp)（implementation）：1–94；与主线去空白字符流相同。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1152–1162；argmax.out/argmin/argmin.out 三条目完整字段（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1114–1124；同三条目，与主线逐字相同。
- 负向证据：`func: argmax(`在主线与发布两版本 yaml 全文 rg 零命中（functional 未登记）；argmax/argmin 无 dimname 条目（`argmax.dimname`/`argmin.dimname`/`.names_dim` rg 零命中）。

## max系sparse标记的消费路径：SparsePrivateUse1生成链与to_dense后重分发

上文pairwise节把发布`max.out`登记里的`sparse: [v2.1, newest]`标记记为“消费语义未核对”；本节覆盖该未确认项。先锚定登记全貌（主线与发布两版本 yaml全文`sparse:`行前四行rg）：主线带sparse标记的仅四名——`add.out`（927–931）、`_coalesce`（1613）、`max(Tensor self)`（3398–3401）、`mul.out`（3645–3648）；发布为`add.out`（899–902）、`_coalesce`（1554）、`max(Tensor self)`（3292–3295）、`max.out`（3313–3317）。`max(Tensor self)`主线与发布两版本均`sparse: [v2.1, newest]`+`acl_op: all_version`+`op_api: all_version`；`max.out`的sparse标记仅发布有（主线全文无max.out登记，上文pairwise节已定案，不重复）。**min系零sparse标记**：`min(Tensor self)`/`min.out`主线与发布两版本均无（负向rg定案）。add.out/mul.out/_coalesce的消费路径属g18 elementwise与sparse主题域（add.out/mul.out已由sparse范围账本核对、_coalesce已由既有卡核对），本节不展开。

| 环节 | 实际门槛→动作 | 失败/边界 |
| --- | --- | --- |
| 生成链三段 | op-plugin `torchnpugen/gen_op_plugin_functions.py`把`sparse`字段读入后并入导出项（`new_item['sparse'] = 'op_api'`，主线:46、67–68；发布:45、62–63）；op-plugin `torchnpugen/gen.py`为带标记Schema生成`<op>_sparse`后缀包装——声明处`op_name += "_sparse"`（主线:247–249）、定义处包装体调用`sparse::{impl_name}_sparse({args})`（主线:404–408）；pytorch fork `torchnpugen/gen_backend_stubs.py`经`gen_target_registration("sparse", DispatchKey.SparsePrivateUse1, ...)`把该包装注册到**SparsePrivateUse1分派键**（主线:1799–1806、发布:871–878） | 生成体在构建期产出、不随仓提交——本表是生成器源码的静态推导，未运行gencode；注册面只证明键与包装的连接，不证明任意稀疏布局（COO/CSR/混合）都被该键接住 |
| `sparse::max_sparse(self)`（op_plugin/ops/opapi/sparse/SparseMaxKernelNpuOpApi.cpp 21–24，主线与发布两版本去空白字符流相同） | `self.to_dense()`后`at::max(dense_tensor)`——**先稠密化再重入ATen分发** | 没有原生稀疏max内核：稀疏self的检测走稠密化路径；to_dense本身是上游ATen/torch_npu实现（未核对），稠密化的内存与拷贝成本不在本层核对；重分发后落回本卡已核对的max(self)实现（acl_op路全局委托amax、主线opapi的numel>0检查等见上文各节），不重复展开 |
| `sparse::max_out_sparse(self, other, result)`（同文件26–29） | `self.to_dense()`后`at::max_out(dense_tensor, other, result)`——重入pairwise max_out分发（上文pairwise节的发布max_out包装：DO_COMPATIBILITY(aclnnMaximum, acl_op::max_out)路） | **只对self做to_dense**——other与result原样传入：other若也是稀疏张量，其在at::max_out内部的路径未核对，不据本包装断言支持；result按pairwise out合同（check_tensor以broadcast尺寸为参照） |
| 消费语义小结 | 稀疏COO的self经SparsePrivateUse1键进入`max_sparse`包装后立即to_dense，检测计算全部在稠密路径上完成；输出为稠密张量 | 上文pairwise节“sparse标记只按登记原文记录，其消费语义未核对”由本节核对；`[v2.1, newest]`只是登记的版本范围，不证明所有安装组合装载了sparse注册组（与上文all_version口径同型） |

torch.min对稀疏输入在本源集内既无sparse标记也无SparseMin实现文件（主线与发布两版本 `op_plugin/ops/opapi/sparse/` find零命中：仅SparseAdd/SparseCoalesce/SparseMax/SparseTensorUtils四组），其框架侧路径（ATen默认稀疏分发或CPU回退）未核对，不外推为不可用。本节静态阅读：未构造稀疏张量、未运行分发或数值验证，不新增verified或平台承诺。

### max系sparse补充证据

- [SparseMaxKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/sparse/SparseMaxKernelNpuOpApi.cpp)（primary）：21–29；max_sparse与max_out_sparse两个完整函数体（文件31行，前部版权头不重复计行）。
- [SparseMaxKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/sparse/SparseMaxKernelNpuOpApi.cpp)（implementation）：21–31；发布侧完整函数体（33行），与主线去空白字符流相同（仅排版差异）。
- [gen.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/gen.py)（primary）：245–249、403–408；`_sparse`后缀声明与包装体生成段。
- [gen_op_plugin_functions.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/gen_op_plugin_functions.py)（primary）：40–47；`sparse`字段并入impl_ns段（`new_item['sparse'] = 'op_api'`）。
- [gen.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/gen.py)（implementation）：同两段（与主线同构，行段见manifest source_meta行数）。
- [gen_op_plugin_functions.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/gen_op_plugin_functions.py)（implementation）：44–48、62–65；同口径（发布无dvm行，行段对齐同名语句）。
- [gen_backend_stubs.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/gen_backend_stubs.py)（primary）：1799–1806；`gen_target_registration("sparse", DispatchKey.SparsePrivateUse1, ...)`调用段。
- [gen_backend_stubs.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torchnpugen/gen_backend_stubs.py)（implementation）：871–878；同口径。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3398–3401；max(Tensor self)条目含sparse标记（该文件已列于frontmatter来源）；sparse全表与min负向见上文正文rg锚点。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3292–3295、3313–3317；max(Tensor self)与max.out两条目含sparse标记（该文件已列于frontmatter来源）。
- 负向证据：`op_plugin/ops/opapi/sparse/`主线与发布两版本仅SparseAdd/SparseCoalesce/SparseMax/SparseTensorUtils四组文件（find零其他）；`min(Tensor self)`/`min.out`条目主线与发布两版本均无`sparse:`字段（rg `-B4 "    sparse:"`正文核对零min命中）；canonical与全部batch*/staged rg `max_sparse|max_out_sparse|SparseMaxKernelNpuOpApi` 零命中（sparse范围账本稿的defer声明除外，其显式归本卡owner）。
