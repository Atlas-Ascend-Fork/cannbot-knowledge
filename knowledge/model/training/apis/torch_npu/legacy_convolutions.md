---
type: API
title: 旧卷积包装：参数顺序、权重布局与functional迁移
description: 覆盖2D/3D卷积及转置卷积，强调低层声明无默认值和转置参数重排；含未融合/slow conv 13 名注册面；含 slow conv 两支专用 aclops backward 内部：三命令分解、output_mask 门控不对称与 BiasAddGrad 输入字面。并含npu_conv_transpose2d/convolution_transpose 与 3D 反向的 aclops 实现层。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_conv2d.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_conv3d.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_conv3d.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_conv3d.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_conv_transpose2d.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_convolution.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_convolution_transpose.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NnpackSpatialConvolutionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NnpackSpatialConvolutionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/NnpackSpatialConvolutionKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/NnpackSpatialConvolutionKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvtbcKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConvtbcKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvTbcBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConvTbcBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SlowConvDilated2DKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SlowConvDilated2DKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SlowConvTranspose2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SlowConvTranspose2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Conv3dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Conv3dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConvolutionKernelNpuOpApi.cpp
  role: implementation
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SlowConvTranspose2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SlowConvDilated2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SlowConvTranspose2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SlowConvDilated2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvTranspose2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConvTranspose2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvTranspose2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConvTranspose2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Conv3dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Conv3dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvTranspose3dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConvTranspose3dBackwardKernelNpu.cpp
  role: implementation
created_at: '2026-11-09T20:27:55Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# 旧卷积包装：参数顺序、权重布局与functional迁移

## 固定版本及消费边界

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda实际收录的中英文页。发布对应ascend_26_0_pt28；TorchNPU实现发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b、独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf分别消费，不将两个main当配套发行。

默认平台A2/A3仅指各页所列范围；主线新增产品或参数另明确版本，旧Atlas不自动映射新型号。beta及计划废弃是上游接口状态，知识卡stable不表示推荐新模型使用或运行verified。本卡未做上游导入、模型加载、设备执行、反向或性能实验；注册all_version不是全硬件保证，底层Kernel实现不在本卡结论范围。


## 普通卷积

npu_conv2d、npu_conv3d和按维数选择的npu_convolution均计划废弃，分别指向F.conv2d/F.conv3d。输入为(N,Cin,H,W)或(N,Cin,T,H,W)，weight为(Cout,Cin/groups,kH,kW)或其3D形式，bias可为None、非空时(Cout)。groups需满足通道分组关系。

固定声明顺序为input,weight,bias,stride,padding,dilation,groups；bias类型可空不等于可以省略位置参数，两个schema并未给这些参数默认值。主线conv3d文字提padding默认1，不能据此构造省略padding的旧入口调用；迁移到functional后应显式核对每个参数，不继承不同接口的默认值。

## 转置卷积

npu_conv_transpose2d与npu_convolution_transpose对应2D或2D/3D转置卷积，weight通道顺序变为(Cin,Cout/groups,...)。旧入口顺序是input,weight,bias,padding,output_padding,stride,dilation,groups，不能原样位置传给functional。

padding对应dilation*(kernel_size-1)-padding的隐式两侧关系，output_padding增大输出一侧的尺寸；不是给结果任意添加零元素的通用pad接口。迁移按实际维数选择F.conv_transpose2d/F.conv_transpose3d并使用关键字核对shape、groups、stride、dilation和输出尺寸。

本卡只核对文档与注册声明，未审完所有卷积算法选择、workspace或反向底层实现；不由旧包装名推断更低内存或更快性能。发布页在主线缺失不证明接口删除。

## npu_conv_transpose2d / npu_convolution_transpose 与 3D 反向的 aclops 实现层

上文仅核对 slow_conv_transpose 族与文档页；本节补 npu_* 转置卷积/3D 反向四个 aclops 文件（主线与发布两版本 全部去空白等价，本卡 `tr -d` 比对）。

