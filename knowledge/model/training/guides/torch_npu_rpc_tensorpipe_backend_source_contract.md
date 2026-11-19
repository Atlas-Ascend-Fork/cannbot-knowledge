---
type: Guide
title: TorchNPU RPC TensorPipe 后端源级契约：注册、传输优先级与设备/流协议
description: 固定主线源级核对 NPU_TENSORPIPE 后端注册与options校验、TP_SOCKET_IFNAME地址解析、传输/通道优先级、设备绑定、流与内存协议、超时生命周期及测试用Faulty注入边界。
tags:
- task.implementation
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/tensorpipe_agent.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/tensorpipe_agent.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/tensorpipe_utils.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/tensorpipe_utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/tensorpipe_npu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/init.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/init.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/testing/faulty_tensorpipe_agent.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/testing/faulty_tensorpipe_agent.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/rpc/backend_registry.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/rpc/options.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/init.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/init.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/tensorpipe_agent.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/tensorpipe_agent.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/tensorpipe_npu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/tensorpipe_utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/tensorpipe_utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/rpc/backend_registry.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/rpc/options.py
  role: implementation
created_at: '2026-11-13T05:22:15Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# TorchNPU RPC TensorPipe 后端源级契约：注册、传输优先级与设备/流协议

## 固定版本与范围

固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，整读 `torch_npu/csrc/distributed/rpc/` 下 init/tensorpipe_agent/tensorpipe_utils/tensorpipe_npu/testing/faulty_tensorpipe_agent 的 C++ 实现与 `torch_npu/distributed/rpc/` 的 backend_registry.py/options.py，共约 2900 行。静态阅读，未启动 RPC worker、未执行传输或设备实验；产品支持面与用户层约束复用[原生RPC与Future](torch_npu_native_rpc_future_scope.md)，本卡补源级行为。TensorPipe 为仓内 vendored `third_party/Tensorpipe`（命名空间 `tensorpipe_npu`），其内部实现不在本卡。

## Python 注册面与 options 校验

`backend_registry.py` 在 `torch_npu._C._rpc_npu_init` 存在时向 torch 的 `rpc.backend_registry` 注册两个后端：`NPU_TENSORPIPE`（常规）与 `NPU_FAULTY_TENSORPIPE`（测试故障注入），并把 `torch.distributed.rpc.BackendType` 重导出到本模块。静态组（传 world_size）走 `_init_process_group` 后用 `dist.all_gather_object` 交换各 worker 的设备数/device_maps/devices，校验通过后构造反向映射与设备表，再建 TensorPipeAgent、`_init_rpc_states`、`_all_gather` 与 barrier；动态组不建 process group，改用 `rpc_sync` 逐 worker 调 `_get_device_infos`/`_update_group_membership`，任一步失败即 `api.shutdown()` 并以 `ErrCode.INTERNAL` 重抛。

设备校验（`_validate_device_maps`）拒绝：节点设备重复、设备索引越界（`0 <= d.index < device_count`，计数来自 PrivateUse1 自定义后端的 `device_count`）、device_map 非 1 对 1（按目标设备反向查重）、静态组目标节点名不在名单、源/目标设备不在对应节点设备表或索引越界。所有 ValueError 均拼 `dist_error(ErrCode.*)` 错误码。`options.py` 的 `NPUTensorPipeRpcBackendOptions` 继承 torch `_TensorPipeRpcBackendOptionsBase`：`set_devices` 只接受 PrivateUse1 设备；`set_device_map`/`_to_device_map` 强制 1 对 1；num_worker_threads/rpc_timeout/init_method 默认值取 torch rpc 常量，不在本卡重复定义。

## 地址解析与传输/通道优先级

`TP_SOCKET_IFNAME` 指定网卡时经 `tensorpipe_npu::transport::uv::lookupAddrForIface` 解析；未设置按 hostname 解析；两者失败都只 `LOG(WARNING)` 并回退默认地址 `127.0.0.1`——多机部署依赖 hostname/网卡解析成功，静默回退环回地址会造成连接失败而非显式报错。传输优先级：shm 200 > ibv 100 > uv 0（最低优先级传输用于 bootstrap）；通道优先级：cma 1200 > mpt_uv 1100 > basic 1000 > npu_basic 0。注释明确 CPU 通道优先于 NPU 通道：npu_basic（`tensorpipe_npu::channel::npu_basic::create` 包一层 basic）垫底，因为 NPU 通道可能承载 CPU-to-CPU 传输但效率低于纯 CPU 通道。mpt_uv 通道固定建 16 条 UV lane（`kNumUvThreads=16`），发送时数据等分到多连接。用户可用 options 的 `_transports`/`_channels` 覆盖注册顺序：按向量出现次序反向赋优先级。

