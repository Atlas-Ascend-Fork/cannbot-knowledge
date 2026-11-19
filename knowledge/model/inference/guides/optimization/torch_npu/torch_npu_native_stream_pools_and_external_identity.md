---
type: Guide
title: TorchNPU原生流池、身份校验与外部流登记
description: 核对分设备线程本地当前流、池轮转和优先级映射，区分主线外部流登记、句柄反查及unpack校验，并给出 Python 构造面的参数路由与优先级查询拒绝。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUStream.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUStream.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Stream.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Stream.cpp
  role: implementation
created_at: '2026-11-11T03:59:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU原生流池、身份校验与外部流登记

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整审读两版NPUStream.cpp/h本地定义，逐项比较C++ token及注释差异。本卡增补主线 `torch_npu/csrc/npu/Stream.cpp`（Python 绑定面）。产品与完整软件配套待核，保持draft、空平台；未构建或执行设备/并发/性能测试。公开API复用[C++流接口](../../../apis/torch_npu/cpp_npustream.md)，这里补本地池、身份与所有权消费者。

## 初始化、流池与当前流

LeakyStreamInternals保存设备、id、ACL句柄、Repository、预处理/stop/sync-launch标志及prev_stream。构造默认建立Repository，析构刻意不调用ACL销毁流，注释理由是全局对象销毁时runtime可能已关闭；这不是调用者自行销毁任意句柄的授权。

全局按设备维护default与secondary流、两个优先级索引的普通池、4条sync-launch流。GetStreamsPerPool与对应bits均为函数内static：OptionsManager的GetStreamsPerDevice()==8时取8及3bit，其他值取32及5bit。源码“每池8条”的注释不覆盖该真实分支。普通池和sync-launch各用原子计数模池大小轮转，所以重复取得包装对象不保证物理流独占。

initNPUStreamsOnce先current_device、SetTargetDevice、LazySetDevice和系统LazyInitialize，按设备flag与mutex延迟初始化default/secondary；thread_local current_streams数组初次建立时各设备指向default。initGlobalStreamState取device_count并断言不超过C10_COMPILE_TIME_MAX_NPUS；device_id先初始化为0，GetDevice返回错误时只记日志，随后仍用该变量继续初始化，不推断失败调用是否改写输出参数。默认流初始化只在TaskQueue开启时InitRepo。普通两池各用call_once延迟建立，sync-launch另有call_once。

getStreamFromPool(int priority)以clamp(-priority,0,1)选择池，bool重载映射到0或-1，getNPUStreamFromPool使用0。池创建实际向AclrtCreateStreamWithConfig传priority=0及FAST_LAUNCH|FAST_SYNC；不能仅由HIGH标签推导所配runtime必然抢占或已实现不同物理优先级。sync-launch固定4条，flags仅FAST_SYNC并标is_sync_launch。

getCurrentNPUStream、普通池和secondary入口在解析-1为当前设备后检查device范围；getDefaultNPUStream本地按该编号直接取数组，不能替所有入口补同一检查。getCurrentNPUStreamNoWait直接返回thread-local当前内部对象的ACL句柄。setCurrentNPUStream修改对应设备的线程本地指针，不在本地自动恢复；需要作用域恢复的调用者复用[StreamGuard接口](../../../apis/torch_npu/cpp_npustream_guard.md)。

## 包装、标识与主线校验

NPUStream包装c10::Stream，普通构造检查PrivateUse1；Unchecked构造跳过它。device/id/unwrap/pack3与相等比较沿底层流表示，std::hash同样委托c10::Stream。成员析构为空，不以包装对象消失推导设备流销毁。

普通流id按类型左移pool bits并合索引，包含DEFAULT、SECONDARY、SYNCLAUNCH、NORMAL、HIGH。主线另用bit30作为external标记，其余低位作登记索引；内部默认无效id为int64的0x3FFFFFFF，发布仍为int32的-1。该表示属于固定实现，不能由用户自行拼id替代取得接口。

主线NPUStream_internals先验证设备编号处于编译期C10_COMPILE_TIME_MAX_NPUS范围，再按类型处理：default索引必须0且句柄已初始化；普通池索引需小于32且对应句柄非空；sync-launch索引小于4且已初始化；secondary需非空；external持锁检查登记索引及指针。普通池物理上限32检查不意味着8条配置中其余槽位已经创建。

主线unpack3构造后调用validate，validate沿上述internals检查；发布unpack3仅包装返回，没有这组新增校验。发布internals对普通/secondary/sync-launch的访问也没有主线新增的范围和非空检查。不要把主线失败关闭条件回推发布；源码错误文本仍提CUDA也不改变真实PrivateUse1类型。

## 主线外部句柄登记与托管句柄反查

