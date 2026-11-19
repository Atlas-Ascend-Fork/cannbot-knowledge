---
type: Guide
title: GE AOE调优的原生调用与失败边界
description: 沿两版原生AOE调用区分初始化、调优Status、配置文件键与清理，解释Python计数不能证明优化成功。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/npu_aoe.cpp
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/npu_aoe.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/session.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/session.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/concrete_graph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/concrete_graph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/checker.h
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/torchair.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/_backend.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
created_at: '2026-11-10T12:36:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE AOE调优的原生调用与失败边界

## 版本和证据范围

定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的Python到C++ AOE调用链，以及发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的NpuAoe、Session::AutoTuneGraph和NpuConcreteGraph::AutoTune对应实现。本文的原生调用顺序、Status忽略和配置文件键差异在两个C++快照相同；Python计数细节据所列主线范围。没有加载AOE动态库、执行调优、故障注入、设备或性能测量，保持draft与空平台。

## 调优在设备编译之前，不是所有首次调用必做

普通GeConcreteGraph调用在graph.load之后检查should_auto_tune；成立则auto_tune，之后才compile。前置条件和Python首次调用时序已在[运行绑定卡](torchair_ge_runtime_binding_and_first_call.md)说明，本卡补齐其实际消费者。

主线auto_tune调用self.graph.auto_tune(inputs)，正常返回才递增本实例_auto_tune_times。GE图包装器和TorchNpuGraph把请求传给C++桥接；桥接转换Tensor列表、释放GIL并调用NpuConcreteGraph::AutoTune。后者逐项AtTensorToGeTensor后进入Session::AutoTuneGraph，没有在这一层返回优化收益或最优算法报告。

## 初始化和每次AOE session是两层资源

Session::AutoTuneGraph先要求GE Session已初始化，再以options.at取得work_path与aoe_mode，传给AoeTuningInitialize；AOE初始化成功后设auto_tune_init_=true，复制原GE图，再把图副本、输入和GE Session指针交给RunAoeTuning。复制失败会返回错误，不会继续调优。

AoeTuningInitialize每次进入都会dlopen libaoe_tuning.so、解析所需符号，并以work_path、job_type调用AoeInitialize；该函数没有“已经初始化就跳过”的保护。所需符号还含SetDependGraphs/SetDependGraphsInputs，即使所选RunAoeTuning函数没有使用它们，符号缺失仍会令加载返回错误。因此Python每个图实例的调优次数限制不能等同于整个进程只初始化AOE一次。

RunAoeTuning依次创建AOE session、绑定GE Session、设置调优图和输入、调用AoeTuningGraph，最后销毁本次AOE session。该函数虽接收stream参数，所读函数体没有使用它；不能仅因外层传递stream就认定调优已绑定该流。原生库内部调优、缓存及性能选择未在这里展开。

AoeTuningGraph的返回码0与8均被接受；8在本文件命名为NonOptimizerGraph。即使走到Success日志，也不能据此证明图发生优化或已有性能提升。

## 低层Status被忽略会影响“已调优一次”的含义

checker.h中TNG_ASSERT失败是返回Status::Error；RunAoeTuning的大部分调用失败因此返回错误Status。Session::AutoTuneGraph却用(void)忽略RunAoeTuning的返回值，随后直接返回Success；NpuConcreteGraph和Python/C++桥接只能看到这个外层状态。

因此，在初始化与图复制成功、低层调优返回错误Status的具体路径上，Python auto_tune仍可能正常返回并递增_auto_tune_times，接着进入普通编译。不能把计数大于0或Python没有抛错当成已成功完成AOE的证明。初始化失败和复制失败仍由外层返回错误；C++异常也不等同于Status返回，不能说所有错误都被吞掉。

RunAoeTuning在各步骤失败时直接返回，函数体没有统一清理guard保证执行末尾DestroySession。这里只指出所读函数的清理边界，未证明AOE库内部没有回收，更没有设备复现泄漏。

## 配置文件键的检查与读取不同

两个快照都先检查options是否包含ge.aoe_config_file，随后却从options.at(aoe_config_file)取值，再写入tuning_options[ge.aoe_config_file]。这两个输入键不同：

- 只有aoe_config_file键时，该条件不成立，这个文件值不会由所读代码传给AoeTuningGraph。
- 只有ge.aoe_config_file键时，条件成立但读取缺失的aoe_config_file会触发map::at异常；这不是前述被忽略的错误Status。

这里不提供绕过实现差异的内部配置配方，也不将差异扩大到所有AOE版本。诊断时应核对进入该函数的实际options和tuning_options，不能仅凭上层已经填写配置文件路径就断言AOE已读取它。

## 调优结束、AOE Finalize与卸库是不同事件

成功尾部DestroySession只结束本次AOE session。Session级Finalize在auto_tune_init_为真时调用AoeTuningFinalize；后者在handle非空时调用AoeFinalize，但不在此关闭句柄或把handle清空。NpuAoe单例析构才dlclose最后保存的handle。这里没有证明重复初始化、异常和进程退出的所有资源路径都已对称释放。

把AOE作为优化步骤时，分别保留实际原生返回码、调优文件/记录、随后编译路线、数值与稳态性能；调优计数和编译成功不能代替收益证据。持久代码生成在启用AOE时还有[独立缓存限制](torchair_ge_cached_kernel_first_run_contract.md)，全局释放另见[Session生命周期](torchair_ge_session_global_options_and_lifetime.md)。

## Evidence

- [主线AOE消费者](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/npu_aoe.cpp)：8–9、18–138；[发布AOE消费者](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/npu_aoe.cpp)：8–9、18–67、69–115、118–136。
- [主线Session调优与Finalize调用点](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/session.cpp)：161–164、238–251；[发布调用点](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/session.cpp)：157–160、232–245。
- [主线输入转换与调用](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/concrete_graph.cpp)：286–297；[发布调用](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/concrete_graph/concrete_graph.cpp)：263–275；[Status宏](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/checker.h)：43–70。
- [主线Python时序和计数](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)：1203–1215、1868–1875、1948–1952；[GE图薄包装调用](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)：905–906；[TorchNpuGraph薄包装调用](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/_backend.py)：205–207；[C++桥接](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/torchair.cpp)：212–230。薄包装仅用于闭合该调用边，不计为新建薄包装主题或全文覆盖。
