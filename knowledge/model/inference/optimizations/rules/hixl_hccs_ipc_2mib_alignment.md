---
type: Optimization
title: HIXL/HCCS IPC KV 传输须 2 MiB 内存对齐（分配点 over-allocate + narrow）
description: online PD 分离推理走 HIXL / HCCS IPC 的 KV 传输后端（KVTransferManager，mooncake.engine.TransferEngine protocol=ascend，对应 Atlas A3 超节点场景）时：所有要向传输引擎 register_memory 的 NPU HBM 基址必须 2 MiB 对齐。PyTorch torch.empty/zeros 返回张量的 data_ptr() 不保证这个对齐，直接注册会得到非法基址。该后端整体 bring-up 的其它非显式前置见 mooncake-ascend-hixl-kv-transfer-bringup。
tags:
- task.optimization
- topic.kv_cache
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/452
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- a3
---

# HIXL/HCCS IPC KV 传输须 2 MiB 内存对齐（分配点 over-allocate + narrow）

## 适用场景

online PD 分离推理走 [HIXL](../../concepts/techniques/hixl.md) / HCCS IPC 的 KV 传输后端（[KVTransferManager](../../concepts/frameworks/kv_cache_manager.md)，`mooncake.engine.TransferEngine` protocol=`ascend`，对应 Atlas A3 超节点场景）时：**所有要向传输引擎 `register_memory` 的 NPU HBM 基址必须 2 MiB 对齐**。PyTorch `torch.empty/zeros` 返回张量的 `data_ptr()` 不保证这个对齐，直接注册会得到非法基址。该后端整体 bring-up 的其它非显式前置见 [mooncake-ascend-hixl-kv-transfer-bringup](../../runbooks/runtime/mooncake_ascend_hixl_kv_transfer_bringup.md)。

## 手段：对齐在分配点用 over-allocate + align_memory().narrow() 满足

对齐由**调用方在分配处**负责（`batch_register` 只做长度校验后 `register_memory`）：多分配一整个 `HIXL_ALIGNMENT` 的 slack，再取对齐后的视图切回目标长度。

```python
HIXL_ALIGNMENT = 2 * 1024 * 1024   # HIXL/HCCS IPC 要求注册基址 2 MiB 对齐

def align_memory(tensor, alignment):     # over-allocate 后返回对齐视图
    data_ptr = tensor.data_ptr()
    aligned = (data_ptr + alignment - 1) // alignment * alignment
    offset = int((aligned - data_ptr) // tensor.element_size())
    return tensor.narrow(0, offset, tensor.numel() - offset)
```

两处分配点各带一个 `data_ptr() % HIXL_ALIGNMENT` 运行时断言做防御：

- **元数据 buffer**（`MetadataBufferPool`，prefill RDMA 写入的 slot 池）：`torch.zeros(numel + HIXL_ALIGNMENT, uint8, device="npu")` → `align_memory(...).narrow(0, 0, numel)`；CPU fallback（tests / 非 NPU）不做对齐。
- **KV cache 张量**（`allocate_cache_tensors`）：`HIXL_ALIGNMENT` 是**字节数**，须按 dtype 元素大小换算 slack 元素数（`slack = (HIXL_ALIGNMENT + elem_size - 1) // elem_size`）——即对齐**已考虑数据类型**，`torch.empty(numel + slack, dtype, device)` 后 `align_memory().narrow().view(shape)`。

## 边界

- **ROCE 路径（`HCCL_INTRA_ROCE_ENABLE=1`）无此对齐要求**（据 `batch_register` 注释），对齐分配对两种后端通用（注释称 2 MiB 对齐对 memfabric DEVICE_RDMA 也无害）。
- 适用范围限本仓 HIXL/HCCS IPC KV 传输路径。"HIXL HCCS IPC 要求 2 MiB 对齐 / ROCE 无要求"为集成方的代码注释（对底层约束的陈述），未独立比对 HIXL/HCCS 算子规格。多实例 online PD 部署的 rendezvous 配置另见 [multi-instance-online-master-addr](multi_instance_online_master_addr.md)。

## 相关经验
- [vllm-ascend Mooncake connector 在昇腾直连 KV 传输的两个后](../../runbooks/runtime/vllm_ascend_mooncake_connector_backend_incompat.md)

## Evidence

- `diff 事实`（@aa8e66b6）：`buffer.py` 的 `HIXL_ALIGNMENT` 常量 + `MetadataBufferPool` 对齐分配 + CPU fallback、`cache_utils.py::allocate_cache_tensors` 的 dtype 感知 slack + 断言、`common_utils.py::align_memory` 实现、`transfer_engine.py::batch_register` 的 ROCE 例外注释均对上。
- 溯源下探：[cann-recipes-infer-pr-452-feat-mooncake-hixl-import-support-models-lazy-import](https://gitcode.com/cann/cann-recipes-infer/merge_requests/452)
- 无 before→after 性能数据（属正确性/前置约束）。