---
type: Guide
title: GE动态C++执行器：Host搬运、冻结输入与输出所有权
description: 解释动态图每次输入更新和二维以上Host同步拷贝，区分预分配输出与GE内存转交，以及同一执行器的流限制。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/npu_utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_executor.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/executor.h
  role: constraint
created_at: '2026-11-10T11:48:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE动态C++执行器：Host搬运、冻结输入与输出所有权

## 固定路径与证据范围

定向核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的动态执行器、拷贝helper和GE输出转Tensor。下述I/O主体在两版一致；主线新增外部内存关闭条件及首次FastLoad后的deadlock check，不能回推发布版。未导入或运行上游、编译GE、访问设备或测量性能，完整平台未知，保持draft与空平台。

主线创建器在编译summary非静态时选DynamicNpuGraphExecutor；summary静态但具备动态档位选项时另选MutiGear执行器。不能仅凭torch.compile(dynamic=True)就认定最终走本卡所有分支。

## 每次更新输入，但frozen项提前跳过

首次AssembleInputs按输入位置构造GE/gert描述，并把符合NPU条件的frozen索引、真实data_ptr及storage字节数写入load选项。后续非frozen设备输入使用AssembleDataAndStorageShapeToGe，更新数据与存储shape；frozen项在placement检查之前直接continue，不重新绑定新地址或shape。

placement数量必须与本次输入数量一致，非frozen输入还检查编译与执行位置一致。CheckPlacement本身仅以HOST对应is_cpu、DEVICE对应非CPU作粗分类，不是任意非CPU设备都可用于NPU图的支持合同。dtype、地址寿命、布局和输入域仍需调用方建立，不能从动态更新函数名推导完整输入guard。

## 二维以上Host输入引入同步搬运

该执行器的Host适配按rank分支：scalar/一维直接绑定；二维以上先建立PrivateUse1暂存Tensor。后续shape相同复用这份暂存，shape改变才重建，但非空数据每次仍调用H2DMemcpy。复用暂存不等于省去每次复制。

H2DMemcpy先aclrtSynchronizeStream，再同步aclrtMemcpy(HOST_TO_DEVICE)，不是在这里安排异步拷贝。因此把辅助输入留在Host、或把一维数据改成二维形状，可能增加同步和搬运成本；不能仅按元素数或Python输入处理耗时评估。这里未测得延迟，也未核实首次调用中空stream的Runtime语义。

两处UpdateHostInput的调用没有用TNG_RETURN_IF_ERROR传播其Status；helper内部的同步或拷贝错误返回与外层Success须分别核对。这是源码中的错误处理边界，尚未复现设备故障。

## 预分配输出与GE分配输出不同

assigned_outputs为空或与图输出数量相同。某槽给了Tensor时，首次绑定其描述，后续更新数据和shape，运行后直接把该Tensor作为返回对象。该分支没有额外clone，也没有本层统一的完整dtype、设备和容量合法性验证，不能只因返回对象身份不变就认证所有别名组合正确。

未给Tensor的槽在运行前清空GE数据指针和大小，让GE分配，再由GeTensorToAtTensor构造返回Tensor；它不是无条件把结果复制到新的PyTorch缓冲。

| GE表示与分支 | 数据所有权处理 |
| --- | --- |
| ge::Tensor | ResetData取出RawGeDataPtr，将它放进PyTorch DataPtr的context，由deleter销毁该持有者。 |
| gert::Tensor带addr manager | Release取得地址管理器及block，在PyTorch context析构时调用kFreeTensor。 |
| gert::Tensor无manager、设备输出 | 使用原地址和deleteNothing；本分支不拥有释放回调，生命周期需要外围另证。 |
| gert::Tensor无manager、Host输出 | 分配CPU缓冲并memcpy，不能把它视为与设备分支相同的零复制。 |

gert转换还拒绝origin shape与storage shape不同的结果，随后按连续字节数构建Storage。内部格式输出、跨次调用保存结果和真实stride须单独检查；这一转换不支持任意设备布局的直接封装承诺。

## 同一执行器不支持换stream运行

Run未收到stream时取得当前NPU流；首次记录first_stream_，后续要求stream相等。快速路径需要FastLoadGraph与FastExecuteGraph同时可用，否则使用RunGraph；这个能力判断在局部static变量中保存，不是每次重新探测。

成功完成运行和输出转换后才把is_first_run_设False。固定权重、输出别名和Host输入复制与[Python输入重建](torchair_ge_runtime_binding_and_first_call.md)分层核对；显存和耗时比较应包含同步拷贝、GE分配、输出持有与后续消费流，而不只看图内算子时间。

- [静态执行器的输出与Host分支](torchair_cpp_static_executor_host_outputs.md)
- [外部分配器与feature内存](torchair_ge_external_allocator_feature_memory.md)
- [Python输出别名与输入复用](torchair_ge_output_alias_and_input_reuse.md)

## Evidence

- 两版dynamic_npu_graph_executor.cpp的AssembleInputs、UpdateHostInput、AssembleOutputs、RefreshAtTensorFromGeTensor和Run；定向范围及固定源SHA见入库清单。
- 两版npu_utils.cpp的H2DMemcpy、AssembleFrozenOption；两版concrete_graph/utils.cpp的GE输出转换及context释放。
- 主线npu_executor.cpp的执行器选择和include/executor.h的CheckPlacement；不表示全文或完整设备生命周期审计。

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_utils.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/npu_utils.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/utils.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/utils.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_executor.cpp)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/executor.h)（constraint）