`ConvTranspose2dKernelNpu.cpp`（75 行）：`npu_conv_transpose2d` 前向发 ACE `Conv2DTranspose`——**首个输入是输出尺寸向量（at::kInt）**，随后 input("x")/weight("filter")/可选 bias；`pads`/`output_padding` 扩成四元（output_padding 前补 0,0）、`strides`/`dilations` 四元（前补 1,1）、`data_format` 固定 NCHW。

`ConvTranspose2dBackwardKernelNpu.cpp`（400 行）：input 梯度发 ACE `Conv2D`（转置卷积的反向输入梯度等价一次正向卷积，grad 作为卷积输入）、weight 梯度发 `Conv2DBackpropFilter`、bias 梯度按 grad 沿 N,H,W 求和；`npu_conv_transpose2d_backward` 组合三者，`npu_convolution_transpose_backward` 对 3D 委托 `npu_conv_transpose2d_backward`；`npu_convolution_transpose` 按输出 dim 选 2D 路径或 `convolution_transpose3d_out_npu_nocheck`（ACE `Conv3DTranspose`，sizeVec 以 at::kInt 首输入）。

`Conv3dBackwardKernelNpu.cpp`（134 行）：`npu_conv3d_backward` 按 `grad_input_mask` 分配后三段——grad_input 以 `ACL_FORMAT_NDC1HWC0` 请求并发 `Conv3DBackpropInput`，grad_weight 发 `Conv3DBackpropFilter`，grad_bias 按 mask 求和；stride/padding/dilation 各自 TORCH_CHECK ≥3 元。`ConvTranspose3dBackwardKernelNpu.cpp`（181 行）：input 梯度发 `Conv3D`、weight 梯度发 `Conv3DBackpropFilter`，输入/grad 维数校验同型。

