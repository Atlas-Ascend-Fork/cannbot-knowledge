---
type: Guide
title: 原生线性代数：分解精度、LU产品与CPU回退
description: 区分linalg接口的输入类型、六维matmul限制、lu的950DT范围和lstsq可能回退CPU。并含 linalg_cholesky/qr/cross 的符号探测回退、本地检查与旧ACL整备。并含 trace 与 triangular_solve.X 的对角和、双输出三角求解包装。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-linalg.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-linalg.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgSolveTriangularKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgSvdKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgSolveTriangularKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgSvdKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgCholeskyKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgCholeskyKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgCrossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgCrossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgQrKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgQrKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LinalgCrossKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LinalgCrossKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LinalgQrKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LinalgQrKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TraceKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TraceKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TriangularSolveKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TriangularSolveKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/TriangularSolveKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/TriangularSolveKernelNpu.cpp
  role: implementation
created_at: '2026-11-09T12:28:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生线性代数：分解精度、LU产品与CPU回退

## 固定来源与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14支持页；七版本及实际存在的中英文页分别审阅，不回推26.0/PyTorch2.8发布组合，也不将950DT扩为950PR。文档未收录的接口/产品只表示此清单未验证；支持条目不是完整社区参数手册。本卡仅静态审阅，未执行上游、设备或性能实验。

## 明确限制的入口

| linalg入口 | 本提交支持页限制 |
| --- | --- |
| norm | input仅BF16/FP16/FP32 |
| vector_norm | 2.7.1/2.9/2.10中英文列input BF16/FP16/FP32；2.11..2.14中文仅列产品、英文未收录该条目 |
| cholesky | A仅FP32 |
| qr | A仅FP32/FP64/complex64/complex128 |
| solve_triangular | A/B仅FP32/FP64/complex64/complex128 |
| matmul | input仅FP16/FP32，最多6维 |
| lstsq | 可能回退CPU执行 |

以上入口的已列产品为A2/A3训练系列与950DT。vector_norm旧版限制与新版省略都保留，不从省略推定类型扩展，也不把norm、vector_norm、matrix_norm互相替代。linalg.matmul与torch.matmul或量化matmul的类型/维数应按各自条目判断。

## LU与未给细表的分组

中文七版本对lu明确A2/A3不支持、950DT支持；lu_factor、lu_solve、lu_factor_ex则列三类产品，不能据LU前缀统一成一个产品结论。英文linalg页未列lu等多个中文入口，不将英文缺项改成不支持。

中文页对matrix_norm、det/cond、eig/eigvals/eigh/eigvalsh、svd/svdvals、solve、inv/pinv、matrix_exp/matrix_power、cross/vecdot/multi_dot/householder_product、tensorinv/tensorsolve/vander，以及cholesky_ex/inv_ex/solve_ex、ldl_factor/ldl_factor_ex/ldl_solve列三类产品。部分旧页章节顺序不同；这些条目没有另一份完整dtype/参数/梯度表，不能把qr的复数或cholesky的FP32横向扩展给它们。

## 精度与执行位置验收

固定具体分解、输入条件、dtype、维数及前后向，比较结果、残差、梯度与实际Kernel。对lstsq同时核对CPU路径和设备间拷贝，分开测量数据转移与计算；清单“支持”不保证全部计算在NPU，调用成功也不保证数值稳定或吞吐提升。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-linalg.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-linalg.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-linalg.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-linalg.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-linalg.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-linalg.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-linalg.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-linalg.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-linalg.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-linalg.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-linalg.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-linalg.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-linalg.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-linalg.md)（constraint）

## 三角求解与SVD：工作副本和结果类型准备

固定OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的包装显示：solve_triangular即使只返回X，也准备一份系数矩阵clone；主线SVD新增奇异值的实数dtype整理与空输入路径。以下补执行准备，不扩大前面支持页的产品/类型矩阵。

