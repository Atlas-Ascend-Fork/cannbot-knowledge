---
type: Guide
title: GE动态档位执行器：维度刷新、Host暂存与输出容量
description: 解释MutiGear如何复用静态分配与图实例，核对分档维度、私有格式、Host同步复制及实际输出shape和缓冲容量的区别。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/muti_gear_npu_graph_executor.cpp
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/muti_gear_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/muti_gear_npu_graph_executor.h
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_executor.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/static_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_utils.cpp
  role: implementation
created_at: '2026-11-10T12:00:58Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE动态档位执行器：维度刷新、Host暂存与输出容量

## 固定版本与路径

定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的MutiGear执行器和继承调用点。下述档位输入与输出主体在两版一致；主线额外包含disable_external_mem_base、首次FastLoad后的deadlock check，以及可刷新feature指针的非空条件，不能回推发布版。

仅有源码静态证据，没有执行GE、编译、设备、内存或并发实验；整卡平台未知，保持draft与空平台。公开档位值域、zip/product组合和0/1限制仍见[set_dim_gears](../../../apis/torchair/set_dim_gears.md)，本卡不重复这些接口规则。

创建器先看编译summary.IsStatic；静态summary同时存在ge.dynamicDims、ge.inputShape和ge.dynamicNodeType三个选项才选MutiGear，否则选普通Static。非静态summary使用Dynamic。因此Python dynamic=True、GE动态档位和C++ DynamicNpuGraphExecutor不是同一个分类。

## 档位维度从hint shape提取

首次ParseInputGears按graph_data.inputs_shape收集值为-1的维度索引；后续非frozen设备输入只更新这些位置，再更新数据地址。ge::Tensor使用SetShapeDim，gert::Tensor同时更新origin/storage对应维度；没有在这里重新推导整张图或逐项检验所有非分档维度。

inputs_shape为空或记录了未知rank标记时，局部回退按当前rank填入多个-1。UpdateSpecificDims又把这些值直接作为维度索引使用，本层没有将其展开为0到rank-1。不能把这个回退概括为“任意未知rank都能正确更新全部维度”；本卡未运行该分支，也未证明某个具体模型会走到它。接入时保留正确的hint shape和已知rank。

## 分档设备输入与Host输入条件不同

首次设备输入只要有分档维度，就要求为base format；未分档设备项不受同一个条件限制。后续更新不再重复这项格式检查。frozen项在更新循环开头直接跳过，shape或地址变化不能依赖该分支自动发现；标为固定地址的输入应满足独立合同。

Host输入要求其分档维度列表为空；首次仍无条件建立NPU暂存，保存源/目的字节数并在非空时H2D，以后继续用这份固定字节数复制。这个路径没有普通主线Static执行器的直接Host绑定分支，也没有动态执行器按shape重建Host暂存的逻辑。

H2DMemcpy先同步流再进行同步拷贝，所以即使辅助Host Tensor自身不分档，也可能带来每次调用的同步和搬运。Host输入尺寸、dtype和存储需要保持合同；不能因某个设备输入支持多档，就让所有Host辅助输入也自由变shape。

## 输出shape回填不等于按实际档位缩小分配

MutiGear继承StaticNpuGraphExecutor的AssembleOutputs：首次按编译summary的输出shape/type计算output_size_，未指定输出Tensor时每次请求相应DataPtr。运行后RefreshOutputShape从GE描述回填output_shapes_，再用该实际shape、原output_size_和DataPtr封装Tensor。

本地回填没有重算output_size_。因此实际Tensor shape变小不独立证明缓冲分配字节数也按同一比例变小；反过来也不能未经GE合同确认就把summary shape一概称为所有档位的最大值。应同时记录summary输出、实际输出shape、申请字节数、Storage容量和仍存活的结果。

GetShapeFromGeTensor要求预留shape向量长度与GE返回rank一致，gert版本读取storage shape。这是固定rank下刷新维度的路径，不是任意输出rank变化或任意内部格式输出都被支持的证明。

## 预分配输出不能套用普通Static的CPU回拷

MutiGear也调用继承的AssembleOutputs，但自己的返回循环对于已给定Tensor直接返回它，未执行普通Static Run中的D2HMemcpy。非空CPU预分配输出在基类可能获得设备临时缓冲，不能据此认定本子类会把结果回拷CPU。这个静态路径差异尚未做设备复现；调用方应验证或避开未经确认的CPU预分配组合。

未指定输出时，返回Tensor按实际shape封装设备缓冲，没有在本循环额外复制结果。输出别名和所有权仍与[普通静态I/O](torchair_cpp_static_executor_host_outputs.md)、[动态I/O](torchair_cpp_dynamic_executor_inputs_and_output_ownership.md)分别判断。

## 换档复用与验证成本

同一执行器只在首次FastLoad，后续复用图实例；仍会每次处理输入、准备输出、执行并刷新输出shape，并要求使用首次stream。这里没有每档建立独立C++执行器缓存的分支，也没有按换档自动编译新图的代码，不能从“复用一张图”推导每次零Host或分配开销。

const/feature管理沿用静态基类，见[外部分配器与feature内存](torchair_ge_external_allocator_feature_memory.md)。逐档核对有效输入shape、输出shape/容量、Host辅助输入、预分配输出、流身份和完整端到端耗时，再评价分档收益；本卡没有设备支持认证或性能数字。

## Evidence

- [主线MutiGear](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/muti_gear_npu_graph_executor.cpp)（primary）：19–170、173–241。
- [发布MutiGear](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/muti_gear_npu_graph_executor.cpp)（implementation）：相应输入、Run与返回循环的定向token差异。
- [继承关系](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/muti_gear_npu_graph_executor.h)（implementation）。
- [创建器](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_executor.cpp)（constraint）：17–46。
- [静态基类输出分配](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/static_npu_graph_executor.cpp)（implementation）：87–138、273–290。
- [同步拷贝、shape读取与Storage](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_utils.cpp)（implementation）：46–59、231–245、254–272。
