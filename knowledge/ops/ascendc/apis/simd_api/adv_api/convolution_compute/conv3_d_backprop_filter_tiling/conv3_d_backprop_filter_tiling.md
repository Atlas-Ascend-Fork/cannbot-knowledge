---
type: API
title: Conv3DBackpropFilter Tiling侧接口
description: 提供Conv3D反向卷积滤波器梯度的Host侧Tiling接口，包含TConv3DBpFilterTiling结构体、GetTiling及形状与类型设置方法。
tags: [task.lookup, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/Conv3DBackpropFilter_Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3DBackpropFilter Tiling侧接口

提供 Conv3D 反向滤波器梯度的 Host 侧 Tiling 接口，通过 TConv3DBpFilterTiling 结构体承载切分参数。
核心方法 GetTiling 获取最终 Tiling 数据；SetWeightShape/SetInputShape/SetGradOutputShape 设置各张量形状，SetWeightType/SetInputType/SetGradOutputType 设置数据类型。
另提供 SetPadding/SetStride/SetDilation 设置卷积超参数，使用前需通过构造函数初始化 Tiling 对象。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropFilter使用说明](../conv3_d_backprop_filter_kernel/conv3_d_backprop_filter_usage.md)（`related`）：Conv3DBackpropFilter Tiling侧接口 与《Conv3DBackpropFilter使用说明》的实质衔接是：该 Host tiling 总览把构造、TConv3DBpFilterTiling、GetTiling 与 kernel/使用流程串成同一反向滤波器梯度契约；未为每个 setter 重复生成成员边。
- [GetTiling](get_tiling.md)（`related`）：Conv3DBackpropFilter Tiling侧接口 与《GetTiling》的实质衔接是：该 Host tiling 总览把构造、TConv3DBpFilterTiling、GetTiling 与 kernel/使用流程串成同一反向滤波器梯度契约；未为每个 setter 重复生成成员边。
- [Conv3DBackpropFilter Kernel侧接口](../conv3_d_backprop_filter_kernel/conv3_d_backprop_filter_kernel.md)（`same_topic`）：Host Tiling 卡计算并序列化 Conv3DBackpropFilter 的分块参数，Kernel 卡按同一 BPF 算子合同解析这些参数并执行反向滤波计算；两者共同构成同一算子的 Host/Device 接口。
- [Conv3DBackpropFilter Tiling构造函数](conv3_d_backprop_filter_tiling_constructor.md)（`same_topic`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《Conv3DBackpropFilter Tiling侧接口》说明提供Conv3D反向卷积滤波器梯度的Host侧Tiling接口，包含TConv3DBpFilterTiling结构体、GetTiling及形状与类型设置方法。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [SetDilation](set_dilation.md)（`same_topic`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《Conv3DBackpropFilter Tiling侧接口》说明提供Conv3D反向卷积滤波器梯度的Host侧Tiling接口，包含TConv3DBpFilterTiling结构体、GetTiling及形状与类型设置方法。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
- [SetGradOutputType](set_grad_output_type.md)（`same_topic`）：SetGradOutputType 与《Conv3DBackpropFilter Tiling侧接口》的实质衔接是：该 setter 把 GradOutput 的 GM/NDC1HWC0 与 FP16/BF16 类型写入 BackpropFilter Host tiling；形状 setter 补齐同一张量描述，GetTiling 生成结构后由 kernel Init/SetGradOutput 按同一契约消费。
- [SetStride](set_stride.md)（`same_topic`）：Conv3DBackpropFilter Tiling 总览把 SetStride 列为 Host 侧构造反向滤波 Tiling 参数的设置步骤。
- [SetWeightShape](set_weight_shape.md)（`same_topic`）：Conv3DBackpropFilter Tiling 入口页把 SetWeightShape 列为设置张量形状的核心方法，并说明其结果参与 Host 侧切分。
- [TConv3DBpFilterTiling结构体](t_conv3_d_bp_filter_tiling_struct.md)（`same_topic`）：Conv3DBackpropFilter Tiling侧接口 与《TConv3DBpFilterTiling结构体》的实质衔接是：该 Host tiling 总览把构造、TConv3DBpFilterTiling、GetTiling 与 kernel/使用流程串成同一反向滤波器梯度契约；未为每个 setter 重复生成成员边。
<!-- cannbot:related:end -->
