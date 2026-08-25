---
type: Guide
title: 开启Tiling下沉
description: 将Tiling计算下沉至Device侧AI CPU执行，减少Host-Device交互开销，实现全程Device侧高效计算。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/operator_graph_development/enable_tiling_sink.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 开启Tiling下沉

在静态图模式下，可以通过整图下沉优化调度性能。将完整的计算图一次性下发至Device侧，后续执行则无需Host参与，由Device自主完成计算，从而减少Host-Device交互开销，提升执行效率。部分算子的Tiling计算依赖运行时输入的具体数值（Tiling值依赖），需在执行时动态计算Tiling参数。针对该场景，可采用Tiling下沉优化方案：将Tiling计算下沉至Device侧的AI CPU上执行，从而实现计算全程在Device侧高效完成。
自定义算子开启Tiling下沉的步骤如下，完整样例请参考Tiling下沉算子样例。
Tiling下沉场景下，算子工程的op_host目录结构如下，Tiling实现文件需单独放在一个cpp文件中，示例中为add_custom_tiling_sink_tiling.cpp。
以AddCustom算子为例，讲解关键代码文件的具体实现方法如下：
-   在add_custom_tiling_sink_tiling.h中进行Tiling实现函数的声明
-   算子原型定义、InferShape、InferDataType实现文件add_custom_tiling_sink.cpp，需包含add_custom_tiling_sink_tiling.h，进行Tiling函数和算子原型定义的关联。
Tiling下沉仅适用于存在Tiling值依赖（即当InferShape不依赖输入值，仅Tiling计算需要输入值）且算子输入为非Const类型的场景，本示例中的输入y通过ValueDepend配置了非Const类型的Tiling值依赖。
-   Tiling函数的实现文件add_custom_tiling_sink_tiling.cpp
-   Tiling函数中通过判断值依赖InputTensor即输入y的数据指针是否为空指针来确认当前是否处于编译期。Tiling下沉场景，编译期需要为算子分配内存，包括其所需的workspace。为了保证运行时的高效性，编译期应根据算子的执行需求，合理设置所需的workspace最大值，以避免内存不足或浪费。AddCustomTilingSink样例不需要用户workspace，不涉及设置，此处设置为固定值仅作为示例。
-   完成下沉Tiling函数注册：包含device_op_impl_registry.h头文件，使用宏DEVICE_IMPL_OP_OPTILING进行注册。
-   算子核函数实现
当前Tiling下沉仅支持融合算子，为了模拟融合算子场景，通过KERNEL_TASK_TYPE_DEFAULT接口强制指定算子在AIC、AIV混合场景运行。
-   修改op_host目录下的编译脚本CMakeLists.txt，添加Tiling下沉编译命令。具体代码如下所示：