| gate/入口 | 实际行为 | 可见准备成本 |
|---|---|---|
| 三角求解，外部输入检查通过 | 广播B与A，条件满足时将B转A dtype | dtype转换请求、X结果申请、A.clone |
| left=false | B与A各transpose(-2,-1)，upper取反，执行后再转置X | 布局变化；SDK的transpose参数仍为false |
| solve_triangular out | 求得独立X后resize_as_并copy_到out | out接口仍包含工作结果和写回请求 |
| SVD compute_uv=false | U和Vh各创建shape{0}对象，仍准备S | 省去完整UV申请，不代表无任何输出准备 |
| 主线SVD复数输入 | 将sigma整理为对应实数dtype | ComplexFloat走to；ComplexDouble走实数empty+copy_ |
| 主线SVD空输入且compute_uv/full_matrices为true | 非空U/Vh先zero_再对角fill_(1) | 单位阵构造请求，跳过后面的out helper |

### 三角求解的复制与左右变换

两版本地入口仅先明确检查A/B的rank都>=2，exec helper随后调用外部checkInputsSolver，再_linalg_broadcast_batch_dims(B,A,nullptr)。外部检查通过后，如果广播后的B和A类型不同，才请求B.to(A dtype)；因此这个局部条件不能证明上层接受任意混合dtype。

helper为B形状申请self_working_copy，并对广播后的A.clone，作为aclnnTriangularSolve的两个输出位置，最后只返回前者X。系数矩阵副本没有作为Python可见结果返回，也不表示它的申请/保值成本可以删除；这里未展开SDK对第二输出及别名的契约。

left=true直接用B/A、原upper与transpose=false；left=false使用两输入的转置和!upper，同样transpose=false，然后把X再转置。functional的右侧求解直接返回该转置对象，out路线则对X或X_transpose执行out.resize_as_(...).copy_(...)。不能仅由数值目标相同就忽略两种返回路线的布局和复制差别。

这两个手写入口没有DO_COMPATIBILITY分支；所列Schema只声明op_api all_version。没有在本段根据算子名字推导CPU或旧ACL自动回退，完整ATen广播、输入检查和实际SDK约束仍按所配环境核对。

### SVD的shape与主线实数奇异值

局部先检查rank>=2。主线允许Float/Double/ComplexFloat/ComplexDouble进入后续准备，发布仅允许Float；这不是把旧平台支持页升级成任意硬件均支持这些dtype。

设输入最后两维为m、n，k=min(m,n)：S申请batch+[k]；compute_uv时U为batch+[m,full?m:k]，Vh先按batch+[n,full?n:k]申请再转置末两维，形成batch+[full?n:k,n]。compute_uv=false则U/Vh各申请{0}。S最初仍按A准备，不能在申请阶段就把复杂输入的sigma说成已经是实数Tensor。

两版_linalg_svd.U的gen_opapi配置先生成V=`Vh.dim()<=1 ? Vh : Vh.transpose(-1,-2)`，exec字段为`aclnnSvd,A,full_matrices,compute_uv,S,U,V`；这解释了手写文件中没有另一个op_api::_linalg_svd_out定义的来源。生成配置的一般规则见[OpPlugin适配](../../inference/guides/optimization/torch_npu/torch_npu_opplugin_adaptation.md)。driver虽存在于Schema并由functional传给out helper，exec字段没有它，不能据传参就宣称本地已按driver选择算法；本卡未执行生成器或编译验证。

主线非空路线调用out helper后再Vh.conj()，发布则直接返回helper结果，没有这条额外语句。conj调用不等于此处已经请求物理共轭复制，其实际视图/派发另核。

主线to_real根据A的对应实数类型处理S：已是同类型则复用sigma；目标为Double时申请同shape实数Tensor再copy_；其余调用sigma.to(real_dtype)。ComplexDouble的empty+copy分支旁注释称为绕开特定.to降精度路径，这里确认的是实际转换请求，不把注释当成本卡复现或整体FP64精度验证。发布没有此转换lambda，也没有主线的空输入单位阵分支。

空输入判断发生在S/U/Vh准备之后；只有compute_uv与full_matrices都为true，才对非空U/Vh置单位阵，随后返回(U,to_real(S),Vh)。性能评估应记录版本、输入dtype、m/n、compute_uv/full_matrices、left/upper/unitriangular及out，分别检查工作副本、布局、sigma转换和空输入准备，再核数值残差与梯度。本节仅静态审阅，未执行ATen/生成器/SDK/设备或性能测试，不新增verified或平台承诺。

