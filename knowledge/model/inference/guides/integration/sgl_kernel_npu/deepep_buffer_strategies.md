---
type: Guide
title: DeepEP Buffer：通信组绑定、策略选择与事件兼容边界
description: 说明 DeepEP Buffer 初始化时的 HCCL 通信组与策略绑定、Normal/Low-Latency 混用窗口，以及 EventOverlap
  和清理接口在固定源码中的实际边界。
tags:
- task.implementation
- topic.mixture_of_experts
- topic.implementation.resource_lifecycle
- topic.implementation.synchronization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/ep_strategy.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/utils.py
  role: implementation
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-08T11:02:02Z'
platforms:
- a2
- a3
- '950'
aliases:
- DeepEP Buffer
- DEEP_USE_MODE
- EventOverlap
---

# DeepEP Buffer：通信组绑定、策略选择与事件兼容边界

## 初始化决定通信组与策略

`Buffer(group, num_nvl_bytes=0, num_rdma_bytes=0, low_latency_mode=False, ...)` 读取 `group.rank()`、`group.size()`，通过 NPU backend 获取 HCCL 通信域名，并把这些信息交给 `deep_ep_cpp.Buffer`。`num_nvl_bytes` 等名称为 DeepEP 兼容名称，不能据名字推断 Ascend 采用 NVLink。获取通信域名失败时 Python 会打印异常并传入空名；对象构造成功不能替代后续通信可用性检查。

构造函数中的 `normal_strategy`、`low_latency_strategy` 可以分别选取，但若设置 `DEEP_USE_MODE`，环境变量会覆盖二者。固定源码的映射为：

| DEEP_USE_MODE | Normal | Low-Latency |
| --- | --- | --- |
| `default` | `DefaultNormalCommStrategy` | `DefaultLowLatencyCommStrategy` |
| `alltoall` | `AlltoAllNormalCommStrategy` | `AllToAllLowLatencyCommStrategy` |
| `ops` | `DefaultNormalCommStrategy` | `OpsLowLatencyCommStrategy` |

未知值抛 `ValueError`。这些对象在初始化时创建，之后仅修改环境变量不会重新构造既有策略。不同策略的 handle、padding 与计数格式不同，dispatch/combine 必须使用同一组配套实现。

## 混用窗口与配置边界

模块 README 将 DeepEP 定位于 A2、A3、旧称 A5 的 Ascend 950，正常通信软件组合说明为 CANN 9.0.0/9.1.0；这不意味着所有策略、量化模式和融合 MoE 依赖都支持相同组合。MegaMoe 的版本要求见[专用接口](../../../apis/deepep/deepep_mega_moe.md)。

同一进程对同一 EP group 同时使用 Normal 和 Low-Latency 时，上游要求各 rank 启动前一致设置 `DEEPEP_HYBRID_DEPLOYMENT=1`，为两种模式隔离窗口；只使用其中一种模式时无需据此打开混部。`DEEPEP_HCCL_BUFFSIZE` 只用于 DeepEP 的前置校验，实际 HCCL 缓冲仍由框架配置，不能只改该变量代替真实资源申请。

`get_dispatch_config` 与 `get_combine_config` 的固定配置表只含 EP ranks `2,4,8,16,24,32,64,128,144,160`；默认调用会先查表。其他文档给出的更大 rank 上限不能当作这些默认 helper 的接收范围，超出表时应核对显式 Config 与目标后端支持。

## 事件对象不等于已建立跨流同步

`EventOverlap` 保存 `event` 与可选 `extra_tensors`，但当前 `current_stream_wait()` 的函数体是 `pass`，该类没有 `wait()` 方法。Normal 文档中的 `event.wait()` 同步表述不能直接作为此 Python 封装的可执行用法；`previous_event` 也必须按选中策略逐层核对实际消费位置。

`clean_low_latency_buffer(...)` 在 Buffer 文档中明确为兼容空操作，不清空 Device/RDMA 缓冲，不能用它证明模式切换后的数据和状态已重置。Python 本页仅审阅公开封装与说明，未闭合 C++ 对象析构和设备缓冲释放链，不给出额外的销毁时序保证。

## 集成与验证

先记录平台、CANN 版本、EP group、有效策略和各 rank 环境，再分别验证 [Normal](../../../apis/deepep/deepep_normal_dispatch_combine.md) 与 [Low-Latency](../../../apis/deepep/deepep_low_latency_dispatch_combine.md)。混用场景应覆盖两种调用交替以及真实跨流依赖，不能只检查 `import deep_ep`。EP 的模型层职责见[专家并行](../../../concepts/parallelism/expert_parallel.md)。

本次仅进行了固定版本来源阅读，未执行构建、通信、真机、数值或性能测试。

## Evidence

- [python/deep_ep/deep_ep/buffer.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py)（primary）
- [python/deep_ep/README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/README.md)（supporting）
- [python/deep_ep/deep_ep/ep_strategy.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/ep_strategy.py)（implementation）
- [python/deep_ep/deep_ep/utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/utils.py)（implementation）
