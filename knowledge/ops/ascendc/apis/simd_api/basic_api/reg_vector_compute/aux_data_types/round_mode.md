---
type: API
title: RoundMode
description: 枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/RoundMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: [agnostic]
---

# RoundMode

枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。

本接口属于 Reg 矢量计算辅助数据类型定义。

```cpp
enum class RoundMode {
    CAST_NONE = 0,
    CAST_RINT,
    CAST_FLOOR,
    CAST_CEIL,
    CAST_ROUND,
    CAST_TRUNC,
    CAST_ODD,
    CAST_HYBRID
};
```

- `CAST_NONE`：无精度损失时不舍入；存在精度损失时按 `CAST_RINT` 处理。
- `CAST_RINT`：舍入到最近的偶数。
- `CAST_FLOOR` / `CAST_CEIL`：分别向负无穷和正无穷方向舍入。
- `CAST_ROUND`：四舍五入；`CAST_TRUNC`：向零截断。
- `CAST_ODD` 与 `CAST_HYBRID` 只在相应接口和数据类型支持矩阵中使用，不能仅凭枚举存在推断可用。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Reg CastTrait RoundMode 命名空间编译失败](../../../../../runbooks/compilation/casttrait_roundmode_is_in_ascendc.md)（`exemplifies`）：枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。；只把两个 `RoundMode` 限定名从 `AscendC::Reg` 提升到 `AscendC`；其余 Reg 枚举、trait 的函数内 `static constexpr` 形态和三段计算逻辑全部保留。；目标卡把焦点枚举用于 CastTrait，并给出错误限定名的最小编译修复。
- [bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别](../../../../../runbooks/precision/bf16_cast_cast_rint.md)（`exemplifies`）：枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。；- **扩精度方向**（half/bfloat16 → float，位数增加、无信息丢失、不需要舍入）：`CAST_NONE` 合法且正确。官方 `top_k_top_p_sample.h:619` 对 `half/bfloat16 -> float32` 用 `CAST_NONE` 实证。；目标卡将焦点枚举落实到 bf16 扩精度方向的正确取值和实证验证。
- [f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言](../../../../../runbooks/compilation/reg_cast_f32_to_s64_uses_supported_rounding.md)（`exemplifies`）：`CAST_NONE` 在这条 f32→s64 VCONV 实例化中对应不受支持的舍入编码。；枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。。Runbook 定位 f32→s64 不能使用 CAST_NONE 并改用 CAST_TRUNC，RoundMode 卡给出可配置舍入枚举；联合阅读可从编译静态断言回到合法 trait 选择。
- [FastGelu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/fast_gelu_950.md)（`related`）：“源码把整数 0 转为 `RoundMode`”标出 FastGelu 升精度 Cast 的枚举解释边界；“`CAST_NONE`：无精度损失时不舍入；存在精度损失时按 `CAST_RINT` 处理。”提供数值 0 对应模式的语义，用于核验转换路径。
<!-- cannbot:related:end -->
