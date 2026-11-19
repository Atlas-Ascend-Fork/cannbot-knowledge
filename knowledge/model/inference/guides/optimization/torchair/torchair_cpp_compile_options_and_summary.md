---
type: Guide
title: GE图编译选项、summary检查与编译成本
description: 解释MemoryPriority与零拷贝默认值、静态输出检查、future等待和图析构同步，区分编译日志与完整冷启动。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/concrete_graph.cpp
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/concrete_graph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/session.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/session.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/concrete_graph.h
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/include/concrete_graph.h
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/torchair.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/third_party/ascend/include/metadef/external/ge_common/ge_api_types.h
  role: constraint
created_at: '2026-11-10T12:26:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE图编译选项、summary检查与编译成本

## 版本和证据范围

定向核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的NpuConcreteGraph编译、Session::CompileGraph及图析构。下述默认值插入、summary检查、future等待和析构条件在两版一致；主线内部torchair.disable_external_mem_base分支由已有内存卡单独说明。没有执行GE编译、设备或性能测试，硬件范围未知，保持draft与空平台。

## 默认编译选项通过insert补齐

TorchNpuGraphBase::Load把Python字典转换为GE键值，再调用NpuConcreteGraph::Create。Create解析图、placement、输出dtype与executor类型，随后NormalizeCompileOptions先复制用户options，再向map插入默认项。关键操作均为insert，已有同名键不会被这些默认值覆盖。

| 来源与条件 | 插入项 | 边界 |
| --- | --- | --- |
| NormalizeCompileOptions | ge.exec.memoryOptimizationPolicy=MemoryPriority | 已有该键时保留原值；不是无条件强制MemoryPriority |
| ACL_OP_DEBUG_OPTION非空 | op_debug_option=ACL取得值 | 已有op_debug_option仍优先；ACL返回API_NOT_SUPPORT时只警告并继续 |
| executor_type为NPU | ge.exec.reuseZeroCopyMemory=1 | 已有该键时保留原值；不是对每个Tensor都零拷贝的证明 |

源码中ATOMIC_CLEAN_POLICY插入被注释，不能把它当成这里已启用的优化。MemoryPriority只是传给GE的策略值，本卡未展开GE分配算法或证明它对任意模型都降低峰值显存。reuseZeroCopyMemory与[输出映射复用](torchair_ge_output_alias_and_input_reuse.md)、[静态输出和Host同步](torchair_cpp_static_executor_host_outputs.md)分别核对，不能从一个选项推导所有I/O都不搬运。

## AddGraph、设备编译和执行器创建是不同阶段

Compile先Session::AddGraph；成功后立即记录is_graph_added_、graph_id_和当前进程PID。对于NPU executor再调用Session::CompileGraph取得CompiledGraphSummary，完成静态输出检查，最后Executor::Create建立运行执行器。CPU executor不走本函数的显式CompileGraph/summary检查分支；这里不推导CPU后端内部是否还会编译。

输入hint中的任意负数只影响IsInputShapeStatic的日志分类。输入hint全静态而summary.IsStatic=False时会警告，但仍可继续建立执行器；不能依据FX输入shape就认定实际走静态C++ I/O。后续静态/动态/动态档位选择见[动态执行器](torchair_cpp_dynamic_executor_inputs_and_output_ownership.md)与[动态档位执行器](torchair_cpp_multi_gear_io_and_capacity.md)。

summary.IsStatic=True时，编译后会对照FX输出hint与GE输出：

- 输出数量、每项rank必须一致；逐维比较时任一方该维为-1则跳过该维，其他不相等返回错误。它不是每次Run都重新检查输入shape的guard。
- 输出dtype数量必须一致，一般逐项严格相等；GE为DT_HIFLOAT8或DT_FLOAT4_E1M2且FX为DT_UINT8时，允许警告后继续。该例外不执行类型转换，也不证明这些dtype在所有硬件上可用。

如果AddGraph已成功，而后续CompileGraph、输出检查或Executor::Create失败，本函数没有就地RemoveGraph回滚；图对象保存了已添加标志，清理还要看析构及Session状态。不能仅凭Python编译异常推断GE图已经立即移除。

## std::async不代表Compile接口异步返回

Session::CompileGraph通过std::async(std::launch::async, ...)在工作线程设置设备并调用GE CompileGraph；函数末尾future.get等待结果后才返回。Python/C++ Compile桥接释放GIL并调用该接口，但它仍等待本次编译完成，不向调用方返回一个可稍后等待的编译future。

事件日志Compile Graph ... consume的计时在工作线程内部开始，覆盖aclrtSetDevice与GE CompileGraph，结束时间戳紧接GE编译之后。它不包含AddGraph、工作线程启动/调度等待、随后警告处理、GetCompiledGraphSummary、stream allocation summary查询、FX/GE输出检查或Executor::Create。外层Python首次调用的compile区间还包含更多步骤，见[首次调用时序](torchair_ge_runtime_binding_and_first_call.md)。两条日志不能互换为完整冷启动时延。

CompiledGraphSummary只在传入summary为空时获取。若stream allocation summary符号可用，还会查询并打印逻辑流信息；该查询失败仅debug记录并继续，不等于GE编译失败。这些逻辑流摘要也不是实际设备执行完成的计时证据。

## 移除单图还可能同步绑定流

NpuConcreteGraph析构先检查创建进程PID、已AddGraph标志和Session是否仍初始化，不满足就跳过RemoveGraph。若执行器有绑定stream，先aclrtSynchronizeStream再RemoveGraph；同步返回值只写日志，RemoveGraph状态在析构中被丢弃。因此对象销毁可能产生额外流等待，析构正常结束也不构成每项清理均成功的运行验证。

单图RemoveGraph与[Session级Finalize](torchair_ge_session_global_options_and_lifetime.md)分开；常量/feature块和底层缓存分配器还有[独立生命周期](torchair_ge_external_allocator_feature_memory.md)。评估编译缓存收益时分别测Session初始化、Create/AddGraph、设备编译、summary与检查、首次Run、稳态执行及销毁，不把工作线程启动当作已消除冷启动成本。

## Evidence

- [主线图编译消费者](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/concrete_graph.cpp)：22–53、93–176、194–283；[发布消费者](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/concrete_graph.cpp)：22–53、93–162、176–261。
- [主线Session编译与RemoveGraph](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/session.cpp)：179–236、254–261；[发布Session编译](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/session.cpp)：175–230。
- [主线析构](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/concrete_graph.h)：27–55、74–76；[发布析构](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/include/concrete_graph.h)：27–55。
- [主线Load/Compile桥接](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/torchair.cpp)：182–209；[选项键定义](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/third_party/ascend/include/metadef/external/ge_common/ge_api_types.h)：75–82。