### 线性代数实现证据

- [LinalgSolveTriangularKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgSolveTriangularKernelNpuOpApi.cpp)（implementation）：1–105。
- [LinalgSvdKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgSvdKernelNpuOpApi.cpp)（implementation）：1–99。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：631–641、3035–3039。
- [LinalgSolveTriangularKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgSolveTriangularKernelNpuOpApi.cpp)（implementation）：1–105。
- [LinalgSvdKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgSvdKernelNpuOpApi.cpp)（implementation）：1–60。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：616–626、2936–2940。

## linalg_cholesky/qr/cross：符号探测回退、本地检查与旧ACL整备

上文三角求解与SVD小节核对了op_api直发路的工作副本准备；本节补同一登记面中三个入口的包装路由。linalg_cross(.out)/linalg_qr(.out)主线与发布两版本均登记acl_op+op_api all_version（主线yaml 3019–3033、发布2920–2934，逐字相同）；linalg_cholesky(.out)只登记op_api、无acl_op条目（主线5573–5577、发布5401–5405，逐字相同）。linalg_vector_norm(.out)的实现层已由[普通范数卡](torch_npu_norm_p_routes_dtype_and_foreach_preparation.md)按LinalgNormKernelNpuOpApi.cpp整文件核对（p门控与版本helper），本节不重复。CANN内核侧另见[Cholesky内核卡](../../../ops/ascendc/operators/aclnn/math/math/linalg_cholesky.md)与[linalg_cross_950](../../../ops/ascendc/operators/aclnn/math/math/linalg_cross_950.md)（本卡未核对其内核兼容性与语义）。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| linalg_cholesky（两文件主线与发布两版本逐字节相同）：**无DO_COMPATIBILITY**，每入口先`check_aclnn_kernel_available("aclnnLinalgCholesky")`（检查API名与名拼接GetWorkspaceSize两个符号地址、任一空即false：主线op_api_common.cpp 767–773、发布785–792定向读）；符号可用时按self.sizes()+self dtype（out用check_tensor、functional用apply_tensor_without_format）后单次`EXEC_NPU_CMD(aclnnLinalgCholesky,self,upper,out)` | 符号不可用时**不抛错不告警**地换ATen组合：out变体申请`at::empty({0},Int)`的info后`at::linalg_cholesky_ex_out(out,info,self,upper,false)`再`at::_linalg_check_errors(info,"linalg.cholesky",self.dim()==DIM_2D)`；functional取`at::linalg_cholesky_ex(self,upper,false)`二元组后同校验。cholesky_ex/_linalg_check_errors为ATen组合实现、最终派发未核对；该静默换路没有DO_COMPATIBILITY的Aclnn-only TORCH_CHECK抛错或ASCEND_LOGW告警，两种回退机制不同 |
| linalg_cross op_api（主线与发布两版本逐字节相同）：`DO_COMPATIBILITY(aclnnLinalgCross,acl_op::同名)`后**本地TORCH_CHECK**：self/other维度数相等（原文"linalg.cross: inputs must have the same number of dimensions."）且`maybe_wrap_dim(dim,rank)`后两侧该维长度都==3；broadcast shape+self dtype申请后传`wrap_dim`单次`EXEC_NPU_CMD(aclnnLinalgCross,self,other,wrap_dim,out)` | 维长3与同维检查只在此层显式存在（回退文件内无，见下）；输出dtype跟随self而非result_type；DO_COMPATIBILITY宏语义引用上文sort/topk卡已核对结论（Aclnn-only抛错/否则LOGW回退acl_op） |
| linalg_cross acl_op（主线与发布两版本逐字节相同）：ACE命令"Cross"（attr "dim"；nocheck接受optional dim、无值时哨兵-65530按原文记录）；dest_output=is_scalar_wrapped_to_tensor(self)?other:self，CheckOut/apply以dest_output的NPU格式+self dtype为参照；check_match不匹配走format_contiguous执行+format_fresh_view回写 | 回退文件内**无**dim维长3或同维检查（校验只在op_api层，本地拒绝的组合在回退路是否被拒未核对）；"Cross"内核语义未核对；传给命令的是原dim而非wrap_dim，负轴处理未核对 |
| linalg_qr op_api（主线与发布两版本逐字节相同）：`DO_COMPATIBILITY(aclnnLinalgQr,acl_op::同名)`后本地TORCH_CHECK：self.dim()>=2与mode∈{reduced,complete,r}（报错带实际mode）；mode映射reduced=0/complete=1/r=2；本地shape推导（k=min(m,n)）：reduced→Q{m,k}/R{k,n}、complete→Q{m,m}/R{m,n}、r→Q{0}/R{k,n}；out按self参照check_tensor双输出、functional按self.options申请，单次`EXEC_NPU_CMD(aclnnLinalgQr,self,mode_int,Q,R)` | 输出dtype跟随self；mode字符串→int的映射是包装约定；check_tensor内部未核对；本地推导不保证SDK对任意batch/m/n接受 |
| linalg_qr acl_op（pin差仅qr_npu_output_size内int64_t/发布int拼写，其余逻辑一致）：同样的dim>=2/mode TORCH_CHECK；some=(mode=="complete")?false:true——"r"也按some=true取Q{m,k}/R{k,n}；ACE命令"Qr"（attr full_matrices=!some）；双输出CheckOut以self为参照、check_match分别处理；**mode=="r"时在执行后**才把Q整改为空：out变体再次CheckOut(Q,{0})、functional直接重新apply_tensor_without_format({0})丢弃已算Q | 回退路"r"模式仍按{m,k}申请并执行Q、随后本地丢弃——与op_api路r模式从不申请Q形成可观察准备差异；"Qr"内核是否本就产出Q未核对，不据此计device成本 |
| pin差 | 三份opapi文件与LinalgCross aclops主线与发布两版本逐字节相同；LinalgQr aclops仅int64_t/int类型拼写差；cholesky无acl_op文件（yaml亦无登记），其ATen组合回退不经aclops |

