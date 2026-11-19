---
type: Guide
title: RNG状态保存与恢复：CPU快照、延迟设置和graphsafe共享
description: 区分Host状态快照、初始化前延迟clone、捕获限制及graphsafe状态指针共享。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/random.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/random.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_compat/accelerator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/NPUGeneratorImpl.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/NPUGeneratorImpl.cpp
  role: implementation
created_at: '2026-11-12T01:59:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# RNG状态保存与恢复：CPU快照、延迟设置和graphsafe共享

固定TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的Python状态接口和C++完整相关方法。本组解释状态申请、复制、错误次序与捕获门槛，不替代[原生随机数支持清单](torch_npu_native_rng_state_scope.md)或[C++接口签名](../../../apis/torch_npu/cpp_generator_and_hooks.md)。仅静态读取，未调用RNG、初始化NPU或执行图。

## Python读取会初始化，写入可能先排队

| 接口/条件 | 本地行为 |
| --- | --- |
| get_rng_state / initial_seed | 先_lazy_init，再取得所选/当前设备的默认Generator。all读取逐device_count调用，并非跨rank collective。 |
| 主线set_rng_state且未初始化 | 在DisableFuncTorch上下文clone为连续格式，闭包保留该副本，再_lazy_call。 |
| 主线已初始化 | 不做该Python clone；_lazy_call立即执行回调，将new_state交Generator.set_state。 |
| 发布set_rng_state | 无论是否初始化，先clone连续副本，设备参数str/int先转torch.device，再提交回调。 |
| _lazy_call | 已初始化就cb()，否则只把闭包与格式化堆栈排队。没有在这个helper统一执行设备初始化。 |

主线设备索引解析在回调中执行；发布的缺省索引也在回调中取current_device。manual_seed/seed同样在回调中选择当前设备，不能将未初始化时的调用时刻自动当成最终设备绑定时刻。主线通过get_default_generator兼容入口取Generator：本地配置对>=2.14声明上游accelerator入口，对更旧版本声明default_generators索引路线；解析器本身的版本选择实现不在此展开。

manual_seed_all将一个int seed逐个交给可见设备；seed_all只让第一个设备seed，再把得到的initial_seed传给其余设备。set_rng_state_all按传入迭代顺序逐索引设置，没有本地预先验证其长度恰等于设备数或对后续失败作整组回滚。它们都不自动同步其他进程的随机状态。

## 普通get_state是真正的Host字节快照

两版C++get_state申请CPU ByteTensor，长度为sizeof(uint64_t)+sizeof(int64_t)，以memcpy顺序保存seed和offset；所列实现分别是8字节加8字节。它不是复制一个完整设备随机数组，也不是graphsafe状态对象。字节按本机表示写入，不能据这几行当成跨所有ABI的通用序列化协议。

set_state先委托check_rng_state，再接受两种长度：只含seed的旧8字节格式，或包含offset的16字节格式；旧格式offset置0。完整格式把int64_t offset读出后cast为uint64_t。它先set_current_seed，再set_philox_offset_per_thread，后者要求offset为4的倍数；本地没有先统一验证全部字段再提交。因此无捕获时，坏offset可能在抛错前已经改变seed并把offset清0，恢复不是事务操作，也没有在这层另行拒绝所有负的序列化offset。

普通set/get_offset、随机seed()和新建无状态参数的Generator构造器都有assertNotCapturing。set_current_seed不同：非捕获时写seed并清offset；捕获中只允许与原seed相同，不在该分支重新清offset。Python“再次manual_seed相同值”在捕获内外不能简单理解为相同的重置动作。

get_state本身没有同样的assertNotCapturing；它调用的是philox_offset_per_thread，而不是受限的get_offset。主线按currentStreamCaptureId决定读全局offset或相应capture state的offset_intragraph；发布按CaptureStatus读全局offset或state内的offset_intragraph。这只说明局部选择，不能替所有捕获上下文承诺普通快照能替代图状态注册。

## graphsafe是共享state，不是另一份独立快照

graphsafe_get_state创建另一个同设备GeneratorImpl并传入原state_指针；graphsafe_set_state检查输入能转成NPUGeneratorImpl后，直接令state_等于对方state_。两方法都没有在这里深拷贝seed/offset，也没有在set方法新增设备索引相等检查。持有返回Generator不能理解为冻结一份将来不会变化的独立随机数快照。

普通ByteTensor快照、共享状态Generator、默认Generator及捕获的设备侧状态各有不同寿命和费用。随机序列是否跨步推进还取决于[捕获重放的状态管理](../torchair/torchair_inductor_ascendc_graph_tree.md)，本组没有重审已覆盖的capture/replay或宣称恢复一份状态即可恢复全部rank、输入和执行次序。诊断训练复现时，应同时记录所用接口、有效设备、初始化/排队时刻、状态别名及异常发生前的实际修改。

## 固定实现来源

- [random.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/random.py)（primary）：1–159。
- [random.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/random.py)（implementation）：1–167。
- [__init__.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）：239–244。
- [__init__.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/__init__.py)（implementation）：222–227。
- [accelerator.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_compat/accelerator.py)（implementation）：1–22。
- [NPUGeneratorImpl.cpp ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/NPUGeneratorImpl.cpp)（implementation）：293–495。
- [NPUGeneratorImpl.cpp f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/NPUGeneratorImpl.cpp)（implementation）：233–416。
