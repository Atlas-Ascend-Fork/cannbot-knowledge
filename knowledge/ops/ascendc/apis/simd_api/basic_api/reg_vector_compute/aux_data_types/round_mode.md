---
type: API
title: RoundMode
description: 枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/RoundMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# RoundMode<a name="ZH-CN_TOPIC_0000001956862301"></a>

| 参数名 | 描述 |
| :-- | :-- | 
| RoundMode | 用于设置控制舍入模式。<br>enum class RoundMode { <br>    CAST_NONE = 0, <br>    CAST_RINT, <br>    CAST_FLOOR,<br>    CAST_CEIL,<br>    CAST_ROUND,<br>    CAST_TRUNC,<br>    CAST_ODD,<br>    CAST_HYBRID <br>};<br>&bull;&nbsp;&nbsp;CAST_NONE：当转换过程存在精度损失时，按 CAST_RINT 模式处理；当不存在精度损失时，不进行舍入。<br>&bull;&nbsp;&nbsp;CAST_RINT：向最近的偶数舍入。<br>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;若待舍入部分的首位为 0，则不进位。<br>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;若待舍入部分的首位为 1 且后续位不全为 0，则进位。<br>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;若待舍入部分的首位为 1 且后续位全为 0：当非舍入部分的末位为 0，则不进位。当非舍入部分的末位为 1，则进位。<br>&bull;&nbsp;&nbsp;CAST_FLOOR：向负无穷大方向舍入。<br>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;若符号位（S）为 0（正数），不进位。<br>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;若符号位（S）为 1（负数）：当待舍入部分全为 0，则不进位。否则，进位。<br>&bull;&nbsp;&nbsp;CAST_CEIL：向正无穷大方向舍入。<br>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;若符号位（S）为 1（负数），不进位。<br>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;若符号位（S）为 0（正数）：当待舍入部分全为 0，则不进位。否则，进位。<br>&bull;&nbsp;&nbsp;CAST_ROUND： 四舍五入。若待舍入部分的首位为0，则不进位。否则，进位。<br>&bull;&nbsp;&nbsp;CAST_TRUNC： 直接丢弃待舍入部分。<br>&bull;&nbsp;&nbsp;CAST_ODD：向最近的奇数舍入。<br>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;若待舍入部分全为 0，则不进位。<br>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;若待舍入部分不全为 0：非舍入部分的末位为 1，则不进位。当非舍入部分的末位为 0，则进位。<br>&bull;&nbsp;&nbsp;CAST_HYBRID：随机舍入，目前特指输出结果是hifloat8_t数据类型时的随机舍入。 |

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


<!-- cannbot:related:start -->
## 相关

- [Reg CastTrait RoundMode 命名空间编译失败](../../../../../runbooks/compilation/casttrait_roundmode_is_in_ascendc.md)（`exemplifies`）：枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。；只把两个 `RoundMode` 限定名从 `AscendC::Reg` 提升到 `AscendC`；其余 Reg 枚举、trait 的函数内 `static constexpr` 形态和三段计算逻辑全部保留。；目标卡把焦点枚举用于 CastTrait，并给出错误限定名的最小编译修复。
- [bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别](../../../../../runbooks/precision/bf16_cast_cast_rint.md)（`exemplifies`）：枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。；- **扩精度方向**（half/bfloat16 → float，位数增加、无信息丢失、不需要舍入）：`CAST_NONE` 合法且正确。官方 `top_k_top_p_sample.h:619` 对 `half/bfloat16 -> float32` 用 `CAST_NONE` 实证。；目标卡将焦点枚举落实到 bf16 扩精度方向的正确取值和实证验证。
- [f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言](../../../../../runbooks/compilation/reg_cast_f32_to_s64_uses_supported_rounding.md)（`exemplifies`）：`CAST_NONE` 在这条 f32→s64 VCONV 实例化中对应不受支持的舍入编码。；枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。。Runbook 定位 f32→s64 不能使用 CAST_NONE 并改用 CAST_TRUNC，RoundMode 卡给出可配置舍入枚举；联合阅读可从编译静态断言回到合法 trait 选择。
- [FastGelu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/fast_gelu_950.md)（`related`）：“源码把整数 0 转为 `RoundMode`”标出 FastGelu 升精度 Cast 的枚举解释边界；“`CAST_NONE`：无精度损失时不舍入；存在精度损失时按 `CAST_RINT` 处理。”提供数值 0 对应模式的语义，用于核验转换路径。
<!-- cannbot:related:end -->
