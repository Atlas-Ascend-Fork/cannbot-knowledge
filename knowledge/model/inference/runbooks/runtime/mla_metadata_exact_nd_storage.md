---
type: Runbook
title: MLA 长度 shape 正确仍需排查：owner 切片的 storage_offset 与 ND 存储容量
description: 从连续视图仍持有全 batch 存储的情况出发，核对长度张量的 stride、offset、storage 字节数及 metadata/attention
  输入一致性；修复效果待目标 NPU 验证。
tags:
- task.debugging
- topic.attention
- topic.graph_execution
- topic.memory
status: draft
sources: []
created_at: '2026-10-30T03:17:18Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - mla
      phase:
      - decode
---

# MLA 长度 shape 正确仍需排查：owner 切片的 storage_offset 与 ND 存储容量

## 现象

Kimi K3 Decode 按 request owner 切分主模型 MLA 的 batch。全局 `actual_q`、`actual_kv` 已经在设备上，当前 rank 只处理 `[owner_start:owner_end]` 范围。打印本地长度的 shape 看起来正确，也可能得到 `is_contiguous() == True`，但这还没有检查 Flash MLA 及其 metadata 算子真正接收的底层存储。

本卡处理的是这项输入边界诊断：部署版本的 ND 适配器若按 storage 字节数构造 `storageDims`，本地逻辑长度与仍归属全 batch 的底层分配可能不一致。尚缺目标 NPU 的修前、修后对照，不把该线索直接断言成任意 MLA 报错或精度异常的根因。

## 适用场景

- 工程入口：`models/kimi_k3/models/modules/attention_data.py` 中 `AttentionData.get_attn_metadata()` 的 Decode 分支，后续进入 `prepare_flash_mla_metadata()` 和实际 Flash MLA 调用。
- 目标平台为昇腾 950PR/DT；关注 MLA request-owner 长度张量和 `npugraph_ex` 的输入准备边界。具体 CANN/torch_npu 版本及目标分配器行为仍需在部署机记录，本轮未做实机验证。
- 处理对象是长度与累计长度，不是 K/V cache 的 NZ 布局。DSpark GQA 草稿模型的图外 metadata 构造应另按其自己的调用链排查。
- 使用顺序是先检查部署代码和输入探针，再试验精确物化方案；缺少契约证据时先保留原实现，不删除断言来放行。

## 输入从哪里来，为什么 shape 不够

Decode 先令每个请求的查询长度为 `q_len = verify_size`，再计算 `actual_kv = kv_len + q_len`。本地 `local_q` 和 `local_kv` 各有一个元素对应一个 owner-local 请求；`local_cu_q` 是查询长度累计和，不能把它与每请求长度混用。

仍直接保存切片的实现是：

```python
owner_start, owner_end = self._owner_slice()
local_q = actual_q[owner_start:owner_end]
local_kv = actual_kv[owner_start:owner_end]
local_cu_q = local_q.cumsum(0)
local_cu_kv = local_kv.cumsum(0)
```

设全 batch 有 `B` 个 int32 长度，本 rank 有 `b` 个，请求起点为 `s`。切片的逻辑数据量为 `b × 4` 字节，stride 可以仍为 1；它却可能保持父分配的 `B × 4` 字节存储，并且 `storage_offset = s`。`contiguous()` 检查的是逻辑步幅；当视图已经连续时，不能据此保证产生新的紧凑分配。需分别检查逻辑元素数、offset 和底层 storage 容量。

## 判别方法

1. 在进入编译的 Decode 前，记录当前 rank、owner 起止、各长度张量的 `shape`、`dtype`、`stride()`、`storage_offset()`、`untyped_storage().nbytes()`、`numel() * element_size()`。至少包含 `actual_seq_lengths_q`、`actual_seq_lengths_kv` 与 `query_start_loc`。
2. 检查本地请求数是否等于 owner 区间长度。若逻辑 shape 已错，先修复请求分片或长度计算；精确存储分配不能修复错误的请求归属。
3. 若 shape 正确，继续核对 `ndim == 1`、`stride == (1,)`、`offset == 0`、`storage_bytes == logical_bytes`。前两项成立而后两项不成立，才命中本卡关注的“连续视图仍保留父存储”。
4. 核对部署版本的适配器是否确实依赖 storage 字节推导 ND 描述。仅观察到较大的父分配不足以证明它一定造成算子失败。
5. 顺着两条消费者路径检查：metadata 构建和 Flash MLA 计算应使用同一份长度输入。仅在 metadata 内临时复制一份，可能使 metadata 与 attention 消费不同存储，不能完成边界对齐。

## 处理步骤与完整机制代码

