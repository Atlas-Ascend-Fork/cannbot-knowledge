---
type: Guide
title: Inductor AscendC 控核：AF资源、Worker传递与缓存隔离
description: 界定set_device_limit在AF编译和运行中的注入范围，保留一次调用与失败后的状态边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/set_device_limit_inductor_af_design.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/set_device_limit_inductor_af_design_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py
  role: implementation
created_at: '2026-11-09T18:28:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC 控核：AF资源、Worker传递与缓存隔离

## 固定范围与软件身份

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c双语设计及compiler/__init__.py局部，另对照独立PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的npu_config.py局部。两主线未证明配套；无整套实验产品矩阵，故draft/空platforms，没有调用控核或设备实验。

只同步进程级set_device_limit到AF生成的Kernel/Tiling，不涉及set_stream_limit，不覆盖native aclnn fallback；不是硬件资源隔离或任意混合图全部限核保证。Static TopN还需CANN至少9.1及对应ResLimit接口。

## 用户调用及一次性状态

设计沿用torch.npu.set_device_limit(device,cube_num=-1,vector_num=-1)，cube对应aic、vector对应aiv，-1不限制，建议创建Tensor和compile前设置并使用新进程比较不同配置。0、其他负数或超设备值不作为推荐输入；读取层的归一化不等于公开API接受这些值。

独立固定PyTorch的_call_once_class在调用原函数前先called=True，限制该进程导入的接口对象一次，而不是每device各一次；参数检查或底层设置失败也不会在该装饰器自动复位，不能在同进程反复重试配置。它不是带锁的完整并发一次性协议，本文没有验证多线程竞态。

## 读取、规范化与注入

AF父进程先看set_device_limit.called，没调用返回None保留历史no-limit；调用过再读当前device的有效限制及硬件核数。源码把-1/None/0映射全量，超过上限取min；异常告警回None。called标志是读取依据，不证明用户那次设置已成功，须保留实际异常。

_inject_device_limit按aiv_num/aic_num/ub_size三个uint32调用Wrapper setter，ub_size固定0依赖AF默认解释，不能当已探测物理UB或可调UB参数。未配置跳过；旧Wrapper缺setter告警并保留默认，不能把“未报致命错误”当控核已经生效。

正常wrapper.so与TopN tiling_wrapper.so各自有独立g_device_limit，均须在相应init、候选生成或profiling前注入；FR列表只描述链路目标，不替代每个加载点的运行验证。CppWrapper设计从aclrtGetDeviceResLimit读取相应限制，也不是复用Python字段就自动生效。

## Worker、静态/动态缓存和观测

编译worker不依赖父进程运行时隐式继承，device_limit显式随compile_ascendc/get_topn任务传递，worker不再次调用一次性API。TopN以相同资源生成tiling_repr/workspace/block_dim，再编译静态候选；运行侧仍需注入一致的资源视图。

静态TopN/autotune的vector_core_num/ai_core_num进入artifact hash，变核数需不同静态候选；动态JIT不把这项加入通用库hash，运行时重新计算tiling。不能把动态库缓存命中解释成旧block_dim仍可用于新限制，也不把静态重编译成本当稳态收益。

设计的ResLimit含valid_num、aiv_num、aic_num、ub_size及resv[10]是该AF接口约定，不能手写到任意CANN版本。TC001..TC006表的Verified是来源声明，本仓没有设备验证。用真实Profiler kernel_details.csv的Block Num、duration、workspace及类型核对最终路径；block数满足上限仍不能证明端到端更快、所有fallback均限核或不同实例严格隔离。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/set_device_limit_inductor_af_design.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/set_device_limit_inductor_af_design_en.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/__init__.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py)（implementation）
