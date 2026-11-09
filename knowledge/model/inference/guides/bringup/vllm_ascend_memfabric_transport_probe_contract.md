---
type: Guide
title: vLLM Ascend MemFabric初始化、注册与字节传输探针
description: 说明 GlobalMemfabricTE 的角色/协议锁定、一次性内存注册及 test_memfabric_pd_read 的控制面、数据一致性和清理证据。
aliases:
- GlobalMemfabricTE
- MemfabricBackend
- test_memfabric_pd_read
tags:
- task.implementation
- task.debugging
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/utils/memfabric_transfer_engine.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/test_memfabric_pd_read.py
  role: implementation
created_at: '2026-11-03T05:38:36Z'
updated_at: '2026-11-03T05:38:36Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MemFabric初始化、注册与字节传输探针

## 固定来源与执行边界

本文静态阅读固定 Main 的 MemFabric wrapper 与双端探针，未安装或导入 memfabric_hybrid、初始化 NPU、注册内存或建立跨机连接。它用于安排传输验收，不提供模型质量或性能测量结果。

## 初始化与注册寿命

`GlobalMemfabricTE.configure` 只接受 Prefill/Decode、非负 device ID 和 sdma/device_rdma/device_urma，默认 sdma。首次配置后，角色、设备和协议必须保持相同。get_transfer_engine 必须在 configure 后调用；创建后再次传入不同 hostname 会失败。hostname 可达性错误在引擎初始化时暴露，源码错误提示要求 numeric IPv4。

初始化设置日志级别 2、`set_conf_store_tls(False, '')`，store_url=tcp://hostname，store_server_role=Prefill；unique_id 为 hostname:引擎公布端口，初始化前读取会抛错。这些是该 wrapper 的具体设置，不代表任意部署的控制面配置。

register_buffer 首先要求指针/大小数量一致，且引擎存在；用独立锁逐项注册，所有成功才置全局 `_is_buffer_registered`。之后调用直接返回，不会因新地址、新大小或新增 cache 而补注册。中途失败可能已经注册部分区域，也没有在这个 wrapper 中看到事务回滚；不可把一次成功标志跨换 backing 复用。backend 将非零注册/读取返回码统一为 -1 并记录读取错误，不自动重试。

## 双进程探针实际验证什么

`tools/test_memfabric_pd_read.py` 默认控制端口 29599、4MiB、120 秒 timeout、2MiB 对齐和周期 251 的模式。输入检查 numeric IPv4、非负 device、端口范围、正字节数/池大小与 timeout；不能据此补写未做的有限浮点检查。

P 在 NPU 建立测试字节，sync 后配置 Prefill engine、注册源缓冲，以换行 JSON 传 session、指针、字节数、period 和 SHA256。D 控制连接按 deadline 重试，校验 metadata 后分配目的地：offload 模式使用 2MiB 对齐 pinned CPU 池，另一模式用 NPU 张量。control 消息上限 64KiB，控制连接与数据引擎不是同一种完成条件。

D 调用 batch_transfer_sync_read，要求返回 0，再同步设备；随后同时做完整 torch.equal 与 SHA256 比较，而非仅看返回码。D 将结果回传 P。控制 metadata 中的 hash 与 ptr 只描述这一测试缓冲，不验证实际模型的 KV 页布局、dtype、TP/PP 对应或请求所有权。

脚本通过 setdefault 设置 ASCEND_TRANSFER_TIMEOUT，保留已有值且将秒数取整；不能认为控制面 timeout 与数据面实际 timeout 必然一致。P 关闭引擎、D 释放视图/底层缓冲和 offload 池，清理失败也会令探针失败。即使字节比较通过，也须保留清理状态，避免把未结束的注册寿命当可复用。

## 交给Agent的最小证据

分别记录两端版本、角色/协议/设备、通告地址、控制与数据端口、源和目的缓冲大小/对齐/owner、每阶段返回码、比较结果和清理结果。先用相同协议完成字节验证，再验证真实KV布局和连接器完成门控，最后测量 TTFT/TPOT、带宽与资源预算；单个模式的字节传输通过不直接外推到所有硬件、模型或跨节点组合。
