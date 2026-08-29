---
type: API
title: GetVecLen
description: 获取RegTensor位宽VL（Vector Length）的大小。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetVecLen.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# GetVecLen

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取RegTensor位宽VL（Vector Length）的大小。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](../../../../../runbooks/precision/select_vsel_cmpmask_spr_count_64.md)（`exemplifies`）：焦点接口用于“获取RegTensor位宽VL（Vector Length）的大小。”，候选卡把它用于明确决策：“对 count 大于 GetVecLen/sizeof(T) 的场景，`VSEL_TENSOR_TENSOR_MODE` 是唯一逐 repeat 重载掩码的正确模式。”；VL 直接决定 Select 是否跨 repeat 以及应选的修复模式。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：焦点接口用于“获取RegTensor位宽VL（Vector Length）的大小。”，候选卡在 Compare 掩码存储路径直接计算“uint32_t offset = GetVecLen() / sizeof(T) / 8;”；该偏移公式是定位小 count 掩码 padding 与 stale 数据范围的实现证据。
<!-- cannbot:related:end -->
