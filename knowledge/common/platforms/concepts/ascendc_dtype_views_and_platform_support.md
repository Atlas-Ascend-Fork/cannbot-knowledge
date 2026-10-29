---
type: Concept
title: AscendC 数据类型视图与平台支持范围
description: 区分 AscendC 的 dtype 简写、逻辑 C++ 类型、打包存储单元与产品清单；核对 950PR/950DT 与 Atlas A2/A3 的 bool、S4、FP4/FP8 及复数清单差异，并按接口要求换算 32B 长度倍数，不以清单替代具体 API 的支持判断。
tags:
- task.lookup
- task.design
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/docs/zh/api/SIMD-API/basic_api/data_structures/builtin_data_types.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/asc-npu-arch/references/npu-arch-facts.json
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/asc-npu-arch/references/npu-arch-guide.md
  role: supporting
created_at: '2026-10-23T02:00:00Z'
updated_at: '2026-10-27T19:50:00Z'
platforms:
- a2
- a3
- '950'
---

# AscendC 数据类型视图与平台支持范围

同一个数据类型在 AscendC 材料里有四个视图：文档**简写**（`FP16`、`S4`）、**逻辑/语言类型**（`half`、`int4b_t`）、**存储单元**（两个 4-bit 值可打包为一个 8-bit 单元），以及**产品清单**。四者不总是一一对应。本卡优先采用固定提交的内置数据类型原文；同一提交的派生 JSON 和 guide 与原文清单不一致的地方在下文标出。

## 1. 四个视图

| 视图 | 载体 | 典型形态 | 使用场合 |
|------|------|----------|----------|
| 简写 | 设计文档、表格 | `FP16`、`U8`、`S4` | 人读；**不是** C++ 类型名 |
| 语言类型 | 代码、API 声明 | `half`、`int4x2_t` | 声明、模板参数、类型转换 |
| 存储 | 打包类型 / 字节数 | 1/2/4/8 字节、32B 长度换算 | buffer 计算、tiling、样例数据 |
| 平台 | 产品系列清单 | Ascend 950PR&950DT、Atlas A2/A3 | 初筛产品清单；仍需核对目标 API |

固定来源的 guide 汇总芯片调用名与 dtype 大小；但产品清单应回到其引用的原始文档核对，具体接口仍要核对声明和实现。

## 2. 简写 → 真实类型

| 简写 | 代码中应使用的真实类型 | 备注 |
|------|------------------------|------|
| `S4` | `int4b_t`（逻辑值）；打包时用 `int4x2_t` | 4-bit 有符号整数；存储类型与逻辑类型不同 |
| `U8` / `S8` | `uint8_t` / `int8_t` | 8-bit 无符号 / 有符号整数 |
| `U16` / `S16` | `uint16_t` / `int16_t` | 16-bit 整数 |
| `U32` / `S32` | `uint32_t` / `int32_t` | 32-bit 整数 |
| `U64` / `S64` | `uint64_t` / `int64_t` | 64-bit 整数 |
| `FP8_E4M3` | `fp8_e4m3fn_t` | 8-bit 浮点，4 位指数 / 3 位尾数 |
| `FP8_E5M2` / `FP8_E8M0` | `fp8_e5m2_t` / `fp8_e8m0_t` | 8-bit 浮点格式 |
| `FP4_E2M1` / `FP4_E1M2` | `fp4x2_e2m1_t` / `fp4x2_e1m2_t` | 每个存储单元打包两个 4-bit 值 |
| `HiF8` | `hifloat8_t` | 自定义 8-bit 浮点 |
| `FP16` | `half` | 16-bit 浮点 |
| `BF16` | `bfloat16_t` | 16-bit 浮点，8 位指数 / 7 位尾数 |
| `FP32` | `float` | 32-bit 浮点 |

简写只用于读懂设计文档或表格；写代码须按目标 API 的声明选择类型。`FP16`/`BF16`/`FP32` 对应 `half`/`bfloat16_t`/`float`。`S4` 对应的逻辑类型 `int4b_t` 不是打包单元 `int4x2_t` 的别名。

## 3. 存储视图：sizeof 与 32B 对齐元素数

