---
type: Guide
title: GE静态C++执行器：固定输出分配与Host同步边界
description: 核对编译输出shape、预分配NPU和Host输出、每次DataPtr分配，以及主线和发布版Host输入适配的差异。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/static_npu_graph_executor.cpp
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/static_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/npu_utils.cpp
  role: implementation
created_at: '2026-11-10T11:48:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE静态C++执行器：固定输出分配与Host同步边界

## 固定版本与范围

定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的StaticNpuGraphExecutor I/O、Run及相关拷贝/Storage封装。仅讨论静态执行器，动态档位有独立MutiGear实现，不能把本卡当成所有静态shape Python调用的统一路径。

没有执行C++、导入上游、编译、运行模型或测量显存/耗时；硬件和完整配套未知，保持draft与空平台。输出分配主体在两版一致，Host输入和内存管理的版本差异单独保留。

## 非冻结输入只更新地址，静态不等于自动校验shape

首次输入组装记录描述及frozen/Host load选项。后续frozen项直接跳过；其他项先检查placement，再调用AssembleDataToGe(...,false)，源码明确假定输入shape不变，不重建同样的存储shape描述。

因此运行前应确保缓存与本次输入的shape、dtype和布局合同一致；不能以“地址可以变”推导这些条件也可以任意变。Python Guards是否运行以及固定地址项是否需要重新建立实例，仍按各自路径核对，见[缓存生成kernel](torchair_ge_cached_kernel_first_run_contract.md)。

## 输出大小来自编译summary

首次AssembleOutputs从summary.GetOutputShapes和output_dtypes取输出shape/type，计算连续存储字节数，缓存为output_shapes_、output_torch_dtype_和output_size_。这些值后续不根据任意新输入重新推导。

assigned_outputs必须为空或与输出数量一致。每个输出分为以下路径：

| 输入的输出槽 | 运行缓冲与返回处理 |
| --- | --- |
| 已给定Tensor，且为PrivateUse1或输出字节数为0 | 直接绑定给定Tensor，后续更新其数据与存储shape，最后返回该对象。 |
| 给定非PrivateUse1 Tensor且输出非空 | 先分配NPU DataPtr供GE写入，运行后按编译字节数D2H到给定对象，再返回它。 |
| 未给定Tensor | 每次从PrivateUse1 allocator取得DataPtr供GE写入，之后MakeAtTensor把DataPtr移交给新建Storage，按编译shape建立返回Tensor。 |

最后一项没有在此额外复制整份输出数据，但每次会请求allocator并封装Tensor；是否复用底层缓存块取决于allocator和存活引用，不能把“没有输出数据copy”写成“没有分配开销”。也不能仅由GE的outputReuseMemIndexes选项推导所有Python返回都指向同一缓冲。

预分配对象的绑定没有在本层统一验证全部shape、dtype和容量条件。非PrivateUse1路径也不是任意其他设备都可用的合同；对于CPU目标，目的容量由其numel乘element_size传给拷贝helper，实际需要与编译输出字节数和布局匹配。

## Host输出会形成同步点

D2HMemcpy先aclrtSynchronizeStream，再调用同步aclrtMemcpy(DEVICE_TO_HOST)。返回CPU输出的成本因此包含流等待和设备到Host搬运，不能把包围Run的时钟统一解释成纯异步下发成本，也不能只比较图内算子时间。

零字节输出不走该非空D2H分支。需要CPU消费还是保留NPU结果，应按业务真实使用决定，并分别计入输出保留、同步与复制；本卡没有给出速度或零复制收益数值。

## Host输入适配存在版本差异

发布版首次和后续组装检查HOST且!IsSupportHostInput：首次分配NPU暂存并保存固定复制字节数，以后按该记录执行H2D；helper同样先同步流再拷贝。其IsSupportHostInput调用CheckCANNVersion82RC1，且Host load选项只在支持时加入。这里未展开该版本检查的完整实现，不把函数名当成所有旧CANN组合的支持矩阵。

主线删除了这个静态输入暂存回退，直接AtNpuTensorToGeTensor，并将CPU输入索引加入Host load选项；不能把发布版的旧栈Host回退自动带入主线。动态执行器的二维以上Host暂存是另一条按rank选择的路径，见[动态C++执行器](torchair_cpp_dynamic_executor_inputs_and_output_ownership.md)。

## 同实例的stream和内存时序

两版Run首次取得/记录stream，后续要求与first_stream_相同；FastLoad/FastExecute均可用才走快速路径，否则使用RunGraph。输出转换成功之后才结束本次调用并更新首次状态。

常量、feature和fixed memory与这些用户输出分开管理。特别是feature可刷新标志及主线disable_external_mem_base影响图内存准备，不等于取消用户输出分配或CPU结果拷贝，见[外部分配器与feature内存](torchair_ge_external_allocator_feature_memory.md)。

验证时分别观察真实执行器、输出是预分配还是新分配、CPU/NPU位置、静态shape一致性、流身份和保留结果的生命周期；本卡没有做设备或并发实验。

## Evidence

- [主线静态执行器](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/static_npu_graph_executor.cpp)（primary）：18–138、229–302。
- [发布静态执行器](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/static_npu_graph_executor.cpp)（implementation）：18–159及Run对应范围；定向差异见入库清单。
- [主线拷贝与Storage封装](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_utils.cpp)（implementation）：41–59、213–229、254–272。
- [发布Host能力与Storage封装](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/npu_utils.cpp)（implementation）：48–66、220–238、263–281、369–372。
