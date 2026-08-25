---
type: API
title: Conv3DBackpropInput
description: 提供实现3D卷积反向运算的高阶API，求解反向传播误差，也可用于实现转置卷积Conv3DTranspose算子。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Kernel/Conv3DBackpropInput_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# Conv3DBackpropInput

Ascend C提供一组Conv3DBackpropInput高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。转置卷积Conv3DTranspose与Conv3DBackpropInput具有相同的数学过程，因此用户也可以使用Conv3DBackpropInput高阶API实现转置卷积算子。卷积的正反向传播如图1卷积层的前后向传播示意图，反向传播误差计算如图2 反向传播误差计算示意图。 Conv3DBackpropInput 以 GradOutput 和转置后的 Weight 为输入，计算特征矩阵的反向传播误差 GradInput。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput Tiling侧接口](../conv3_d_backprop_input_tiling/conv3_d_backprop_input_tiling.md)（`related`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；Conv3DBackpropInput Tiling侧接口正文说明“提供Conv3D反向卷积输入梯度的Host侧Tiling接口，包含TConv3DBackpropInputTiling结构体、GetTiling及形状与类型设置方法”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [SetOutputPadding](../conv3_d_backprop_input_tiling/set_output_padding.md)（`related`）：SetOutputPadding 与《Conv3DBackpropInput》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [卷积计算Init](init.md)（`related`）：“卷积计算Init”定义：Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。；“Conv3DBackpropInput”定义：提供实现3D卷积反向运算的高阶API，求解反向传播误差，也可用于实现转置卷积Conv3DTranspose算子。。实质衔接：Init 消费 Tiling 侧生成的结构并划分资源，是 Conv3DBackpropInput 使用流程的起点；计算完成还必须 End 释放事件和临时内存。
- [Conv3DBackpropInput Kernel侧接口](conv3_d_backprop_input_kernel.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；Conv3DBackpropInput Kernel侧接口正文说明“提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [Conv3DBackpropInputTiling](../conv3_d_backprop_input_tiling/conv3_d_backprop_input_tiling_usage.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；Conv3DBackpropInputTiling正文说明“提供获取Conv3DBackpropInput Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [GetTensorC](get_tensor_c.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；GetTensorC正文说明“在完成Iterate操作后调用本接口，获取结果矩阵块，完成数据从L0C到GM的搬运。此接口与Iterate接口配合使用，用于在Iterate执行迭代计算后，获取结果矩阵”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [Iterate（卷积计算）](iterate.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；Iterate（卷积计算）正文说明“每次调用Iterate时，会计算出一个baseM \ baseN的结果矩阵，并将该结果写入L0C Buffer。接口内部会维护迭代进度，每次调用后，矩阵的起始地址将进行偏移。如果传入的数据未对齐存在尾块，则在最后一次迭代中输出尾块的计算结果。本接口需与GetTensorC接口配合”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [SetGradOutput](set_grad_output.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；SetGradOutput正文说明“设置卷积反向计算的输入矩阵GradOutput”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [SetSingleShape](set_single_shape.md)（`same_topic`）：SetSingleShape：SetSingleShape 写入 Conv3DBackpropInput 单核 M/K/N，随后由同一对象的 Init/Iterate 流程消费；用法卡给出它在完整调用序列中的位置。 目标卡《Conv3DBackpropInput》补充：提供实现3D卷积反向运算的高阶API，求解反向传播误差，也可用于实现转置卷积Conv3DTranspose算子。
- [SetStartPosition](set_start_position.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；SetStartPosition正文说明“设置单核上GradOutput载入数据的起始位置”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [SetWeight](set_weight.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；SetWeight正文说明“设置卷积反向计算的输入矩阵Weight”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [卷积计算End](end.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；卷积计算End正文说明“在Conv3DBackpropInput卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
<!-- cannbot:related:end -->