## 设备绑定与线程上下文

Agent 构造时 `tensorpipe_npu::setDeviceId(NpuSysCtrl::InitializedDeviceID())` 固定全局设备。线程池运行用户 UDF、完成 Future、错误路径的每处回调都重新 `c10_npu::SetDevice(InitializedDeviceID())`——线程池线程不继承构造线程的设备上下文，漏掉该重设的改动会破坏设备绑定。静态组用 `checkAndSetStaticGroup` 在 store 写 `rpcIsStaticGroup` 对齐；动态组成员变更走 `updateGroupMembership`，静态组下相关映射的读取由 `GroupMembershipLockGuard` 加锁保护。

## 序列化、流与内存协议

消息固定 4 个 payload：type、id、业务 payload、tensor 列表的 pickle；tensor 数据本体走 TensorPipe tensors 域。发送侧在 `MultiStreamGuard` 下 `cloneSparseTensors`；每设备类型经 `C10_REGISTER_TENSORPIPE_DEVICE_TYPE_CONVERTER` 注册表取转换器（torch_npu 仓注册 CPU 与 PrivateUse1 两种）。CPU 转换器对无 deleter 的 storage（`torch::from_blob` 不带 deleter 产生）强制整块拷贝进 `std::vector<char>`（注释明确防止发送期间内存被释放）；有 deleter 则零拷贝传指针。PrivateUse1 转换器（tensorpipe_npu.cpp）零拷贝：`NPUCachingAllocator::recordStream(data_ptr, stream)` 在 RPC 流上登记 tensor，防止发送完成前被缓存分配器回收；接收侧在 `NPUStreamGuard` 下用 `NPUCachingAllocator` 分配并自带 recordStream。

发送请求时先从全局流池为 `devices_` 取流（`getStreamsFromPoolForDevices`），再 `makeStreamsWaitOnOthers` 让池流等待当前生产者流（event record + block），保证设备侧先序；响应完成在 `MultiStreamGuard` 中 mark Future。反序列化对 PrivateUse1 tensor 用 `NPUStorageImpl` 重包 storage、`NPUNativeFunctions::set_` 挂尺寸/步长、`StorageDescHelper::SetDesc(..., ACL_FORMAT_ND)` 写存储描述，并断言实际收到设备与描述的 targetDevice 一致（不一致是 INTERNAL 错）。

## 设备映射语义与失败边界

默认只支持 CPU tensor：请求方向查 `opts_.deviceMaps`，响应方向查 `reverseDeviceMaps_`；发送非 CPU tensor 而无映射是 `TORCH_CHECK` 参数错误（错误文案引导 `set_device_map`）。响应 tensor 必须落在该 agent 声明的 `devices_` 内，否则把响应整体替换为异常响应（错误文案列出期望设备），不中断连接。RPC 超时由独立线程轮询 `timeoutMap_` 管理；`rpcTimeoutSeconds=0` 表示永不超时（不入表）。`join()` 对静态组做基于 `shutdownStore_` 的 `syncCallCount` 屏障两阶段收敛活跃调用数；动态组 `leaveGroup` 等 `clientActiveCalls_==0` 后从 store 摘除本名。指标键为 `agent.thread_pool_size/num_idle_threads/client_active_calls/server_active_calls/server_active_async_calls`；`agent.gil_average_wait_time_us` 仅在 GIL profiling 开启时聚合，平时不出现。

## Faulty 注入仅限测试链路

`NPU_FAULTY_TENSORPIPE` 构造 `FaultyTensorPipeAgent`：`messages_to_fail`/`num_fail_sends` 按消息类型与 payload 内容计数注入 `INTENTIONAL_FAILURE`；`messages_to_delay` 在 `pipeWrite` 内用 `sleep_for` 阻塞（持 GIL 释放与否未区分，延迟以秒转毫秒整型截断）。`messageStringToType` 只认 10 种消息类型名，其他名字 `TORCH_CHECK` 失败。该后端用于容错测试，不承载性能语义。

## 验证与失效边界

