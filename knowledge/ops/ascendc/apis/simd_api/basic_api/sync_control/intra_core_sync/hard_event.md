---
type: API
title: HardEvent
description: HardEvent 是核内 SetFlag/WaitFlag 使用的事件类型枚举，每个取值表达一条源流水到目标流水的依赖方向，另含 AIC
  专用 HardEventAic 与 AIV 专用 HardEventAiv。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.synchronization
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/impl/basic_api/kernel_event.h
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag_WaitFlag_ISASI.md
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/intra_core_sync_overview.md
  role: supporting
created_at: '2026-10-29T07:13:46Z'
updated_at: "2026-10-31T09:21:53Z"
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
---

# HardEvent

HardEvent 是核内同步 `SetFlag`/`WaitFlag` 使用的事件类型枚举，每个枚举值固定表达一条"源流水 → 目标流水"的依赖方向，命名规则为 `<源流水>_<目标流水>`。例如 `MTE2_V` 表示"源为 PIPE_MTE2、目标为 PIPE_V"的事件，`MTE2_S` 表示"源为 PIPE_MTE2、目标为 PIPE_S"的事件。同文件另有 AIC 专用枚举 `HardEventAic` 与 AIV 专用枚举 `HardEventAiv`。

头文件：`impl/basic_api/kernel_event.h`。枚举声明位于 `:38-128`（固定 commit `016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a`）。

## 枚举定义

```cpp
enum class HardEvent : uint8_t {
    // src_dst
    MTE2_MTE1,
    MTE1_MTE2,
    MTE1_M,
    M_MTE1,
    MTE2_V,
    V_MTE2,
    MTE3_V,
    V_MTE3,
    M_V,
    V_M,
    V_V,
    MTE3_MTE1,
    MTE1_MTE3,
    MTE1_V,
    MTE2_M,
    M_MTE2,
    V_MTE1,
    M_FIX,
    FIX_M,
    MTE3_MTE2,
    MTE2_MTE3,
    S_V,
    V_S,
    S_MTE2,
    MTE2_S,
    S_MTE3,
    MTE3_S,
    MTE2_FIX,
    FIX_MTE2,
    FIX_S,
    M_S,
    FIX_MTE3,
    MTE1_FIX,
    FIX_MTE1,
    FIX_FIX,
#if defined(__NPU_ARCH__) && ((__NPU_ARCH__ == 5102) || (__NPU_ARCH__ == 3003) || (__NPU_ARCH__ == 5101) || \
                              (__NPU_ARCH__ == 5161) || (__NPU_ARCH__ == 5165) || (__NPU_ARCH__ == 5163))
    FIX_V,
    V_FIX,
#endif
    MAX,
};

enum class HardEventAic : uint8_t {
    // src_dst
    MTE2_MTE1,
    MTE1_MTE2,
    MTE1_M,
    M_MTE1,
    MTE3_MTE1,
    MTE1_MTE3,
    MTE2_M,
    M_MTE2,
    M_FIX,
    FIX_M,
    MTE3_MTE2,
    MTE2_MTE3,
    S_MTE2,
    MTE2_S,
    S_MTE3,
    MTE3_S,
    MTE2_FIX,
    FIX_MTE2,
    FIX_S,
    M_S,
    FIX_MTE3,
    MTE1_FIX,
    FIX_MTE1,
    FIX_FIX,
    MAX,
};

enum class HardEventAiv : uint8_t {
    // src_dst
    MTE2_V,
    V_MTE2,
    MTE3_V,
    V_MTE3,
    V_V,
    MTE3_MTE2,
    MTE2_MTE3,
    S_V,
    V_S,
    S_MTE2,
    MTE2_S,
    S_MTE3,
    MTE3_S,
    MAX,
};
```

`FIX_V` 与 `V_FIX` 仅在 `__NPU_ARCH__` 为 5101/5102/5161/5163/5165 时编译进枚举；`HardEvent::MAX` 是枚举边界，不是可用事件。

## 取值规则

| 组成 | 含义 |
| --- | --- |
| 前缀 `MTE1`/`MTE2`/`MTE3` | 各条数据搬运流水 |
| `M` | Cube 矩阵计算流水 |
| `V` | Vector 计算流水 |
| `S` | Scalar 流水 |
| `FIX` | Fixpipe 流水 |
| 下划线后段 | 该事件等待/通知的目标流水，语义与源流水对称 |

常见方向：`MTE2_V`（搬运→Vector）、`V_MTE2`（Vector→搬运，即搬出前等计算完成）、`MTE2_S`（搬运→Scalar）、`MTE3_V`，以及 `V_S`/`S_V` 等标量与向量之间的依赖。

## 约束与注意事项

- `SetFlag` 与 `WaitFlag` 必须成对使用**完全相同的模板参数（事件类型）与 eventID**，否则会出现等待超时（文档以显式告警给出）。
- 枚举条目的语义就是"源流水→目标流水"的依赖方向，不存在"任意两流水通用"的取值；写错方向等于同步到错误的流水。
- `HardEvent` 与 `HardEventAic`/`HardEventAiv` 是三个独立枚举：分离模式（AIC/AIV）下按核类型使用对应枚举，枚举值本身不互转。
- `FIX_V`/`V_FIX` 受架构宏控制，跨代代码不能无条件引用。

## 来源锚点

- 声明：`impl/basic_api/kernel_event.h:38-81`（HardEvent）、`:83-110`（HardEventAic）、`:112-128`（HardEventAiv）。
- 语义与配对约束：`docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag_WaitFlag_ISASI.md` 参数说明（`:58-66`）、约束说明（`:71-110`）；枚举/流水对照见同目录 `intra_core_sync_overview.md` 表2、表3。

## 相关 runbook

- [PipeBarrier 只支持 MTE2/V/MTE3 而非全部 PIPE_S](../../../../../runbooks/compilation/ol_35_pipebarrier_only_supports_mte2_v_mte3_not_pipe_s.md)
- [手写跨核 flag 交接（AIC/AIV 混合）](../../../../../runbooks/compilation/manual_crosscore_flag_handoff_mixed_aic_aiv.md)
