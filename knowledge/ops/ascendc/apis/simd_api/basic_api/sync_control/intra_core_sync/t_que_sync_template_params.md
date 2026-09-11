---
type: API
title: TQueSync
description: TQueSync类的模板参数，用于指定源流水和目标流水，目的流水等待源流水，配合SetFlag/WaitFlag实现跨硬件版本兼容的核内同步。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/TQueSync_template_params.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
source_headers:
- include/basic_api/kernel_operator_block_sync_intf.h
---

# 模板参数<a name="ZH-CN_TOPIC_0000001973155037"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_block_sync_intf.h"`。

TQueSync类的模板参数用于指定源流水和目标流水，目的流水等待源流水。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template<pipe_t src, pipe_t dst>
class TQueSync {
public:
    __aicore__ inline void SetFlag(TEventID id);
    __aicore__ inline void WaitFlag(TEventID id);
};
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| src | 输入 | 源流水。支持的流水参考[硬件流水类型](intra_core_sync_overview.md#硬件流水类型)。 |
| dst | 输入 | 目的流水。支持的流水参考[硬件流水类型](intra_core_sync_overview.md#硬件流水类型)。 |

## 返回值说明<a name="section640mcpsimp"></a> 

无

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例

请参考[SetFlag-WaitFlag](set_flag_wait_flag.md)接口的调用示例。
