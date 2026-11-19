---
type: Guide
title: 原生卷积执行：路由、梯度分配与格式成本
description: 核对OpAPI与旧ACL卷积路由、mask仍分配的梯度、FP32权重梯度中间值、格式与contiguous成本及HF32重载。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConvolutionKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ConvolutionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConvolutionBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ConvolutionBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvolutionKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConvolutionKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Conv2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Conv2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Conv2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Conv2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp
  role: implementation
created_at: '2026-11-10T12:12:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生卷积执行：路由、梯度分配与格式成本

## 固定调用链与范围

本卡定向核对OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的普通convolution/反向驱动，以及旧ACL Conv2D的分配与特例。两版所选OpAPI计算/入口函数、ACL Conv2D分配函数与新版ACL总入口的去注释token一致，不宣称整份文件、全部版本分支、转置/3D/深度卷积实现都已审完。旧ACL总入口以下限定VERSION_BETWEEN(V2R2,VERSION_NEWEST)分支及共用view helper。

对应TorchNPU精度/分配helper另固定主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`，没有从单个helper推导任意混装版本兼容。整卡产品矩阵未知，保持draft与空平台；本卡不执行上游或设备实验。原生API支持与产品限制仍见[文档层卷积迁移](torch_npu_native_convolution_constraints.md)，GE构图见[卷积Converter合同](../../inference/guides/optimization/torchair/torchair_ge_convolution_lowering.md)。

## 符号存在后仍有实现路由

OpAPI入口在调用计算辅助层前，用DO_COMPATIBILITY检查aclnnConvolution或aclnnConvolutionBackward及对应GetWorkspaceSize符号；缺符号时，ACLNN-only设备报错，其他情形转旧ACL。符号探测只检查动态库入口，不验证该shape/dtype的kernel能力。

随后前向_calc_convolution与反向_calc_convolution_backward各自计算空间维数dim=weight.ndimension()-2，并采用同一条件：

```text
(allow_internal_format OR jit_enabled) AND (dim != 3) AND (NOT conv_sc)
    -> 旧ACL
otherwise
    -> 本地ACLNN分配/调用分支
