---
type: API
title: MaskMergeMode
description: 枚举类型，用于指定寄存器数据写入模式，包括ZEROING置零和MERGING保留原值两种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/MaskMergeMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: [agnostic]
---

# MaskMergeMode

枚举类型，用于指定寄存器数据写入模式，包括ZEROING置零和MERGING保留原值两种模式。

本接口属于 Reg 矢量计算辅助数据类型定义。

```cpp
enum class MaskMergeMode {
    UNKNOWN,
    MERGING,
    ZEROING
};
```

- `UNKNOWN`：接口或转换类型不支持显式 MaskMergeMode 时使用。
- `ZEROING`：mask 未选择的 lane 在目的寄存器中置零。
- `MERGING`：mask 未选择的 lane 保留目的寄存器原值。具体接口是否支持 MERGING 仍需核对其支持矩阵。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Reg Cast 默认 UNKNOWN mask 被拒 — 显式 ZEROING](../../../../../runbooks/compilation/reg_cast_requires_explicit_zeroing_trait.md)（`exemplifies`）：- `ZEROING`：mask 未选择的 lane 在目的寄存器中置零。；CANN 9.0.1 的默认 `castTrait` 将 `MaskMergeMode` 置为 `UNKNOWN`，而 dav-3510 的 `Reg::Cast` 实现静态约束只接受 `ZEROING` 或 `MERGING`。。运行手册展示 Reg::Cast 在 dav-3510 上如何实际选择枚举卡定义的 ZEROING，以修复默认 UNKNOWN 被静态约束拒绝的问题。
<!-- cannbot:related:end -->
