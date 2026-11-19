---
type: Guide
title: 融合AddLayerNorm：残差输出、梯度复用与Meta边界
description: 记录AddLayerNorm前后向的混合dtype分配、统计shape、optional梯度补零和双槽dx句柄复用，说明Meta差异及跳过测试的边界。
tags:
- task.optimization
- topic.compute.normalization
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddLayerNormKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddLayerNormBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddLayerNormNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddLayerNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_add_layer_norm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_add_layer_norm_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddLayerNormKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddLayerNormBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AddLayerNormNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AddLayerNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_add_layer_norm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_add_layer_norm_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-11T09:03:15Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 融合 AddLayerNorm：残差输出、梯度复用与 Meta 边界

## 固定版本与融合范围

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 与发布 `dedc316708372c9a8bfde4527abd2a94b74840f5`，覆盖 `npu_add_layer_norm` 及其 backward 的 OpAPI/ACL 本地包装、两个小型测试、精确 Meta/Schema/derivative 配置。主线四个 CPP 和两个测试实际全文读取；发布四 CPP 的完整 phase2 token、全部注释差异与两个测试的原始字节逐对核对。外部 ACLNN、OpCommand 执行、生成的 autograd 包装和设备数值另计，未导入或运行上游。

公开 Schema 在两个版本都给出四输出前向、两个 optional 梯度输入的四输出反向，ACL 和 OpAPI 均标 all_version。前向默认 epsilon=1e-5、additional_output=False；这里的版本标签不是任意硬件、dtype 或 shape 的执行认证。对照的 CPU 参考把 x=x1+x2，再以最后一轴的 mean/variance 计算 LayerNorm，并用 gamma、beta 仿射；它只为测试所用的一维 gamma 提供语义参考，不把这个测试扩展为任意多轴归一化证明。

## 前向的实际分配与返回

OpAPI 先以 aclnnAddLayerNorm 做兼容分派；其后两条执行路径如下。兼容宏的符号与门控边界按[原生 LayerNorm 执行指南](torch_npu_native_layer_norm_execution.md)已有固定证据复用，不把探测通过当成设备成功，也不推导存在 kernel 失败后自动重试。

| 本地输出 | OpAPI 与 ACL 的分配规则 |
|---|---|
| y、第四输出 x | x1/x2 dtype 相同时按 x1 分配；不同时按 x1 的形状、设备选项显式申请 FP32 |
| mean、rstd | FP32；shape 为 x1 的前 `x1.dim()-gamma.dim()` 个长度，随后**只追加一个1** |
| additional_output=False | 包装仍申请 x 并返回四个 Tensor 句柄，布尔值传到底层；不能仅据句柄存在保证关闭时 x 的内容有效 |

OpAPI 把一个 undefined bias Tensor 传给 ACLNN，随后输出顺序为 `(y,mean,rstd,x)`。ACL 回退使用命名 OpCommand `AddLayerNorm`，输入 x1/x2/gamma/beta，无额外 bias 输入；epsilon 明确转为 float 属性，并传 additional_output。两个包装均没有在本地为 x2/gamma/beta 添加完整的 shape、dtype 和归一化轴校验；底层接受范围不能由这几个分配分支补出。

混合输入并非只影响内部累加精度：包装明确改变 y 和 x 的输出申请 dtype。优化残差与归一化融合时，应同时检查第四输出是否被后续使用、两路输入 dtype、额外统计及残差申请，不能把 additional_output=False 简化为“该包装完全不申请残差输出”。本卡没有测分配量、融合收益或 kernel 次数。

## 反向的两个 optional 梯度与返回复用

反向按参数顺序接收 `(dy_opt,x1,x2,rstd,mean,gamma,dsum_opt)`。optional 不存在或包含 undefined Tensor 时，dy 与 dsum 各自用 `at::zeros(x1.sizes(),x1.options())` 补成 Tensor；两者都缺失可走两次 zeros，包装没有统一空梯度早退或 output_mask。dgamma、dbeta 总是按 gamma.sizes() 申请 FP32，并交底层同时输出。

OpAPI 先探测 aclnnAddLayerNormGrad，dx 按 x1 申请；ACL 回退的 dx 按补齐后的 d_y 申请。这是两条本地申请依据的区别，dy 的 dtype/shape 若与 x1 不同，不能静默宣称二者所有输出元信息仍必然一致；本卡未验证这种输入组合被底层接受。ACL 命令 `AddLayerNormGrad` 按 dy/x1/x2/rstd/mean/gamma/dsum 输入并输出 dx/dgamma/dbeta。

两个包装最终都直接返回 `(dx,dx,dgamma,dbeta)`：前两个位置来自**同一 dx Tensor 句柄**，没有第二份 dx 申请或 clone。它解释残差相加的两路输入梯度复用边界；不把这段返回值分析冒充实际运行后的 autograd 梯度存储检查，也不能假定调用者可独立原地修改这两个直接返回槽。

