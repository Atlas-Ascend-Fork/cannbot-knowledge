---
type: Guide
title: torch矩阵与信号运算：精度模式、距离和形状限制
description: 核对函数级矩阵乘类型、950精度代价、cdist模式、STFT迁移及窗口误差范围；含 BLAS 向量入口 addmv/addr/dot/mv/vdot 的 Eager 包装层：dtype 参照分裂、acl_op 组合命令与生成层 exec 合同。
tags:
- task.optimization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddmvKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MvKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddmvKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddrKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DotKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/VDotKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MvKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddmvKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MvKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AddmvKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AddrKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DotKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/VDotKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MvKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py
  role: implementation

created_at: '2026-11-09T14:10:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# torch矩阵与信号运算：精度模式、距离和形状限制

## 固定来源与参数表的范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的2.7.1、2.9至2.14中英文torch页；下表默认2.14，较早版本与实际收录语言另列。产品为A2/A3训练系列和950DT，不扩到950PR，不回推26.0/PyTorch2.8发布基线。

每行的input、dtype、tensors等是该条目的局部字段，不与Tensor方法的self表互换，不表示返回值或整个模型的数据类型。没有独立类型表、未收录语言/版本不等于已证实不支持；显式产品排除和额外条件另列。不借同名别名、父对象或相邻函数补齐参数、默认值与实现。这里仅静态核对，没有运行上游、编译、加载文件或进行设备实验。

## 精度模式与类型表同时成立

已收录条目的产品表列三产品。addmm/bmm/matmul/mm的input在2.11至2.14为FP16/FP32，较早三版本另列BF16；matmul输入最多6维并支持Named Tensor。

einsum/addmm/baddbmm/bmm/matmul/mm的950DT说明默认高性能FP32或complex64结果可能与GPU及A2/A3有精度差异，cube_math_type为4可切高精度但降低性能。complex64出现在精度说明中，不代表那些只列FP16/FP32或BF16的input表已允许complex64。实际setter需CubeMathType枚举，按[卷积与精度配置](torch_npu_native_convolution_constraints.md)核对，不直接给属性赋裸整数4。
## 函数级参数类型

| 函数/对象 | 局部参数类型表 | 来源 |
| --- | --- | --- |
| `torch.tensordot` | a/b=FP16/FP32 | 中英文 |
| `torch.hann_window` | dtype=BF16/FP16/FP32 | 中英文 |
| `torch.baddbmm`、`torch.corrcoef`、`torch.dist` | input=BF16/FP16/FP32 | 中英文 |
| `torch.outer` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.gradient` | input=BF16/FP16/FP32/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.dot` | input=BF16/FP16/FP32/UINT8/INT8/INT32 | 中英文 |
| `torch.addbmm`、`torch.addmm`、`torch.bmm`、`torch.matmul`、`torch.mm`、`torch.mv`、`torch.vdot` | input=FP16/FP32 | 中英文 |
| `torch.addmv` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.addr` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.cross` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.slogdet` | input=FP32/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.stft` | input=FP32/FP64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.cov` | input=FP32 | 中英文 |
| `torch.einsum` | operands=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.cdist` | x1/x2=BF16/FP16/FP32 | 中英文 |
| `torch.trapezoid` | y/x=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.cumulative_trapezoid` | y/x=FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.kron` | 未给独立参数类型表 | 中英文 |
| `torch.bartlett_window`、`torch.blackman_window`、`torch.cholesky_inverse`、`torch.cholesky_solve`、`torch.convolution`、`torch.embedding`、`torch.geqrf`、`torch.hamming_window`、`torch.inner`、`torch.lobpcg`、`torch.logdet`、`torch.lu_unpack`、`torch.ormqr`、`torch.pca_lowrank`、`torch.svd_lowrank`、`torch.trace`、`torch.vander` | 未给独立参数类型表 | 仅中文 |

## 较早版本的不同参数表

| 函数/对象 | 文档版本 | 当时参数表 | 2.14参数表 | 来源 |
| --- | --- | --- | --- | --- |
| `torch.addmm`、`torch.bmm`、`torch.matmul`、`torch.mm` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32 | input=FP16/FP32 | 中英文 |

## 文档收录版本与语言

