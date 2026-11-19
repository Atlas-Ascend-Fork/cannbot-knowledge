---
type: Guide
title: GE AutoFuse自动内存归属的配置链
description: 闭合AutoFuse双开关、CANN版本查询缓存与load注入到图内存基址分支，解释保守判定和I/O边界。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/_backend.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/core/_backend.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/concrete_graph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/graph_data.h
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/static_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/muti_gear_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/GetCANNInfo.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/concrete_graph.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/muti_gear_npu_graph_executor.h
  role: constraint
created_at: '2026-11-10T12:36:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE AutoFuse自动内存归属的配置链

## 固定版本与适用范围

本卡定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的自动判定、load生产者和C++内存标志消费者，并沿Python版本辅助函数追至TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的原生CANN查询/比较入口。这两个固定实现用于说明调用合同，不构成任意TorchAir/TorchNPU/CANN组合兼容认证。未展开完整版本字符串解析器、GE内部融合编译或内存算法，没有设备实验，保持draft与空平台。

TorchAir发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的所查TorchNpuGraph.load没有这段自动注入，C++也没有同一内存标志分支，不能把主线行为回推发布版。本卡讨论GE图执行器，不混用TorchNPU FXRT的AutoFuse原生kernel接入或Inductor Ascend C后端的配置语义。

## 两个flags同时为真才通过前置检查

_is_autofuse_enabled读取当次AUTOFUSE_FLAGS，把分号分隔的每段去空白，再按等号拆分。必须恰有两个部分；缺少等号或含多个等号的段会警告后跳过。键名精确匹配，值去空白后转小写，仅true或1视为真；同名键重复出现时后面的有效段覆盖先前布尔值。

该辅助函数同时要求--enable_autofuse与--experimental_enable_jit_executor_v2为真。缺少任一项、显式false或其他值都不通过。只设置AutoFuse一个开关，不能据这条函数认定已切换图内存归属；该解析器也不是任意shell参数或GE全部配置的解释器。

_disable_external_mem_base_for_autofuse在此基础上继续检查：torch_npu必须已经位于sys.modules，随后导入其_is_gte_cann_version并比较9.2.0，module明确为CANN。没加载torch_npu时直接False，不为了探测而在该分支主动加载它。比较False或整个检查中发生Exception，均不自动注入关闭外部基址的标志；异常会警告，采用保留外部基址的保守判定。

## load时检查不等于每次重新探测安装版本

TorchNpuGraph.load先复制options字典，满足上述条件时将内部torchair.disable_external_mem_base写为字符串1，再调用底层load。它没有修改调用者原options对象。该辅助函数每次load都会调用，并非每次Run重算；已经创建的图不会因之后修改环境变量就在这条路径自动切换归属。

返回False的含义是“不自动注入”，并不是主动删除调用方已经提供的同名项；返回True则覆盖副本中的同名值。这个字段是前后端内部协作标志，本卡不把它发布为应手动设置的稳定调优接口。

在所审TorchNPU主线中，Python辅助函数转发到_C._is_gte_cann_version，再由Module.cpp调用IsGteCANNVersion。后者通过GetCANNVersion取CANN模块版本并调用专用比较器。GetCANNVersion按模块缓存结果：命中缓存立即返回；CANN包查询失败时连空字符串也会缓存。空/无效当前版本比较返回False。因此，TorchAir在load时重复调用版本辅助函数，不保证原生层重新探测安装版本，也不能把False一概解释成“实际CANN版本低于9.2”。

这里没有读取驱动版本替代CANN版本，也没有证明完整软件栈、芯片能力或所有融合算子均满足条件；9.2.0是这个生产者使用的门槛。

## 内部标志选择基址准备，保留用户I/O合同

GraphData.disable_external_mem_base默认False。NpuConcreteGraph::Create只在内部选项值精确等于1时置True，并从传给GE的compile_options中删除该选项；它不是直接转交给GE的同名公共参数。

当标志True，静态执行器跳过外部const和feature基址准备，但Run仍为stream注册分配器；动态执行器仍注册stream分配器，首次跳过外部fixed feature基址设置。动态档位执行器也保留stream分配器注册，并调用继承的基址准备逻辑。详细容量复用与释放边界复用[外部分配器卡](torchair_ge_external_allocator_feature_memory.md)。

这些分支改变的是TorchAir是否安装外部图内存基址，不是关闭用户输出分配、输入处理或Host结果搬运；也不保证总显存一定下降、所有计算已经融合或性能必定提升。I/O分别见[静态执行器](torchair_cpp_static_executor_host_outputs.md)、[动态执行器](torchair_cpp_dynamic_executor_inputs_and_output_ownership.md)及[动态档位](torchair_cpp_multi_gear_io_and_capacity.md)。

排查AutoFuse内存行为时，分别核对load时flags解析、torch_npu加载状态、实际版本查询结果及缓存、最终内部标志和执行器类型，再测图内存与用户I/O。全局Session是否重新初始化另见[Session生命周期](torchair_ge_session_global_options_and_lifetime.md)；重新load一张图不等于清空进程内所有版本或Session缓存。

## Evidence

- [主线自动判定与load](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/_backend.py)：60–114、181–195；[发布load对照](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/core/_backend.py)：109–125。
- [内部标志消费](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/concrete_graph.cpp)：210–215；[GraphData默认值](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/graph_data.h)：33–39。
- [静态基址与分配器调用](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/static_npu_graph_executor.cpp)：148–179、233–248；[动态调用](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp)：208–224；[动态档位调用](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/muti_gear_npu_graph_executor.cpp)：173–191。
- [TorchNPU Python版本入口](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)：51–62；[原生绑定](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)：2042–2056、2375；[原生查询缓存与比较入口](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/GetCANNInfo.cpp)：35–43、433–460、479–542。

- [发布C++ Create对照](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/concrete_graph.cpp)：192–196；[动态档位继承关系](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/muti_gear_npu_graph_executor.h)：13。
