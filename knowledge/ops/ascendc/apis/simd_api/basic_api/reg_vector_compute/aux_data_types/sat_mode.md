---
type: API
title: SatMode
description: SatMode 用于设置 Cast 类型转换的饱和与不饱和模式，包括 UNKNOWN、NO_SAT 和 SAT。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/SatMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: [agnostic]
---

# SatMode

SatMode 用于设置 Cast 类型转换的饱和与不饱和模式。

本接口属于 Reg 矢量计算辅助数据类型定义。

```cpp
enum class SatMode {
    UNKNOWN = -1,
    NO_SAT,
    SAT
};
```

- `UNKNOWN`：转换类型不支持显式 SatMode 时使用。
- `NO_SAT`：不饱和模式。
- `SAT`：饱和模式；溢出和非有限值行为仍需按具体 Cast 接口与数据类型核对。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失](../../../../../runbooks/precision/cast_satmode_sat_fp16_nan_inf.md)（`exemplifies`）：SatMode 用于设置 Cast 类型转换的饱和与不饱和模式。 即高层 `AscendC::Cast` 对所有 b16↔fp32 转换强制 `SatMode::SAT`（饱和），底层 `Reg::Cast` 指令同样饱和。 Runbook 用 NaN/Inf 变为 65504 的实测信号具体化 SAT 后果，并说明 trait 调参无法恢复已丢失的非有限值。
- [HiFloat8 SatMode::SAT Cast NaN 映射 0x00](../../../../../runbooks/precision/hifloat8_satmode_sat_cast_nan_0x00.md)（`exemplifies`）：**触发条件（trigger）**：对使用 `Cast<hifloat8_t, float, castTraitF32toh8>`（SatMode::SAT）做 fp32→hifloat8 量化的算子，用全 NaN 输入跑 golden-vs-device 字节级比对，HiFloat8 路径 FAIL/SUPPRESSED，而同输入下其他量化模式（如 MX-FP8、Normal）PASS。；SatMode 用于设置 Cast 类型转换的饱和与不饱和模式。。runbook 的 NaN 字节差异由具体 HiFloat8 Cast 的 SatMode::SAT 路径触发，辅助类型卡提供选择饱和/不饱和模式的枚举入口，联合阅读可从失败信号回到 Cast trait 配置。
<!-- cannbot:related:end -->