| 函数/对象 | 中文收录版本 | 英文收录版本 |
| --- | --- | --- |
| `torch.bartlett_window`、`torch.blackman_window`、`torch.cholesky_inverse`、`torch.cholesky_solve`、`torch.geqrf`、`torch.hamming_window`、`torch.inner`、`torch.lobpcg`、`torch.logdet`、`torch.lu_unpack`、`torch.ormqr`、`torch.pca_lowrank`、`torch.svd_lowrank`、`torch.trace`、`torch.vander` | 2.10.0、2.11.0、2.12.0、2.13.0、2.14.0、2.7.1、2.9.0 | 未收录 |
| `torch.qr` | 2.10.0、2.11.0、2.12.0、2.13.0、2.7.1、2.9.0 | 2.10.0、2.11.0、2.12.0、2.13.0、2.7.1、2.9.0 |
| `torch.signal.windows.bartlett`、`torch.signal.windows.blackman`、`torch.signal.windows.cosine`、`torch.signal.windows.gaussian`、`torch.signal.windows.general_hamming`、`torch.signal.windows.hamming`、`torch.signal.windows.hann`、`torch.signal.windows.kaiser`、`torch.signal.windows.nuttall` | 2.10.0、2.11.0、2.12.0、2.7.1、2.9.0 | 未收录 |
| `torch.convolution`、`torch.embedding` | 2.13.0、2.14.0 | 未收录 |

## 距离、形状和回退

cdist的x1/x2仅BF16/FP16/FP32；p=2.0时compute_mode只支持donot_use_mm_for_euclid_dist，其他值会自动改成这个模式。950DT的FP16精度可能与A2/A3不同，不能把请求使用矩阵乘当作实际命中该路线。cross要求两输入shape相同；kron不支持5维及以上输入；slogdet可能CPU回退。

## STFT、窗口与旧入口

stft超时时来源建议官方set_op_execute_time_out调高阈值，这只是超时判定配置，不是执行速度优化或无限延长的保证。英文2.9/2.10/2.14要求实数input显式传return_complex，提示False弃用、使用True，若需实数表示再用view_as_real；其他版本未重复提示。hann_window仅BF16/FP16/FP32，FP32且window_length大于10000时可能有误差。

qr仅同提交2.7.1、2.9至2.13收录；英文2.9/2.10建议改linalg.qr并把some参数换成mode。中文signal.windows九个窗口函数仅2.7.1、2.9至2.12收录，与bartlett_window等不同名称分别记录，不由缺项推断实现删除。中文convolution/embedding仅2.13/2.14列产品，没有补齐卷积或嵌入参数合同。

其他仅给产品表的分解、低秩、积分、梯度和信号条目，不从名称推导算法精度、反向支持、分块策略或收益。FFT依赖与限制另见[FFT指南](torch_npu_native_fft_constraints.md)。

## 2.14总览明确声明旧分解入口移除

同提交2.14两语言总览说明torch.qr、Tensor.qr、torch.cholesky、Tensor.cholesky的实现已移除、调用会报错，推荐torch.linalg.qr/cholesky；qr的some迁为mode，Cholesky上三角结果示例为torch.linalg.cholesky(A).mH。这里区分总览的明确移除声明与普通接口表缺项，前文“缺项不能推定删除”不抹去该版本的明示说明。

这些是目标文档版本声明，不能据此认定本卡来源外的 26.0/PyTorch2.8 发布组合也删除了旧入口，也不能以文档存在推定实际安装包已完成相应NPU数值验证。Tensor方法与torch根函数仍各按自己的局部类型和产品表使用。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/overview.md)（primary）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/overview.md)（constraint）

## BLAS 向量入口 addmv/addr/dot/mv/vdot 的 Eager 包装层

上文函数级类型表只锚定公开支持页；本节补齐 `addmv(±out/_)`、`addr(±out/_)`、`dot(±out)`、`mv(±out)`、`vdot(±out)` 在两版OpPlugin固定树的 Eager 实现层。yaml 登记主线与发布两版本字段逐字相同（vdot.out 主线与发布两版本均显式 `dtype: out`，无字面差异；对照 dot.out 主线与发布两版本均无 dtype 行——ResInfo 缺省 dtype=out，同语义）：`addmv`/`addmv.out`/`addmv_`（主线1003–1013、发布965–975）与 `mv`/`mv.out`（主线3684–3690、发布3571–3577）均 acl_op+op_api all_version、**无 gen_opapi**——op_api 路由由手写文件承担；`addr`/`addr.out`/`addr_`（主线1015–1035、发布977–997）、`dot`/`dot.out`（主线1978–1993、发布1915–1930）、`vdot`/`vdot.out`（主线5418–5434、发布5251–5267）带 gen_opapi——op_api 路由由生成层承担，主线与发布两版本均无对应手写 opapi 文件（find 零命中）。生成层行为按 struct_codegen 模板静态推导（与[激活精度卡]同口径，生成代码不随仓提交、未运行 gencode）。本节只读源码，未运行任何设备或CPU算子。