| 存储位宽 | 存储类型 | 存储单元字节数 | 32B 长度对应的存储单元数 |
|------|------|:------:|:-------------:|
| 8-bit | `bool`、`int8_t`、`uint8_t`、`fp4x2_e2m1_t`、`fp4x2_e1m2_t`、`hifloat8_t`、`fp8_e5m2_t`、`fp8_e4m3fn_t`、`fp8_e8m0_t`、`int4x2_t` | 1 字节 | 32 |
| 16-bit | `half`、`bfloat16_t`、`int16_t`、`uint16_t` | 2 字节 | 16 |
| 32-bit | `float`、`int32_t`、`uint32_t`、`complex32` | 4 字节 | 8 |
| 64-bit | `double`、`int64_t`、`uint64_t`、`complex64` | 8 字节 | 4 |

上表只列出固定来源 JSON 给出 `size` 的 22 种存储类型，不把 4-bit 逻辑值 `int4b_t` 误记为 1 字节的 `sizeof`。当具体接口要求搬运长度为 32B 整数倍时，若 `count` 是存储单元数，需满足 `count * size_bytes % 32 == 0`；这是长度条件，不等于首地址对齐，也不是所有接口的统一合法性要求。两条容易漏的细节：

- `fp4x2_e2m1_t`、`fp4x2_e1m2_t`、`int4x2_t` 按 8-bit 存储单元计算：一个存储单元打包两个 4-bit 值，因此 32B 对应 32 个存储单元、即 64 个 4-bit 值。计算 N 个逻辑 4-bit 值时应分配 `ceil(N/2)` 个 8-bit 打包单元，再按具体接口补齐；半字节换算本身并非错误，关键是区分逻辑元素与存储单元。
- 32B 对齐元素数随 dtype 变化（32 / 16 / 8 / 4），换 dtype 时基于元素个数的 tiling 常量需要重算。

## 4. 平台支持差异

| 产品范围 | 文档声明的支持 dtype | 数量 |
|----------|----------------------|:----:|
| Ascend 950PR & 950DT 系列 | `bool`、`int4b_t`、`int4x2_t`、`int8_t`、`uint8_t`、`fp4x2_e2m1_t`、`fp4x2_e1m2_t`、`hifloat8_t`、`fp8_e8m0_t`、`fp8_e5m2_t`、`fp8_e4m3fn_t`、`int16_t`、`uint16_t`、`half`、`bfloat16_t`、`int32_t`、`uint32_t`、`float`、`complex32`、`int64_t`、`uint64_t`、`double`、`complex64` | 23（含逻辑类型 `int4b_t`） |
| Atlas A2 / A3 系列（原文分别列出，名单相同） | `bool`、`int4b_t`、`int8_t`、`uint8_t`、`int16_t`、`uint16_t`、`half`、`bfloat16_t`、`int32_t`、`uint32_t`、`float`、`int64_t`、`uint64_t`、`double` | 各 14（含逻辑类型 `int4b_t`） |

原文还分别列有 Atlas 200I/500 A2 推理、Atlas 推理系列 AI Core/Vector Core 与 Atlas 训练系列的名单；本表只对照 950 与 Atlas A2/A3，不据此概括其他产品。原文与派生资料的差异集中在三处：

1. **`bool` 与 `int4b_t` 在两边的原始名单中都有。** 派生 JSON 的 950 清单漏 `int4b_t`，A2/A3 清单还漏 `bool`。`int4b_t` 是逻辑类型，不能由其产品清单项推断它有独立的字节大小或任何 API 都接受它。
2. **FP4/FP8、HiFloat8 与 `int4x2_t` 仅在 950 的这两行对照中出现。** A2/A3 原文列 `int4b_t`，但没有列出打包类型 `int4x2_t`，不能把两者互换或由缺行推断所有 API 禁用打包。
3. **复数类型只出现在 950 的这两行对照中。** 原文的复数段落也写明当前仅 950PR/950DT 支持；派生 guide 则写“910_95”，两种口径不能合并为更宽的支持范围。

原文 950 名单是 23 项（包括逻辑 `int4b_t`），派生 JSON 的 22 种存储类型与它不可直接作数量等同。产品清单不保证所有 API 接受对应类型；仍须查目标 API 的声明、实现与已有用例。

## 5. 初始化能力：独立于产品清单的维度

按原文所列“支持使用立即数赋值和初始化”的类型，以及派生 guide 的通用 UT 策略，可分三组。这是 UT 样例构造策略，与产品清单是两个独立维度：

