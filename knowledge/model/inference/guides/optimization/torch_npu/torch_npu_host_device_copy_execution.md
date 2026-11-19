---
type: Guide
title: Host与NPU复制：non_blocking回退、生命周期和转换位置
description: 核对copy_的Host指针分类、主动同步与事件记录，说明主线和发布的H2D/D2H异dtype转换及临时存储差异。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/op_api/CopyKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/ops/op_api/CopyKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/CachingHostAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/CachingHostAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml
  role: implementation
created_at: '2026-11-10T13:56:11Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Host与NPU复制：non_blocking回退、生命周期和转换位置

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的原生OpAPI copy_到Host/NPU搬运与Host指针处理链。所比四个选定底层搬运/指针处理函数的非注释词法token相同；dtype准备和入口处理有差异，不能据此说两版全部copy_相同。整卡平台未知，保持draft、空平台；未导入、构建或运行上游。

## 入口与适用分支

两版npu_native_functions.yaml均声明copy_使用OpAPI；主线另有internal_format_opapi=True。显式NPUNativeOpApiFunctions::copy_在目标为NPU且源为Host时调用copy_h2d_baseformat_opapi，目标为Host且源为NPU时调用copy_d2h_baseformat_opapi，再经同dtype连续搬运helper进入copy_between_host_and_device_opapi。

入口先有DO_COMPATIBILITY表达式指定原生copy_回退，主线还处理内部格式回退/转换。这里闭合的是选中的base-format Host/NPU搬运消费者，不认证安装包最终分派、内部格式完整支持、D2D/P2P、共轭/负位后处理或所有Tensor.to路径。公开dtype/产品范围仍按[原生Tensor转换限制](torch_npu_native_tensor_conversion_scope.md)消费。

## non_blocking=True仍可能主动等待

同dtype、同shape且双方连续时可直接进入搬运helper；一般路径先准备连续/广播/转换后的Tensor再进入。实际搬运字节为`dst.numel()*dst.element_size()`，H2D选目标NPU设备的当前流，D2H选源NPU设备的当前流。

| non_blocking | 所选helper的本地调用序列 |
| --- | --- |
| False | 先aclrtSynchronizeStream，再调用AclrtMemcpyWithModeSwitch，显式携带Storage及storage_offset字节偏移。同步错误另按恢复模式等分支处理。 |
| True | 先LaunchAsyncCopyTaskWithModeSwitch，随后对Host一侧Storage与实际data_ptr调用process_non_blocking_copy。该后处理可能再次同步，不能只看前面的异步下发调用或日志。 |

`non_blocking copy without StreamSynchronize`日志打印在指针后处理之前，所以看到该行不证明整个copy_没有Host等待，更不证明搬运与模型计算重叠。这里没有把底层ModeSwitch/队列函数名称当成全部异步可见性保证。

## Host指针分类与生命周期钩子

H2D检查Host源，D2H检查Host目标。若ACL指针属性接口存在，先查询实际data_ptr的location.type；若不存在，则只用Host Storage基地址是否由TorchNPU Host缓存分配器识别来判断。

| 条件 | 所选后处理 |
| --- | --- |
| 属性为HOST且Storage基地址被ptr_exist识别 | 调用CachingHostAllocator_recordEvent，传入Storage基地址、DataPtr context和当前流。 |
| 属性为HOST但不被本分配器识别 | 本helper不记录该分配器事件，也不在这个分支显式同步；不能据此认定外部Host内存已由TorchNPU取得所有权。 |
| 属性不是HOST | 调用process_unregistered_mem_location_type，其中显式AclrtSynchronizeStreamWithTimeout。 |
| 属性接口不存在 | 识别为本分配器地址则记录事件，否则走上述同步分支。 |

属性查询使用实际data_ptr，分配器识别/事件记录使用storage.mutable_data与context；带偏移view不能把两种地址混为同一个检查项。`recordEvent`调用用于追踪Host存储与流的使用，不等于调用时数据已可由CPU读取、随意改写或已完成回收。

普通未注册Host内存可能落入同步路径；外部已注册内存可能进入不记录本分配器事件的路径。这里不推导任意外部注册/自定义分配器的自动生命周期保护，也未审完Host池全部释放和事件回收算法。配置与版本前提见[pinned memory选项](torch_npu_pinned_memory_options.md)。

## 异dtype时，主线与发布在哪里转换

下面限定已经进入Host/NPU的base-format路径。相同dtype、相同shape且双方连续时，两版均直接进行同dtype搬运；非连续或广播会先准备临时Tensor，不能仅凭copy_一次调用统计只发生一次分配/复制。

| 方向 | 发布快照 | 主线新增选择 |
| --- | --- | --- |
| H2D异dtype | 在Host对src.to(dst.dtype())，再expand_as/contiguous；目标不连续时另申请连续目标，搬运后再复制回目标。 | 当non_blocking=True且CPU-cast回退判据为false，先以源dtype申请设备临时目标，搬入源dtype数据，再aclnnCast到最终目标。其他分支仍先在Host转换。 |
| D2H异dtype | 先以源dtype搬到Host临时量，再由Host dst.copy_执行最终转换/布局复制。 | 当non_blocking=True且CPU-cast回退判据为false，先在NPU整理格式并_npu_dtype_cast到目标dtype，再D2H；否则仍用源dtype Host临时量和Host copy_。 |

主线CPU-cast回退判据先比较SoC枚举区间，再看源或目标的ACL dtype是否属于COMPLEX32、HIFLOAT8、FLOAT8_E5M2/E4M3FN、FLOAT4_E2M1/E1M2或INT4。它只决定这里避开设备cast的分支，不是完整产品支持矩阵，也不证明CPU转换必定可用；不能由新增设备cast路线扩大任意低精度搬运能力。

因此同一对源/目标dtype，打开non_blocking可能改变转换位置、临时量dtype和经过总线的数据大小；是否更快、数值是否满足参考要求，需要按实际路径验证。主线H2D临时量若与目标dtype不同则调用aclnnCast；同dtype但不同存储才做额外D2D copy。D2H若Host目标不连续或仍需转换，则最后还有Host copy_，non_blocking参数继续传入不等于整个包装无CPU工作。

重新生成的Host临时量走哪种分配器/是否被属性接口识别，需针对实际对象核对，不能把原始输入或最终目标的pinned属性直接套给全部中间量。

## 优化评估与边界

测输入搬运时，固定版本、实际入口、方向、源/目标dtype、shape/stride、Host分配来源和流；分别观察连续准备、Host/Device cast、传输字节、最终copy及Host等待。比较端到端延迟时保留数据就绪和异步存储寿命要求，再判断是否真的与计算重叠。

本卡只记录局部静态消费者，未执行Host属性查询、传输、Profiler采集、数值或性能实验；没有验证外部Host buffer、完整Host缓存池释放、图捕获或跨流组合。True标志、日志、指针识别或知识库校验通过都不构成运行verified。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/op_api/CopyKernelOpApi.cpp)（primary）：定向范围 17–36, 42–110, 113–224, 226–287。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/ops/op_api/CopyKernelOpApi.cpp)（implementation）：定向范围 38–76, 96–112, 116–203。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/CachingHostAllocator.cpp)（implementation）：定向范围 1276–1330。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/CachingHostAllocator.cpp)（implementation）：定向范围 1244–1298。
- [固定实现来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）：定向范围 14–20。
- [固定实现来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/npu_native_functions.yaml)（implementation）：定向范围 14–20。