getStreamFromExternal先拒绝nullptr、初始化和检查设备，持external_streams_mutex按设备查找相同ACL句柄；已存在则复用同一内部对象，否则分配external id、保存句柄并reset其repo，再加入只增长vector。包装不接管该外部ACL流的销毁或完成跟踪。相同地址在不同设备登记仍分属各自列表，本函数没有查询runtime验证句柄真实设备归属。

getNPUStreamFromManagedAclrtStream与上述登记用途不同：按指定设备或所有设备扫描已存在default/secondary/普通池/sync-launch句柄，找到后返回托管包装，找不到抛VALUE；它不把未知句柄登记成外部，也不为匹配预先创建尚未初始化的池。所读发布cpp/h没有这两个主线实现入口，结论仅限定准确源码文件。

主线query与synchronize显式拒绝external流，isSyncLaunchStream对external直接返回false；external判断/拒绝helper另见[原生Event与外部流](torch_npu_native_event_host_submission_and_ipc.md)。原始句柄仍需调用者提供完成和寿命协议。取句柄的Host排队副作用与同步范围见[原生流队列](torch_npu_native_stream_queue_drain_and_synchronization.md)。

## Python 构造面的参数路由

增补固定主线 `torch_npu/csrc/npu/Stream.cpp`（`torch_npu._C._NPUStreamBase`，基类为 torch 的 THPStream）。构造只收六个键：`priority`/`is_sync_launch`/`stream_id`/`device_index`/`device_type`/`stream_ptr`，路由按优先级判定：

1. 显式给出 `stream_id`/`device_index`/`device_type` 任一即 `unpack3` 重建既有流（随后 `stream.validate()` 走主线校验），三个参数被当作一组，不校验彼此一致性由调用方负责。
2. 否则给 `stream_ptr` 时登记外部流：`getStreamFromExternal(aclrtStream, current_device)`；**外部流禁设 priority 与 is_sync_launch**，任一非默认值即 TORCH_CHECK PARAM 报错（错误文案固定为 "was explicitly set for an external stream"）。current_device 在解析参数前已由 `GetDevice` 取得，即外部句柄登记在当前设备，不在参数里换设备。
3. 否则 `is_sync_launch` 取 `getNPUStreamFromSyncLaunchPool()`（4 条固定池）。
4. 否则 `getStreamFromPool(priority)` 建普通池流。

**`get_priority` 与静态 `priority_range()` 都直接 TORCH_CHECK false（NOT_SUPPORT）**——构造参数接受 priority（并用于选池），但流对象的优先级查询面不存在；错误文案为 "NPU dose not support ... currently."（源码如此拼写）。`set_data_preprocess_stream(bool)` 把流标记为数据预处理流（配合 runtime 的引擎优先级语义，另见[TaskQueue 模式执行](torch_npu_taskqueue_mode_execution.md)）。`query`/`synchronize` 中 synchronize 释放 GIL；`stream_id`/`device_type`/`device_index` 为只读成员。`THNPUtils_PySequence_to_NPUStreamList` 接受本类型或 None 的混合序列（None 转空 optional，供 profiler 等消费方表达「保持默认流」），序列中出现其他类型按 TYPE 报错。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.cpp)（primary），读取范围 1–1037。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.h)（implementation），读取范围 1–166。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUStream.cpp)（implementation），读取范围 1–817。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUStream.h)（implementation），读取范围 1–172。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Stream.cpp)（primary），读取范围 1–254 全文。

## 发布 pin 对照（f3ecfe4a）

本节结论来自发布 pin 孪生文件的逐文件比对（比对口径：sha256 → 去空白 → 全空白折叠 token → 注释剥离 token）。

### 版本边界（发布 pin 行为不同）

- `torch_npu/csrc/npu/Stream.cpp`（Python 绑定面，254 → 261 行）：acl 头 include 改 third_party 相对路径之外，发布版**删除了外部流的 priority/sync-launch 禁设检查与 `stream_ptr` 的 `getStreamFromExternal` 直取路径**（主线 :52-54 的两条 "was explicitly set for an external stream" TORCH_CHECK 与 :61 的三元分派中 stream_ptr 分支）。「Python 构造面的参数路由」一节的第 2 条路由与外部流禁设检查**限定主线**；发布版构造参数面相应收窄（stream_ptr 不再是登记外部流的入口），主线 NPUStream.cpp 侧 external 登记机制的版本差异见上文「主线外部句柄登记与托管句柄反查」既有分界。`get_priority`/`priority_range` 的 NOT_SUPPORT 拒绝与其错误文案两版语义不受此差异影响。

### Evidence（发布 pin 补绑）

- [发布孪生 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Stream.cpp)（release-twin-binding）：diff 级全文对照（外部流检查与 stream_ptr 路径删除）。


（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