| 入口 | 实际门槛→动作 | 失败/边界 |
| --- | --- | --- |
| addmv/.out/_（opapi 手写 AddmvKernelNpuOpApi，主线与发布两版本去空白字符流相同，25–72） | 共享内层：单次 `EXEC_NPU_CMD(aclnnAddmv, self, mat, vec, alpha, beta, result, cube_math_type)`——**实参顺序 alpha 在 beta 前**（与 schema 形参序相反，按原文记录），`cube_math_type = get_cube_math_type_with_passthrough()`（精度开关语义见[卷积与精度配置](torch_npu_native_convolution_constraints.md)）。addmv functional：先算 `propagate_names_for_addmv`（在 DO_COMPATIBILITY 之前）→ `DO_COMPATIBILITY(aclnnAddmv, acl_op::addmv(...))` → 输出尺寸 `addmv_npu_output_size(self, mat)`（self.sizes() 与 {mat.size(0)} 广播）→ promote=`result_type({self,mat,vec})`，**promote 为 Bool 且 alpha/beta 任一≠1 时改 Long** → `apply_tensor_without_format`。addmv.out：尺寸不符 `result.resize_(output_size)`（**重整而非拒绝**）；addmv_：`check_memory({self,mat,vec},{self})` 后 EXEC 直写 self | out 变体不做 check_tensor——shape/dtype 不符的 out 被原地 resize，语义与其他入口的 CheckOut 族不同；命名张量在兼容回退前已计算、回退路是否传播由 acl_op 侧决定 |
| addmv（aclops，主线与发布两版本去空白字符流相同，23–73） | **mul+mm+add 组合而非单命令**：`npu_utils::check_1d(vec, "vec", "addmv")` → `vec.unsqueeze(1)` → `at::mul(mat, alpha)` → `at::mm(mat_alpha, mat1)` → `squeeze()` → `add_out(result, mm_mul_result1, self, beta)`；result 先 resize_ 到广播尺寸 | 三条设备命令（mul/mm/add）加中间申请；acl_op 路没有专用 addmv 设备命令，与 aclnn 路不互推 |
| addr/.out/_（生成层 exec aclnnAddr/aclnnInplaceAddr，无手写文件） | addr functional：`DO_COMPATIBILITY(aclnnAddr, acl_op::addr(...))` → out 尺寸 `addr_npu_output_size(self, vec1, vec2)`（self.sizes() 与 {vec1.size(0), vec2.size(0)} 广播）、dtype=`at::native::result_type({self,vec1,vec2})` → `apply_tensor_without_format` → `EXEC_NPU_CMD(aclnnAddr, self, vec1, vec2, beta, alpha, result)`（生成层按 schema 参数序补全，beta 在 alpha 前）。addr.out：`check_tensor({self,vec1,vec2}, out, out.scalar_type(), addr_npu_output_size(...))`。addr_：**inplace 生成分支无 size/dtype 定义、无申请/检查**，`EXEC_NPU_CMD(aclnnInplaceAddr, self, vec1, vec2, beta, alpha)` 后 return self——专用 inplace 命令 | 生成 wrapper 无本地形状/长度检查（vec1/vec2 一维性只在 aclops 路查）；aclnnAddr/aclnnInplaceAddr 设备侧未核对；functional 的 dtype 是三输入 promote，与 out 变体跟 out 自身不同 |
| addr（aclops，主线与发布两版本去空白字符流相同，26–137） | `check_beta_aplha` 四道 TORCH_CHECK（Bool beta/alpha 仅限 Bool 结果，原文"Boolean beta only supported for Boolean results."；全整型输入要求 beta/alpha 整型，原文"For integral input tensors, argument beta must not be a floating point number."）+ `check_1d(vec1/vec2)`；**结果 dtype 为 Bool 时四个张量全部 `_npu_dtype_cast` 到 Float**、beta/alpha `toFloat()`，计算完转回 Bool 再 `out.copy_`；组合：`mul(vec1.unsqueeze(1), vec2.unsqueeze(0))` 外积 → `mul(…, alpha)` → `add_out(result_cast, mul_result_alpha, self_cast, beta_cast)`；addr functional 以 high_dtype `apply_tensor` 申请；addr_ 走 `CheckMemory`+`check_match`/`format_contiguous`/`format_fresh_view` 惯例（见[out 准备卡](../../inference/guides/optimization/torch_npu/torch_npu_out_preparation_resize_and_overlap.md)） | `_npu_dtype_cast` 实现在 torch_npu 仓未核对；Bool 往返是 aclops 路私有，aclnn 路无此层；外积+两条乘加是三命令组合 |
| dot/.out（生成层 exec aclnnDot，无手写文件） | dot functional：`DO_COMPATIBILITY(aclnnDot, acl_op::dot(...))` → out 尺寸空 SmallVector（0 维标量）、dtype=self → `apply_tensor_without_format({}, self.options().dtype(self.scalar_type()))` → `EXEC_NPU_CMD(aclnnDot, self, tensor, result)`。dot.out：`check_tensor({self,tensor}, out, out.scalar_type(), {})` | 生成 wrapper 无 dtype 拒绝检查（整型拒绝只在 aclops 路，见下）；aclnnDot 设备侧未核对 |
| dot（aclops，主线与发布两版本语义相同仅排版，24–60） | **TORCH_CHECK self dtype ∉ {Int, Byte, Char}**（TYPE，原文"'dot_npu' not implemented for 'Int'"——消息只举 Int，Byte/Char 同拒按原文记录），functional 与 out 均查；`CheckOut({self,tensor}, result, self, {})`/`apply_tensor(self, {})`；ACE 命令 `Dot`；`check_match` 不符走 `format_contiguous`+`format_fresh_view` | 整型输入在 acl_op 路被 host 拒绝、生成层路不拒（交 SDK）——两路检查面不对称；上文支持表的 dot 整数行（UINT8/INT8/INT32）与该拒绝不互推，按实际路由核对 |
| vdot/.out（生成层 exec **aclnnDot**——与 dot 同一命令，无手写文件） | 与 dot 同构：functional `{}` 尺寸、dtype=self、`EXEC_NPU_CMD(aclnnDot, self, other, result)`；vdot.out：主线与发布两版本 yaml 均显式声明 `dtype: out`（逐字相同）；对照 dot.out 主线与发布两版本 均无 dtype 行（ResInfo 缺省 dtype=out，同语义） | vdot 与 dot 共用 aclnnDot/“Dot”——复数语义（vdot 为共轭点积）是否由同一命令内部处理未核对，不据命令名断言等价 |
| vdot（aclops，主线与发布两版本语义相同仅排版，24–52） | **无 dot 的整型拒绝检查**（不对称按原文记录）；`CheckOut({self,other}, out, self, {})`/`apply_tensor(self, {})`；ACE 命令 `Dot`（与 dot 同命令）；`check_match` 惯例同上 | dot 拒 Int/Byte/Char 而 vdot 不拒——同一“Dot”命令两种 host 检查面，按入口核对不互推 |
| mv/.out（opapi 手写 MvKernelNpuOpApi，主线25–52、发布25–45） | mv_out：`DO_COMPATIBILITY(aclnnMv, acl_op::mv_out(...))` → `check_tensor({self,vec}, out, out.scalar_type(), {self.size(0)})` → `EXEC_NPU_CMD(aclnnMv, self, vec, out, cube_math_type)`。mv functional：**结果 options 跟 vec**（`apply_tensor_without_format({self.size(0)}, vec.options())`）——mv 的输出 dtype 合同参照是 vec 而非 self，与 addmv 的三元 promote 不同；主线以 `#if !VERSION_BETWEEN(V2R13, VERSION_NEWEST)` 包住命名张量分支（has_names → `at::empty`），发布无版本门恒在（≤2.12 构建主线与发布两版本等价）；cube_math_type passthrough 同 addmv | out 变体 dtype 跟 out 自身、functional 跟 vec——mv 家族内部就有两种参照；主线 ≥2.13 构建丢弃命名张量分支（构建期差异，非运行时分支） |
| mv（aclops，主线与发布两版本去空白字符流相同，27–76） | TORCH_CHECK `self.dim() >= 1`（PARAM，原文"mv(): input tensor must has at least 1 dimension, but got ..."，has 拼写按原文记录）；nocheck 内层：`is_transpose_last_two_dims(self)` 为真时 `InputWithoutContiguous` + attr `transpose_x1=true`（**不物化转置**），否则 `format_contiguous(self)`；`vec.unsqueeze(1)`；ACE 命令 `MatMul`（attr `transpose_x2=false`）——**mv 无专用命令，走矩阵乘**；尾部 `npu_fast_reshape_`（机制与边界见[matmul bmmV2 分发与 fast reshape 卡](../../inference/guides/optimization/torch_npu/torch_npu_aten_matmul_bmmv2_dispatch_and_fast_reshape.md)）；out 变体 `result.unsqueeze_(1)`/`squeeze_(1)` 原地维桥 + `check_match` 惯例 | 转置输入经 attr 旁路连续化、非转置输入先 format_contiguous——同一入口两种准备成本；unsqueeze 维桥是 host 元数据操作不等于数据搬运 |
| 尺寸 helper（KernelNpuOutputSize.cpp，主线226–235、发布215–225） | `addmv_npu_output_size` = `broadcast_ops_npu_output_size(self.sizes(), {mat.size(0)})`；`addr_npu_output_size` = `broadcast_ops_npu_output_size(self.sizes(), {vec1.size(0), vec2.size(0)})` | 广播失败（不可广播形状）的报错来自 broadcast_ops 内部，本层无额外检查 |