本节静态阅读：未运行任何分解/求值；_linalg_check_errors的检查内容在ATen侧、未核对；上文支持页的cholesky仅FP32、qr的复数等dtype矩阵不因本节包装事实扩大。

### linalg_cholesky/qr/cross 补充证据

- [LinalgCholeskyKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgCholeskyKernelNpuOpApi.cpp)（primary）：1–48；完整本地小文件。
- [LinalgCholeskyKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgCholeskyKernelNpuOpApi.cpp)（implementation）：1–48；与主线逐字节相同。
- [LinalgCrossKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgCrossKernelNpuOpApi.cpp)（primary）：1–65；完整本地小文件。
- [LinalgCrossKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgCrossKernelNpuOpApi.cpp)（implementation）：1–65；与主线逐字节相同。
- [LinalgQrKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinalgQrKernelNpuOpApi.cpp)（primary）：1–108；完整本地小文件。
- [LinalgQrKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinalgQrKernelNpuOpApi.cpp)（implementation）：1–108；与主线逐字节相同。
- [LinalgCrossKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LinalgCrossKernelNpu.cpp)（implementation）：1–66；完整本地小文件；与发布逐字节相同。
- [LinalgQrKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LinalgQrKernelNpu.cpp)（implementation）：1–143；完整本地小文件；与发布差异仅为qr_npu_output_size内int64_t（发布int）类型拼写，其余逻辑一致（整文件diff -u核对）。
- [LinalgCrossKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LinalgCrossKernelNpu.cpp)（implementation）：1–66；与主线逐字节相同。
- [LinalgQrKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LinalgQrKernelNpu.cpp)（implementation）：1–143；同上口径。
- [op_api_common.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）：767–773；check_aclnn_kernel_available定义定向读。
- [op_api_common.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）：785–792；同口径。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119；DO_COMPATIBILITY宏定义定向读（cross/qr使用）。
- [op_api_common.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–110；同口径。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3019–3033、5573–5577；cross/qr/cholesky六条目完整字段（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：2920–2934、5401–5405；同口径，与主线逐字相同。

## trace 与 triangular_solve.X：对角和、双输出三角求解

本节核对同登记面剩余两名。主线与发布两版本 yaml均登记 `trace` 与 `triangular_solve.X` 为 acl_op+op_api all_version（主线5135–5142、5144–5156；发布4969–4976、4978–4990，逐字相同），两者op_api路均由gen_opapi生成（trace：out空shape、dtype按 `isIntegralType(self.scalar_type(), true)` 取kLong否则self、exec aclnnTrace；triangular_solve.X：X/M按 `op_infer::triangular_solve_output_size(self, A)`、new_params注入output_sizes、exec aclnnTriangularSolve）。生成体不随仓提交，gen_opapi块即登记面实现事实；生成wrapper实际host检查未运行gencode验证。手写层只有acl_op路，下表核对：

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| trace acl_op（主线与发布两版本仅排版差）：TORCH_CHECK `self.dim() == 2`（原文"trace: expected a matrix, but got tensor with dim ..."）→outDtype整型（isIntegralType含bool）取kLong否则self dtype→`apply_tensor({}, outDtype, self)`（标量输出，shape列表为空）→单次ACE命令"Trace"（TraceKernelNpu.cpp 22–31） | 2D硬检查只在acl_op路；gen_opapi的op_api路dtype规则与acl_op一致（整型→Long）但无2D检查登记；"Trace"内核语义与aclnnTrace设备侧均未核对，不据此比较两路数值/性能 |
| triangular_solve.X acl_op：`triangular_solve_out_common_nocheck` 先 `at::native::_linalg_broadcast_batch_dims(self, A, "triangular_solve")`（ATen helper，批维广播），TORCH_CHECK **两侧均为Float**（原文"_triangular_solve_helper_npu only supported Float, but get ..."）与A.dim()>=2；unitriangular时用 `at::eye` 组合将对角置1（`a_tensor * (1 - diagonal_tensor) + diagonal_tensor`，host组合非内核参数）；ACE命令"MatrixTriangularSolve"（attr lower=!upper、adjoint=transpose），输入顺序 **A在前self在后**，输出为self工作副本；外层 `triangular_solve_out` 对X/M分别 `resize_as_`+`copy_` 写回双输出（TriangularSolveKernelNpu.cpp 23–37、custom_functions/aclops/TriangularSolveKernelNpu.cpp 24–58） | M返回的是广播前 `a_broadcasted.clone()`（在unitriangular对角修正**之前**取的clone），"cloned_coefficient"语义按代码字面；Float-only是本层硬检查，op_api生成路无此登记；`_linalg_broadcast_batch_dims`/`at::eye` 是ATen组合（上游，六个固定版本外）内部未核对；"MatrixTriangularSolve"内核对第二输出/别名的契约未核对 |
| pin差 | 两文件主线与发布两版本均仅排版差异（diff -wB过滤后语义一致）；yaml条目逐字相同 |

本节静态阅读：未运行任何求解/求值；上文支持页的矩阵类dtype表不因本节包装事实扩大；trace在两路的输出dtype规则一致性按登记面字面记录，未数值验证。

### trace/triangular_solve 补充证据

- [TraceKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TraceKernelNpu.cpp)（implementation）：18–33；完整本地小文件。
- [TraceKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TraceKernelNpu.cpp)（implementation）：18–36；与主线仅排版差异（diff -wB过滤后语义一致）。
- [TriangularSolveKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TriangularSolveKernelNpu.cpp)（implementation）：16–38；完整本地小文件。
- [TriangularSolveKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TriangularSolveKernelNpu.cpp)（implementation）：16–38；与主线仅排版差异。
- [custom_functions/aclops/TriangularSolveKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/TriangularSolveKernelNpu.cpp)（primary）：21–59；完整本地小文件。
- [custom_functions/aclops/TriangularSolveKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/TriangularSolveKernelNpu.cpp)（implementation）：21–59；与主线仅排版差异。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5135–5156；trace与triangular_solve.X完整条目（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：4969–4990；同口径，与主线逐字相同。