| 分组 | 类型 | 使用规则 |
|------|------|----------|
| 可直接初始化 | `bool`、`int8_t`、`uint8_t`、`int16_t`、`uint16_t`、`half`、`int32_t`、`uint32_t`、`float`、`int64_t`、`uint64_t` | 通用 UT 模板可安全构造样例数据 |
| 通用 UT 需特化 | `bfloat16_t`、`double`、`complex32`、`complex64` | 原文的立即数支持清单未列入；并非 C++ 禁止初始化（原文还给出 `complex64 value2 = 4;`），按目标 API 的路径核对 |
| 低精度逻辑值、打包 / 8-bit 浮点 | `int4b_t`、`fp4x2_e2m1_t`、`fp4x2_e1m2_t`、`hifloat8_t`、`fp8_e5m2_t`、`fp8_e4m3fn_t`、`fp8_e8m0_t`、`int4x2_t` | 需确认逻辑值和打包布局、转换 API 与目标 API 支持范围 |

"可直接初始化"只表示通用 UT 模板可以构造出样例数据，不表示任意 API 都支持该类型。

## 6. 常见误用

1. **把简写当类型写进代码**：`FP16 x;`、`S4 v;` 中的 `FP16`、`S4` 是文档简写；应依据接口选用 `half`、`int4b_t` 或 `int4x2_t`（后两者取决于逻辑值/打包存储语义）。
2. **用逻辑 `int4b_t` 推算打包 buffer 的 `sizeof`**：`S4` 的单个逻辑值范围为 `[-8, 7]`；两个值打包时按一个 `int4x2_t` 8-bit 单元计算容量，单个 `int4b_t` 不能直接代入存储表的字节数。
3. **由产品清单推断具体 API**：原文另列其他产品清单；本卡只展开两种产品范围，其他目标应回原文逐项确认，同时核对 API 文档、声明、实现与 UT。
4. **把"类型在清单里"当成"所有 API 都支持"**：类型级支持不等于接口级支持。新增 dtype 支持时，声明、实现、文档、UT 和示例要同步检查。
5. **混淆 32B 长度倍数与地址对齐**：仅在目标接口要求长度为 32B 整数倍时按存储单元数检查 `count * size_bytes % 32 == 0`；首地址约束另行核对，换 dtype 后换算量（32 / 16 / 8 / 4）也需重算。
6. **把"低精度更省"直接当结论**：低精度类型还带打包布局、转换路径与特殊值语义问题，使用前必须确认打包顺序、转换 API 与 golden 生成方式。

## 7. 失效边界

- 本卡的对照只取原文 950PR/950DT、Atlas A2 与 A3 的三行；原文还有其他产品清单，本卡不替它们下结论。产品列表漏项也不能单独证明某个 API 禁用该类型。
- 复数在固定原文的产品清单和复数章节均限定 950PR/950DT；同一提交的派生 guide 的“910_95”口径与之不一致。生成 UT 前按目标 API 和本地实现确认，不据派生口径扩大本卡的平台范围。
- 本卡只给 dtype 层结论，不含"具体 API 接受哪些 dtype"、精度/误差、量化格式、Triton 侧类型名等结论。
- 架构分支条件编译（`__NPU_ARCH__`）不在本卡范围；文档未声明的芯片范围不应加入条件编译分支。

## 8. 与相邻卡的分工

- [NPU 内存层次与数据通路模型](npu_memory_model.md)：从存储空间（GM/L1/UB/L0A/L0B/L0C）角度看容量、数据通路与对齐。32B 对齐在那张卡是存储空间的通用要求，在本卡是 dtype 尺寸到元素数的换算；定位"buffer 放不下"先看那张卡，定位"这个类型能不能用、多大、怎么对齐"看本卡。
- [内置数据类型（数据结构）](../../../ops/ascendc/apis/simd_api/basic_api/data_structures/builtin_data_types.md)：逐类型的位域、取值范围、产品清单与复数定义等原文细节。本卡只做四个视图的换算、选定产品的清单对照与误用边界，不重复位域表和取值公式。
- [数据类型支持矩阵（Data Type Support Matrix）](../../../ops/triton/apis/data_type_matrix.md)：Triton-Ascend 的 `tl.*` 类型体系及其 load/store、dot、cast、原子操作支持矩阵。那是另一套 DSL 的类型名与支持口径，本卡不做 AscendC 与 Triton 之间的类型映射，需要跨 DSL 对照时以那张卡为准。
- [Duplicate 支持类型分档：arch22 无 int8/int64](../../../ops/ascendc/runbooks/compilation/duplicate_dtype_support_arch22_arch35.md)：单个 API 的 dtype 支持面按架构分档的实例——同一类型在 arch22 与 arch35 上可用性不同。它印证第 6 节第 4 条的"类型级支持 ≠ 接口级支持"：判断某 API 能否用某 dtype，要查对应架构目录下的实现，而不是只看本卡的 dtype 清单。