跨族三条：其一，**dtype 参照四分裂**——addmv functional 用三元 promote（Bool+非单位标量→Long 特例）、addr functional 用 result_type 而 aclops 路对 Bool 结果做 Float 往返、dot/vdot/mv functional 跟 self 或 vec、全部 .out 变体跟 out 自身（addmv.out 例外：resize_ 重整）；任一路都不构成族规则。其二，**命令面分裂**——acl_op 的 addmv/addr 是 mul/mm/add（或外积+乘加）组合、mv 复用 MatMul（带 transpose attr）、dot/vdot 才有专用“Dot”；aclnn 侧 addmv/mv 携带 cube_math_type、addr_ 走专用 aclnnInplaceAddr、dot/vdot 共用 aclnnDot。其三，**检查面不对称**——dot 的整型拒绝只在 acl_op 路、vdot 无此检查；addmv.out 用 resize_ 而非 check_tensor；vec 一维性检查只在 aclops 路；用 out 变体或生成层路由时不能假设 functional 的 host 检查仍在。

### BLAS 向量入口补充证据

- [AddmvKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddmvKernelNpuOpApi.cpp)（primary）：25–72；addmv_out_op_api/addmv_out/addmv/addmv_ 完整函数体；与发布去空白字符流相同。
- [MvKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MvKernelNpuOpApi.cpp)（primary）：25–52；mv_out/mv 完整函数体（含 V2R13 版本门）。
- [MvKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MvKernelNpuOpApi.cpp)（implementation）：25–45；同构无版本门（整文件 diff -u 核对，差异仅版本门与排版）。
- [AddmvKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddmvKernelNpu.cpp)（primary）：23–73；三个入口完整函数体；与发布去空白字符流相同。
- [AddrKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddrKernelNpu.cpp)（primary）：26–137；check_beta_aplha/addr_out/addr/addr_ 完整函数体；与发布去空白字符流相同（发布124行为排版差异）。
- [DotKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DotKernelNpu.cpp)（primary）：24–60；完整函数体；与发布语义相同（diff -u 核对：排版+尾注释 `// namespace acl_op` vs `//op_plugin` 差异）。
- [VDotKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/VDotKernelNpu.cpp)（primary）：24–52；完整函数体；与发布语义相同（同上口径）。
- [MvKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MvKernelNpu.cpp)（primary）：27–76；mv_out_npu_nocheck/mv_out/mv 完整函数体；与发布去空白字符流相同。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：226–235；addmv/addr 两个尺寸 helper 完整函数体。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：215–225；发布侧同 helper。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1003–1035、1978–1993、3684–3690、5418–5434；12 个 schema 条目完整字段。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：965–997、1915–1930、3571–3577、5251–5267；同条目（主线与发布两版本 逐字相同）。
- [struct_codegen.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py)（implementation）：43–58、295–476；ACLNN_FUNCTIONS_DEFINITION 与 compute_op_api_definition（addr/dot/vdot 生成层行为推导依据）。
- [struct/model.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py)（implementation）：40–105、230–265；ResInfo out 缺省与 cmd_args 展开。
- 负向证据：主线与发布两版本 `op_plugin/ops/opapi/` 无 Addr/Dot/VDot 手写文件（find 零命中）；canonical 与全部 batch*/staged rg `AddmvKernelNpuOpApi|aclnnAddmv|aclnnInplaceAddr|MvKernelNpuOpApi|DotKernelNpu|VDotKernelNpu|AddrKernelNpu|aclnnDot|aclnnAddr|addr_npu_output_size` 零命中——本节为该家族首个实现级小节（上文类型表仅 docs 面；canonical matmul bmmV2 卡仅以 MvKernelNpuOpApi 作 fast_reshape 负向证据，未覆盖 mv 行为）。