在图外 `get_attn_metadata()` 内为每个 owner-local 输入重新分配、设置 ND、复制数值，并立即检查结果。以下是完整的局部 helper；它依赖外围方法的 `self.global_rank`、已导入的 `torch`，不是可脱离类上下文直接调用的独立脚本：

```python
def materialize_1d(name: str, value: torch.Tensor) -> torch.Tensor:
    # This runs before the compiled decode. For ND, the ACL adapter
    # derives storageDims from storage bytes, not from tensor.shape.
    result = torch.empty(value.shape, dtype=value.dtype, device=value.device)
    if result.device.type == "npu":
        import torch_npu

        result = torch_npu.npu_format_cast(result, 2)  # ACL_FORMAT_ND
    result.copy_(value)
    storage_bytes = result.untyped_storage().nbytes()
    if (
        result.ndim != 1
        or result.stride() != (1,)
        or result.storage_offset() != 0
        or storage_bytes != result.numel() * result.element_size()
    ):
        raise RuntimeError(
            f"MLA metadata {name} rank={self.global_rank}: shape={tuple(result.shape)}, "
            f"stride={result.stride()}, offset={result.storage_offset()}, "
            f"storage_bytes={storage_bytes}, dtype={result.dtype}"
        )
    return result
```

长度输入的成对应用：

```python
local_q = materialize_1d("seqused_q", actual_q[owner_start:owner_end])
local_kv = materialize_1d("cache_seqlens", actual_kv[owner_start:owner_end])
local_cu_q = local_q.cumsum(0)
local_cu_kv = local_kv.cumsum(0)
```

查询边界还应是带起始零、长度为 `b + 1` 的 int32 向量，而不是只有末尾累计值。该路径在 `mla_decode` 字典的 `query_start_loc` 中，先以 `torch.cat((local_cu_q.new_zeros(1), local_cu_q))` 补起始零并转 int32，再调用同一 `materialize_1d`。`query_boundaries` 的列表表示也要与这组边界一致。

按顺序完成下列修改：先图外物化 `local_q/local_kv`，再基于新输入计算累计长度，最后让 `mla_decode_metadata` 中的长度字段以及后续 Flash MLA 都使用这组输入。不要把 helper 搬进捕获中的 metadata 调用，额外生成只被单个消费者持有的临时张量。

## 设计决策

- 显式 `empty + copy_` 表达新的存储所有者；它解决的是 ownership 与容量问题，而不是通过改变数值规避失败。
- NPU 上显式设置 `ACL_FORMAT_ND`，再检查真实容量；格式名称本身不能替代存储探针。
- 保留失败即报错的守卫。若分配器仍返回不满足条件的存储，错误里应保留 rank、shape、stride、offset、字节数和 dtype，让下一步定位有据可查。
- metadata 算子的流事件与 capture/replay 生命周期仍可留在模型现有实现中；“长度输入图外物化”不等于把整段 metadata 计算任意移出图。

## 验证信号

当前已核对到两种实现形态：直接保存 owner 切片，以及图外物化并检查精确 ND 存储。也已核对 metadata 读取 `actual_seq_lengths_kv`、`query_start_loc`，量化路径另读取 `actual_seq_lengths_q`。这些是实现级证据，尚无本轮 NPU 修后验收结果；卡片保持 draft。

## 部署验收

1. 覆盖 owner 起点为零与非零的 rank，确认所有长度张量的值不变，精确物化后的 offset 为零、逻辑字节数与 storage 字节数一致。
2. 比较 metadata 与 attention 实际拿到的 dtype、值和存储信息，确认没有一条路径仍指向旧切片。
3. 在相同 shape 下更换 KV 长度和请求内容，完成至少两轮目标 NPU capture/replay；对齐 eager 输出以及 cache 写入与历史保留。
4. 若只通过存储断言但图执行仍失败，继续保留错误现场，检查真实算子 schema、长度语义和图生命周期；不能把断言通过写成精度通过。

## 坏实践、回退与失效边界

不要只看 shape 或 `is_contiguous()` 就结束；不要给张量附一个 ND 标签却不检查容量；不要只紧凑 metadata 的输入而保留 attention 的原切片；不要删 offset/容量守卫来宣称已修复。

回退必须同时恢复 metadata 与 attention 的长度输入策略，确保两者保持一致。该方案不处理全 batch 分片错误、query 累计长度缺起始零、K/V cache 布局或算子版本错配。未决项优先是取得目标 NPU 的修前、修后相同输入对照，并核实实际 ND 适配器的 `storageDims` 行为；未取得这些证据前不升级为稳定的实机修复结论。
