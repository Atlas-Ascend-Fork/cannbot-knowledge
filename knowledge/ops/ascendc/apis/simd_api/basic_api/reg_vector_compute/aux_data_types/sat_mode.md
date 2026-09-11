---
type: API
title: SatMode
description: SatMode 用于设置 Cast 类型转换的饱和与不饱和模式，包括 UNKNOWN、NO_SAT 和 SAT。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/SatMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# SatMode<a name="ZH-CN_TOPIC_0000001956862301"></a>

| 参数名 | 描述 |
| :-- | :-- | 
| SatMode | 用于设置Cast类型转换饱和与不饱和模式。<br>enum class SatMode { <br>    UNKNOWN = -1, <br>    NO_SAT, <br>    SAT <br>};<br>&bull;&nbsp;&nbsp;UNKNOWN：当转换类型不支持SatMode时，选择该模式；<br>&bull;&nbsp;&nbsp;NO_SAT：不饱和模式；<br>&bull;&nbsp;&nbsp;SAT：饱和模式。 |

```cpp
enum class SatMode {
    UNKNOWN = -1,
    NO_SAT,
    SAT
};
```


<!-- cannbot:related:start -->
## 相关

- [Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失](../../../../../runbooks/precision/cast_satmode_sat_fp16_nan_inf.md)（`exemplifies`）：SatMode 用于设置 Cast 类型转换的饱和与不饱和模式。 即高层 `AscendC::Cast` 对所有 b16↔fp32 转换强制 `SatMode::SAT`（饱和），底层 `Reg::Cast` 指令同样饱和。 Runbook 用 NaN/Inf 变为 65504 的实测信号具体化 SAT 后果，并说明 trait 调参无法恢复已丢失的非有限值。
- [HiFloat8 SatMode::SAT Cast NaN 映射 0x00](../../../../../runbooks/precision/hifloat8_satmode_sat_cast_nan_0x00.md)（`exemplifies`）：**触发条件（trigger）**：对使用 `Cast<hifloat8_t, float, castTraitF32toh8>`（SatMode::SAT）做 fp32→hifloat8 量化的算子，用全 NaN 输入跑 golden-vs-device 字节级比对，HiFloat8 路径 FAIL/SUPPRESSED，而同输入下其他量化模式（如 MX-FP8、Normal）PASS。；SatMode 用于设置 Cast 类型转换的饱和与不饱和模式。。runbook 的 NaN 字节差异由具体 HiFloat8 Cast 的 SatMode::SAT 路径触发，辅助类型卡提供选择饱和/不饱和模式的枚举入口，联合阅读可从失败信号回到 Cast trait 配置。
<!-- cannbot:related:end -->