```

这里allow_internal_format由!CheckForbidInternalFormat取得，jit_enabled由!CheckJitDisable取得；conv_sc分别是各自函数中的static CheckCompatibleImpl结果，不能将切换环境变量描述为每次调用都会重新读取这个值。仅关闭内部格式但仍允许JIT，不足以绕开该旧ACL条件；compatible标志、空间维数和符号检测也会影响路线。dim==3只绕过这个局部条件，不代表3D永不回退或全部3D Kernel均可用。

因此比较配置前后性能时，应先记录真实调用符号、格式转换/在线编译、首次与稳态，再归因开关效果。这个条件改变实现路线，不是“关闭私有格式一律更快”的证明。

## 输出分配与1D补维的成本属于不同层

本地ACLNN前向按conv_npu_output_size分配input.options的输出，调用apply_tensor_without_format，再调用aclnnConvolution。已读TorchNPU helper通过NPU empty、Contiguous memory_format创建这类输出；这不保证后端没有内部workspace、格式转换或输入临时缓冲。

旧ACL的新版_convolution对weight rank3先扩stride/padding/dilation/output_padding，在轴2给input/weight补维，再按transposed分派；最后squeeze输出轴2。共用view4d就是unsqueeze(2)，没有显式contiguous或物理transpose。因此这个补维不独自证明任意非连续、channels_last或私有格式输入已经重排；直接ACLNN路径也没有在所选计算函数中复制这套1D补维代码，不能互相套用局部成本。

普通旧ACL Conv2D请求的输出格式为FP16输入时NC1HWC0，其他类型ND；调用的是apply_tensor_with_format。该helper仍会推导/修正存储format后交给底层分配，应实查结果格式和转换成本，不能仅按逻辑NCHW或format参数宣称最终物理布局固定。逻辑shape、连续性、存储格式和后端执行格式分别核对。

## output_mask不保证ACLNN前端免分配

常规ACLNN反向无条件分配gradInput和gradWeight；gradBias在mask=True时按bias_sizes_opt分配，在False时仍按推导尺寸分配。output_mask继续传给aclnnConvolutionBackward，可能影响后端计算，但本地代码并没有按False跳过这三类输出buffer。禁用槽返回Tensor不证明其值已写入或可作为有效梯度读取。

这与空channel分支不同：入口在符号检测前检查input.size(1)==0，按mask分别返回zeros_like(input/weight)或bias尺寸的零Tensor，未请求槽保持未定义；请求bias梯度时要求bias_sizes_opt存在。它并不是任意numel==0输入都能覆盖的通用短路。

优化仅训练部分参数的模型时，分别统计所请求梯度、前端申请字节数、实际kernel、workspace和峰值存活。不要把图侧output_mask可省节点的结论直接等同于Eager少分配。

## 旧ACL普通Conv2D反向的中间精度和contiguous

旧ACL npu_conv2d_backward按mask才分配各梯度。输入梯度请求FP16时NC1HWC0、其他ND；权重梯度先用FP32申请，groups>1请求NCHW，否则请求与weight相同的NPU格式。上层npu_convolution_backward随后把已定义的权重梯度cast回weight.scalar_type。因而最终weight.grad dtype相同，不代表没有FP32中间分配或cast成本，也不证明kernel内部全部累加细节。

bias反向辅助层先做grad.contiguous()再view：若仅剩N×C元素，沿N归约；其他情形view为[N,C,-1]并沿N和展平空间归约。非连续grad可能因此增加复制；这个显式成本与前述仅unsqueeze的1D补维不同。所选源码没有给出实际耗时，不能先假定该复制占主导。

## 特殊大stride Conv1D会走Matmul，但仍须核对等价性

旧ACL npu_conv2d另有补维后Conv1D特例：stride[1]>63且等于weight.size(3)，padding[1]==0、dilation[1]==1、groups==1并且input.size(1)==1时，将input/weight view后做Matmul，再permute/unsqueeze返回，绕过普通Conv2D命令和上述输出format分配。

本地判定没有额外检查H轴为1或view所需的整除/连续条件；该提前返回分支也没有读取并加回bias。它是需定向核对的静态调用链，不是可直接推广的“卷积改Matmul必然等价且更快”方案。本卡未复现有bias或异常布局的设备结果；使用这类形状时，分别验证有/无bias、边界长度、非连续输入、输出布局及真实参考数值。

## 精度来自bool重载，不是直接照搬cube枚举

本地ACLNN前/反向调用get_cube_math_type(IsAllowConvHF32())。固定TorchNPU的这个bool重载转发到GetCubeMathType(bool)，把allowHf32和IsAllowFP32ToFP16组合成两位码：00为KEEP_DTYPE，01为USE_FP16，10为USE_HF32，11为ALLOW_FP32_DOWN_PRECISION；此重载没有读取CUBE_MATH_TYPE参数。

直接读取CUBE_MATH_TYPE并支持USE_FP32_ADD的代码是另一个无参数重载，不能因为配置对象存在就认定上述卷积调用已经采用它。OpAPI入口接收的allow_tf32、benchmark、deterministic等参数在旧ACL回退表达式中保留，但所选本地ACLNN计算层不消费这些参数来选算法/精度；实际确定性仍可能受共享运行机制影响，本卡不据此断言整个后端无确定性支持。

验收时把实际路线、HF32/降精度策略、前后向误差、dtype/私有格式、mask分配与中间cast放在同一负载中核对，并单独看1D特例和空channel。未完成真实前向、反向及训练步前，不用前端存在或静态审阅认证精度、训练收敛或性能收益；本卡没有新增verified。


## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConvolutionKernelNpuOpApi.cpp)（primary）：所审范围85–103,292–420。

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ConvolutionKernelNpuOpApi.cpp)（implementation）：所审范围212–299。

- [固定实现来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConvolutionBackwardKernelNpuOpApi.cpp)（implementation）：所审范围30–213。

- [固定实现来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ConvolutionBackwardKernelNpuOpApi.cpp)（implementation）：所审范围30–63,82–155。

- [固定实现来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvolutionKernelNpu.cpp)（implementation）：所审范围84–117,715–715,977–1076,1122–1277。

- [固定实现来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConvolutionKernelNpu.cpp)（implementation）：所审范围109–119,809–908,954–1086。

- [固定实现来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Conv2dKernelNpu.cpp)（implementation）：所审范围23–147。

- [固定实现来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Conv2dKernelNpu.cpp)（implementation）：所审范围23–111。

- [固定实现来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Conv2dBackwardKernelNpu.cpp)（implementation）：所审范围179–266。

- [固定实现来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Conv2dBackwardKernelNpu.cpp)（implementation）：所审范围169–208。

- [固定实现来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：所审范围94–119。

- [固定实现来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：所审范围96–110。

- [固定实现来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）：所审范围257–293,385–411。

- [固定实现来源 14](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）：所审范围382–393。

- [固定实现来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp)（implementation）：所审范围385–420。

- [固定实现来源 16](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp)（implementation）：所审范围343–383。