消费面：torchair `convolution.py` converter 与发布 torch_npu `onnx/wrapper_ops_combined.py` 映射 npu_conv2d 族；API 组合迁移见上文文档页小节。设备侧各 ACE 命令数值语义与 NDC1HWC0/NCHW 转换成本未测，本节为主线与发布两版本 静态阅读。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_conv2d.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_conv3d.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_conv3d.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_conv3d.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_conv_transpose2d.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_convolution.md)（primary）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_convolution_transpose.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [NnpackSpatialConvolutionKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NnpackSpatialConvolutionKernelNpuOpApi.cpp)（implementation）：1–57；完整本地文件。
- [NnpackSpatialConvolutionKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NnpackSpatialConvolutionKernelNpuOpApi.cpp)（implementation）：1–57；完整本地文件，主线与发布两版本 字节相同。
- [NnpackSpatialConvolutionKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/NnpackSpatialConvolutionKernelNpu.cpp)（implementation）：1–73；完整本地文件。
- [NnpackSpatialConvolutionKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/NnpackSpatialConvolutionKernelNpu.cpp)（implementation）：1–73；完整本地文件，与主线去空白字符流相同。
- [ConvtbcKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvtbcKernelNpu.cpp)（implementation）：1–74；完整本地文件。
- [ConvtbcKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConvtbcKernelNpu.cpp)（implementation）：1–74；完整本地文件，与主线去空白字符流相同。
- [ConvTbcBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvTbcBackwardKernelNpu.cpp)（implementation）：1–56；完整本地文件。
- [ConvTbcBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConvTbcBackwardKernelNpu.cpp)（implementation）：1–56；完整本地文件，与主线去空白字符流相同。
- [SlowConvDilated2DKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SlowConvDilated2DKernelNpu.cpp)（implementation）：1–79；完整本地文件。
- [SlowConvDilated2DKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SlowConvDilated2DKernelNpu.cpp)（implementation）：1–79；完整本地文件，与主线去空白字符流相同。
- [SlowConvTranspose2dKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SlowConvTranspose2dKernelNpu.cpp)（implementation）：135–249；仅所列函数段（out_nocheck 与两个公开入口），1–134 辅助未核对。
- [SlowConvTranspose2dKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SlowConvTranspose2dKernelNpu.cpp)（implementation）：1–188；整文件去空白字符流与主线相同，无独立逐行读。
- [Conv3dKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Conv3dKernelNpu.cpp)（implementation）：88–224；slow_conv3d 段定向读，文件其余部分未核对。
- [Conv3dKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Conv3dKernelNpu.cpp)（implementation）：1–224；主线与发布两版本 字节相同。
- [ConvolutionKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConvolutionKernelNpuOpApi.cpp)（implementation）：80–179、292–368、415–544、546–823；仅所列helper/函数段。
- [ConvolutionKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ConvolutionKernelNpuOpApi.cpp)（implementation）：296–505；与主线对应函数段去空白字符流相同，仅行号不同。
- [ConvolutionBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConvolutionBackwardKernelNpuOpApi.cpp)（implementation）：80–168、190–239、241–417、495–564；仅所列helper/函数段。
- [ConvolutionBackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ConvolutionBackwardKernelNpuOpApi.cpp)（implementation）：176–289、291–362；对应函数段，与主线同构（含 CANN≥8.5.1 按 output_mask 选择性分配分支）。
- [ConvolutionKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvolutionKernelNpu.cpp)（implementation）：676–712；仅 _slow_conv2d 三个入口。
- [ConvolutionKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConvolutionKernelNpu.cpp)（implementation）：579–612、1088–1112；同名 _slow_conv2d 入口 rg 定位存在（双版本拷贝），未独立阅读。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–118；DO_COMPATIBILITY 宏定义（符号探测+ACLNN-only 门）。
- [op_api_common.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–113；对应 DO_COMPATIBILITY 宏，与主线同构（仅排版不同）。


- [ConvTranspose2dKernelNpu.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvTranspose2dKernelNpu.cpp)（implementation）：全文 75 行；发布去空白等价。
- [ConvTranspose2dBackwardKernelNpu.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvTranspose2dBackwardKernelNpu.cpp)（implementation）：全文 400 行（三 nocheck 子函数+组合入口+npu_convolution_transpose 族）；发布去空白等价。
- [Conv3dBackwardKernelNpu.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Conv3dBackwardKernelNpu.cpp)（implementation）：全文 134 行；发布去空白等价。
- [ConvTranspose3dBackwardKernelNpu.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConvTranspose3dBackwardKernelNpu.cpp)（implementation）：全文 181 行；发布去空白等价。
## 未融合/slow conv 注册面

13 个未融合/slow conv schema（主线与发布两版本 各 13 条登记）一次核对。除 conv_tbc 主线 op_api 由 gen_opapi 生成直发 aclnnConvTbc（yaml 主线 1804–1813：out size 公式、new_params 注入 cube_math_type=IsAllowConvHF32、发布 1745–1754 同构）外，其余入口都在共享包装文件里，核心形态是「DO_COMPATIBILITY(aclnnConvolution/aclnnConvolutionBackward → acl_op 通用实现) + 共享执行器」：

| 入口（登记，主线/发布行段） | 分派要点 |
| --- | --- |
| _nnpack_spatial_convolution（acl_op+op_api [v2.1,newest]，687–689/659–661） | opapi 全 57 行：标量 padding/stride 广播成四元 pads {p0,p0,p1,p1} 与二元 strides，dilations={1,1}、output_padding={0,0}、groups=1、transposed=false 固定，cube_math_type 按 IsAllowConvHF32，无 DO_COMPATIBILITY，单次 aclnnConvolution；aclops 旧路径 73 行全文已读：ACE Conv2D（strides {1,1,s0,s1}、NCHW、half 输出 NC1HWC0 否则 ND） |
| slow_conv_dilated2d(_backward)（前向 acl_op+op_api [v2.1,newest]，4775–4777/4621–4623；_backward acl_op+op_api all_version，5821–5823/5581–5583） | opapi：transposed=false、output_padding={0,0}、groups=1，DO_COMPATIBILITY→acl_op::_convolution，再共享执行器；aclops 79 行全文已读：dilation/padding/stride ≥2 维、stride 非零、padding 非负四组检查，ACE Conv2D（pads {p0,p0,p1,p1}、dilations {1,1,d0,d1}、groups 1、NCHW）；backward 的 opapi DO_COMPATIBILITY 回退目标是**通用** acl_op::convolution_backward |
| _slow_conv2d_forward(.output)/_backward.output_mask（acl_op+op_api all_version，760–762/735–737、4771–4773/4617–4619、756–758/731–733） | opapi 先把传入 weight **原地 resize_** 成 {s1,s2,kH,kW}（s2=其余维乘积/(kH·kW)，kernel 非零 TORCH_CHECK），DO_COMPATIBILITY→acl_op::_convolution/_slow_conv2d_forward_out；out 变体在允许内部格式或 JIT 时直接走 acl_op，否则 aclnnConvolution(+cube_math_type)；aclops 落点 npu_convolution/npu_conv2d_out/npu_convolution_backward（dilation {1,1}、groups 1）；opapi backward 先存原始 weight 形状，EXEC 后 gradWeight.resize_ 回原形状 |
| slow_conv_transpose2d(.out/_backward)（acl_op+op_api [v2.1,newest]，4763–4769/4609–4615；_backward custom 7126/6916） | transposed=true/groups=1；DO_COMPATIBILITY→acl_op::_convolution；out 变体 expand 四组参数、check_tensor，允许内部格式或 JIT 时改走 acl_op::_convolution（注释自述 groups>1 与 3D 场景 binary 不支持、暂走 path 3），dim∉{1,2,3} 返回空 Tensor，否则 aclnnConvolution(+cube_math_type)；aclops SlowConvTranspose2d 主入口段（135–249）：shape_check 要求 padding/stride/output_padding 恰 2 元，ACE Conv2DTranspose（首个输入是 out 尺寸向量、pads/output_padding 四元、NCHW、half→NC1HWC0） |
| slow_conv3d_forward(.output)（公共 schema **仅 acl_op 登记**，4779–4784/4625–4630） | 注册面与定义面分开：主线与发布两版本 公共 schema 均只有 acl_op 行；ConvolutionKernelNpuOpApi.cpp 内存在同名 opapi C++ 定义，但定义存在不证明公共入口分派到它（可达性需读调用链才能证明），以下为该定义内容：空通道输入走 make_empty_channel_output；310P1≤SoC<910B1 直接 acl_op::slow_conv3d_forward(_out)（不经 aclnn）；其余把 weight resize_ 成 5D、kernel>0 检查、DO_COMPATIBILITY→acl_op::_convolution、共享执行器；aclops Conv3d（88–224）：≥5D、stride/padding ≥3 元、stride 非零、Do/Ho/Wo>0 检查，filter=weight.to(input.dtype) 权重向输入 dtype 对齐，ACE Conv3D（strides {1,1,s0,s1,s2}、pads 6 元、dilations 全 1、NCDHW），forward 输出 NDC1HWC0 |
| conv_tbc(_backward)（acl_op+op_api all_version，1804–1817/1745–1758） | 主线 op_api gen_opapi 直发 aclnnConvTbc；aclops Convtbc 74 行全文已读：self/weight 3D、bias 1D、通道匹配、bias 尺寸匹配五道 TORCH_CHECK + W>0 检查，self/weight transpose+unsqueeze 成 NCHW 4D，ACE Conv2D（pads {0,0,pad,pad}、strides/dilations 全 1），输出 {N,C,1,W} squeeze/transpose 回 tbc 布局；aclops conv_tbc_backward 56 行全文已读：三输入 permute 后 npu_conv2d_backward（stride {1,1}、pad {0,pad}、dilation {1,1}、groups 1），三路梯度 permute 回 |

共享执行器 _calc_convolution（主线 opapi ConvolutionKernelNpuOpApi.cpp 292–368）的实际顺序：允许内部格式或 JIT、且 dim≠3、且 CheckCompatibleImpl 为假时整段走 acl_op::_convolution；dim∉{1,2,3} 返回空 Tensor；否则 expand_dim 四组参数→conv_npu_output_size→apply_tensor_without_format→aclnnConvolution(+cube_math_type)；dim==2 且输入 3D 时把输出与输入 resize_ 掉批维。反向共享执行器 _calc_convolution_backward 同构，主线与发布两版本 各有一份 CANN≥8.5.1 分支按 output_mask 选择性分配三个梯度（主线 529–544、发布 337–352）。主线与发布两版本 上述函数块去空白字符流逐一相同（仅行号不同）；aclops Conv3d 主线与发布两版本 字节相同；NnpackSpatialConvolution opapi 主线与发布两版本 字节相同。

结构性结论：这些入口都是显式命名的 entry 包装，把通用 convolution 分派的参数固定化（groups=1、dilation/output_padding 固定或 weight 改形），**不是独立的慢速 kernel**；已证明的只是包装与 DO_COMPATIBILITY 分派本身，目标与上文卷积核心组共享执行边界（acl_op::_convolution/npu_convolution 族或 aclnnConvolution）。本卡未核对任何调用方或融合可用性门槛，不据此宣称存在『融合 conv 不可用即回退到这些入口』的链路。DO_COMPATIBILITY 的实际语义是静态符号+模式门（op_api_common.h 主线 94–118/发布 96–113）：探测 aclnn 符号与其 GetWorkspaceSize，任一缺失且 ACLNN-only 模式下直接 TORCH_CHECK 抛错、不回退，仅非 ACLNN-only 模式才回退 acl_op 目标，不存在对通用 SDK 失败或融合不可用的重试。13 个 schema 的注册面核对不等于 slow conv 相关优化事实全部核对：专用 aclops backward 文件 SlowConvTranspose2dBackward（188 行）/SlowConvDilated2dBackward（184 行）实现同名 acl_op 符号、由 dispatcher 按 backend 选择而非 DO_COMPATIBILITY 内联调用，本卡未核对其内部。SlowConvTranspose2d 的 1–134 行辅助（输出尺寸推导细节）、npu_conv2d_backward/npu_convolution 内部（属卷积核心组既有边界）、设备侧 Conv2D/Conv2DTranspose/Conv3D/aclnnConvolution/aclnnConvTbc/aclnnConvTbcBackward 语义均未核对；未执行任何前向/反向/数值验证。

## slow conv 两支专用 aclops backward 的内部

上文注册面一节把 `SlowConvTranspose2dBackward`（主线1–188、发布1–150，去空白字符流相同）与 `SlowConvDilated2dBackward`（主线1–184、发布1–148，去空白字符流相同）两个 dispatcher 级 acl_op 符号留为未核对；本节核对其内部。两文件实现同名 schema 的 backend 选择路径（dispatcher 按 backend 路由进入），与上文 opapi 手写层的 `DO_COMPATIBILITY` 内联回退目标（通用 `acl_op::_convolution`/`convolution_backward`）是不同入口，行为不互推。本节只读源码，未运行任何前向/反向或数值验证。

| 入口 | 实际门槛→动作 | 失败/边界 |
| --- | --- | --- |
| slow_conv_transpose2d_backward（主线147–187） | 三子命令分解：**dgrad 用前向 ACE 命令 `Conv2D`**——grad_output 作 `x`、weight 作 `filter`（转置卷积的输入梯度=对 grad 的普通卷积），strides `{1,1,s0,s1}`、pads `{p0,p0,p1,p1}`、dilations `{1,1,d0,d1}`、groups=1、data_format NCHW；wgrad 用 `Conv2DBackpropFilter`（`dim_list=weight.sizes()` 以 at::kInt 设备输入、self 作 `out_backprop`）；**bias 梯度用 `acl_op::sum_out`**——grad_output.contiguous().view({N,C,-1}) 后按 dims {0,2} 归约，是归约命令而非卷积反传命令。三道 TORCH_CHECK（stride/padding/dilation `size() >= 2`，消息均写"slow_conv_transpose2d_backward expected dilation greater than or equal to 2D, but input stride/padding has sizes ..."——stride/padding 报错沿用 dilation 措辞，按原文记录）。分配：grad_input 格式跟 self（Half→NC1HWC0 否则 ND）、尺寸 slow_conv_transpose2d_backward_npu_output_size；**grad_weight 强制 kFloat dtype**（格式跟 weight）；grad_bias {grad_output.size(1)} NCHW | **output_mask 只门控申请、不门控执行**：mask=false 的梯度是默认构造的未定义 Tensor，仍被传入三条子命令作 Output（命令层对未定义输出的处理未核对，不外推为必然崩溃或成功）；grad_weight 的 Float 强制与 out 检查面（上文 opapi 层按 self）不对称 |
| slow_conv_dilated2d_backward（主线155–183） | 三子命令：dgrad 用 `Conv2DBackpropInput`（`dim_list=self.sizes()` Int 设备输入、weight 作 filter、grad_output 作 out_backprop）；wgrad 用 `Conv2DBackpropFilter`（self 作 `x`、`dim_list=weight.sizes()`）；bias 梯度用 `BiasAddGrad` 且 **Input(self)**——喂给命令的是前向输入而非 grad_output（字面按原文记录，不判意图）。检查面：kernel_size/stride/dilation/padding 均 `size() == 2` 恰等（与 transpose 的 `>= 2` 不对称）+ kernel/stride/dilation `all_positive`（padding 不在正数检查）。分配：三个梯度全部 `apply_tensor(grad_output, …)`（dtype/options 跟 grad_output；grad_input=self.sizes、grad_weight=weight.sizes、grad_bias=weight.size(0)） | **output_mask 同时门控申请与执行**（mask=false 直接跳过对应子命令，与 transpose 不对称）；grad_weight 不强制 Float（与 transpose 不对称）；BiasAddGrad 输入字面差异按实际运行核对，不据此推上游 bug 或正确性 |

跨行两条：其一，**同名“backward”两支的三命令组合不同**——transpose 用前向 Conv2D 求 dgrad（数学上转置卷积反向=卷积），dilated 用 BackpropInput；bias 梯度一支走 sum_out 归约、一支走 BiasAddGrad，命令数与中间申请（contiguous+view、dim_list 设备输入）按入口分别核对。其二，**output_mask 语义不对称**——dilated 按 mask 跳过命令，transpose 恒执行三条；用部分 mask（如仅求 grad_input）时两入口的设备命令数不同，不能按 ATen 语义推 mask 一定省算。

### slow conv backward 补充证据

- [SlowConvTranspose2dBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SlowConvTranspose2dBackwardKernelNpu.cpp)（primary）：25–187；grad_output/weight/bias 三个 nocheck 子函数、组合 nocheck 与公开入口完整函数体。
- [SlowConvTranspose2dBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SlowConvTranspose2dBackwardKernelNpu.cpp)（implementation）：完整本地文件（150 行），与主线去空白字符流相同（仅排版）。
- [SlowConvDilated2dBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SlowConvDilated2dBackwardKernelNpu.cpp)（primary）：25–183；input/weight/bias 三个 nocheck 子函数、组合 nocheck 与公开入口完整函数体。
- [SlowConvDilated2dBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SlowConvDilated2dBackwardKernelNpu.cpp)（implementation）：完整本地文件（148 行），与主线去空白字符流相同（仅排版）。
- 边界：Conv2D/Conv2DBackpropFilter/Conv2DBackpropInput/BiasAddGrad/sum_out 设备侧语义未核对；`slow_conv_transpose2d_backward_npu_output_size` helper 未核对（分配尺寸来源）；上文注册面一节其余未确认边界（npu_convolution 族内部、aclnnConvolution 设备侧）不变。
- 负向证据：canonical 与全部 batch*/staged rg `SlowConvTranspose2dBackwardKernelNpu|SlowConvDilated2dBackwardKernelNpu` 零命中——本节为两文件首个实现级小节（上文注册面一节仅声明其存在与 dispatcher 选择关系）。
