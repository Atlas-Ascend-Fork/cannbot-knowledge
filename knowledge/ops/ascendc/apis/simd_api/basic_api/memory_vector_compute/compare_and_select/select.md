---
type: API
title: Select
description: 根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Select

根据 mask 从两个源 tensor 中选择元素，mask 为 1 选 src0，为 0 选 src1。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Select CMPMASK_SPR 模式致混合分支误选](../../../../../runbooks/precision/select_cmpmask_spr.md)（`exemplifies`）：改用 `VSEL_TENSOR_TENSOR_MODE` 后，mask 作为 tensor 参数传入，`VselImpl` 每 repeat 用 `sel + i*selOffset` 正确偏移，对任意 count 正确。；根据 mask 从两个源 tensor 中选择元素，mask 为 1 选 src0，为 0 选 src1。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。。API 定义 mask 到 src0/src1 的选择语义，运行手册实测其 CMPMASK_SPR 重复 mask 故障并给出 tensor-mask 模式的正确偏移用法。
- [Select dst==src 别名破坏张量输入值](../../../../../runbooks/precision/select_dst_src.md)（`exemplifies`）：对所有 `dst==src0` 或 `dst==src1` 的 Select 调用，改用空闲中间 LocalTensor 作 dst，再 `DataCopy` 回填目标。；根据 mask 从两个源 tensor 中选择元素，mask 为 1 选 src0，为 0 选 src1。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。。API 卡定义 Select 的 mask 与双源选择合同，运行手册证明 dst 与任一源别名会破坏待选输入，并给出中间 LocalTensor 加 DataCopy 的安全调用法。
<!-- cannbot:related:end -->