两个版本的 derivatives.yaml 都把前向四输出的可微性标为 `[true,false,false,true]`，为 x1/x2/gamma/beta 统一调用 backward，配置实参精确使用 `grads[0]`、缓存 `result2` 作为 rstd、`result1` 作为 mean，以及 `grads[1]` 作为另一梯度。应把这条配置和第四输出的使用一起核对；生成器和自动梯度累加的完整实现不在本卡资格中。

## Meta 与 Eager 需要分开对照

两版完整 Meta 函数相同，但它不根据 x2 dtype 提升输出，y 和第四输出一律 `empty_like(x1,dtype=x1.dtype)`。因此 x1=FP16、x2=FP32 时，本地 Eager 的 FP32 分配和 Meta 的 FP16 声明存在明确差别；不能用这个 Meta 的结果替代混合 dtype 执行合同。

统计 shape 也有边界：Meta 遍历 x1 的全部维度，把 gamma 覆盖的每一维都置1，保持 x1 rank；CPP 则保留前缀后只追加一个1。一维 gamma 时相合，多维 gamma 时两种构造不相同，测试没有覆盖它。这里指出源码声明差别，未声称某个设备已实际报错。Meta 同样不因 additional_output=False 删除第四输出，也没有完整输入检查；本卡 Meta 证据仅含前向完整函数，不提升整个 Meta 模块覆盖资格。

## 测试真正证明和未证明的内容

前向测试文件在模块加载时设 `jit_compile=False`，两个用例均标注 Ascend910B，形状为 `[1,1024,8192]`、gamma/beta `[8192]`；分别使用 FP32/FP32 与 FP16/FP32，设备调用明确传 additional_output=True，与 NumPy 参考比较四个输出。混合用例的显式 dtype 断言只写在 CPU 参考 y 上；设备输出仍交通用 assertRtolEqual，本卡未重新解释外部测试 helper 的附加检查。设备注解不是本卡执行通过或平台资格。

反向测试通过前向 `[0]` 的 out.backward 驱动自动梯度，而非直接调用公开 backward；读取两个输入梯度，却最终只返回 dx0/dgamma/dbeta 供断言，没有单独核 dx1、两个直接返回槽的别名或 dsum 非零贡献。整个测试方法被 unittest.skip 跳过；其参考 epsilon=1e-6，而设备前向未传 epsilon，使用 Schema 默认1e-5。不能把这个被跳过、参考参数还不同的用例称作完整训练数值验证，也不能据此保证 optional 梯度、额外残差输出反传或多维 gamma 的正确性。

## 版本对照与排查落点

四对 CPP 的完整 phase2 token 相同，OpAPI 文件的注释差异仅主线增加末尾 namespace 标记；其余注释相同，改动为排版。两个测试逐字节相同，所选 Meta、Schema 和 derivative 块逐行相同。这里只证明所列固定包装与配置的局部一致，未推导两版底层 CANN、SDK 或运行环境相同。

排查融合模型时记录精确前后向路径、x1/x2/gamma 的 dtype 与 shape、epsilon、additional_output 和第四输出使用方；再逐一对照 Meta 声明、统计 shape、dy/dsum 是否补零、dx 申请依据、两槽句柄复用与梯度累加。真实执行、精度和性能验证仍需同参参考，本卡未执行。

## Evidence

- [AddLayerNormKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddLayerNormKernelNpuOpApi.cpp)（primary）：1–73；完整本地小文件。
- [AddLayerNormBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddLayerNormBackwardKernelNpuOpApi.cpp)（implementation）：1–66；完整本地小文件。
- [AddLayerNormNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddLayerNormNpu.cpp)（implementation）：1–67；完整本地小文件。
- [AddLayerNormBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddLayerNormBackwardKernelNpu.cpp)（implementation）：1–66；完整本地小文件。
- [test_npu_add_layer_norm.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_add_layer_norm.py)（example）：1–90；完整本地小文件。
- [test_npu_add_layer_norm_backward.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_add_layer_norm_backward.py)（example）：1–100；完整本地小文件。
- [_meta_registrations.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：2683–2693；仅所列完整Meta或Schema/derivative块。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5828–5834；仅所列完整Meta或Schema/derivative块。
- [derivatives.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）：75–78；仅所列完整Meta或Schema/derivative块。
- [AddLayerNormKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddLayerNormKernelNpuOpApi.cpp)（implementation）：1–55；完整本地小文件。
- [AddLayerNormBackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddLayerNormBackwardKernelNpuOpApi.cpp)（implementation）：1–47；完整本地小文件。
- [AddLayerNormNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AddLayerNormNpu.cpp)（implementation）：1–58；完整本地小文件。
- [AddLayerNormBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AddLayerNormBackwardKernelNpu.cpp)（implementation）：1–62；完整本地小文件。
- [test_npu_add_layer_norm.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_add_layer_norm.py)（example）：1–90；完整本地小文件。
- [test_npu_add_layer_norm_backward.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_add_layer_norm_backward.py)（example）：1–100；完整本地小文件。
- [_meta_registrations.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）：2347–2357；仅所列完整Meta或Schema/derivative块。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5588–5594；仅所列完整Meta或Schema/derivative块。
- [derivatives.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）：70–73；仅所列完整Meta或Schema/derivative块。