验证应分别确认：后端名与 options 类型、静态/动态组初始化路径、device_map 校验错误实际抛出（错误码前缀）、`TP_SOCKET_IFNAME` 在多机环境的地址解析日志（是否出现回退 127.0.0.1 的 WARNING）、NPU tensor 发送是否触发 recordStream、跨流等待事件与超时行为。本卡未执行以上任何运行时验证；vendored TensorPipe 与 ACL 行为随固定 commit，升级后需重读。文档层支持矩阵不在本卡，见[原生RPC与Future](torch_npu_native_rpc_future_scope.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/tensorpipe_agent.cpp)（primary），读取范围 1–1328 全文。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/tensorpipe_agent.h)（implementation），读取范围 1–405 全文。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/tensorpipe_utils.cpp)（primary），读取范围 1–316 全文。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/tensorpipe_utils.h)（implementation），读取范围 1–112 全文。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/tensorpipe_npu.cpp)（primary），读取范围 1–87 全文。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/init.cpp)（implementation），读取范围 1–185 全文。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/init.h)（implementation），读取范围 1–17 全文。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/testing/faulty_tensorpipe_agent.cpp)（implementation），读取范围 1–142 全文。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/rpc/testing/faulty_tensorpipe_agent.h)（implementation），读取范围 1–91 全文。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/rpc/backend_registry.py)（primary），读取范围 1–356 全文。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/rpc/options.py)（primary），读取范围 1–90 全文。

## 发布版本 对照（f3ecfe4a）

本节结论来自发布版本 孪生文件的逐文件比对（比对口径：sha256 → 去空白 → 全空白折叠 token → 注释剥离 token）。

### 等价绑定（结论对发布版本 直接适用）

- `torch_npu/csrc/distributed/rpc/init.h`、`tensorpipe_npu.cpp`、`tensorpipe_utils.cpp`、`tensorpipe_utils.h`、`torch_npu/distributed/rpc/options.py`：主线与发布两版本 逐字节一致。传输/通道优先级、kNumUvThreads、设备绑定、recordStream 与流等待协议等结论对发布版本 直接适用。

### 版本边界（发布版本 行为不同）

- **FaultyTensorPipe 测试后端在发布版整体删除**：`init.cpp`（185 → 94 行）不再绑定 `FaultyTensorPipeRpcBackendOptions`/`FaultyTensorPipeAgent`；`backend_registry.py`（356 → 298 行）删除 `NPU_FAULTY_TENSORPIPE` 注册与 faulty 构造 handler。「Python 注册面与 options 校验」中双后端注册与「Faulty 注入仅限测试链路」一节**限定主线**；发布 TorchNPU 26.0.0 无该测试后端，faulty 相关行号锚在发布版本 不可用。
- `tensorpipe_agent.cpp`（1328 → 1312 行）：`acl_rt.h` include 改 third_party 相对路径；RPC 超时错误消息由主线 `fmt::format(kRpcTimeoutErrorStr, timeout)`（:957）改为**空串**（发布 :928-929 `std::string errorMsg = ""`）；`tensorpipe_agent.h`（405 → 404 行）删除 `using torch::distributed::rpc::kRpcTimeoutErrorStr`（主线 :47）。发布版超时 Future 的错误文本为空，超时排障不能依赖错误消息内容，应以 RPCErrorType::TIMEOUT 与时间戳定位。

### Evidence（发布版本 补充）

- [发布孪生 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/init.cpp)（release-twin-binding）：diff 级全文对照（faulty 绑定删除）。
- [发布孪生 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/init.h)（release-twin-binding）：主线与发布两版本 逐字节一致。
- [发布孪生 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/tensorpipe_agent.cpp)（release-twin-binding）：diff 级全文对照（include 路径+超时错误空串）。
- [发布孪生 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/tensorpipe_agent.h)（release-twin-binding）：diff 级全文对照（kRpcTimeoutErrorStr using 删除）。
- [发布孪生 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/tensorpipe_npu.cpp)（release-twin-binding）：主线与发布两版本 逐字节一致。
- [发布孪生 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/tensorpipe_utils.cpp)（release-twin-binding）：主线与发布两版本 逐字节一致。
- [发布孪生 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/rpc/tensorpipe_utils.h)（release-twin-binding）：主线与发布两版本 逐字节一致。
- [发布孪生 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/rpc/backend_registry.py)（release-twin-binding）：diff 级全文对照（NPU_FAULTY_TENSORPIPE 删除）。
- [发布孪生 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/rpc/options.py)（release-twin-binding）：主线与发布两版本 逐字节一致。


（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
