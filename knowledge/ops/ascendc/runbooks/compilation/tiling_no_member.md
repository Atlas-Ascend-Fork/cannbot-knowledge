---
type: "Runbook"
title: "手动 tiling 头遮蔽自动生成类致 no member 判别"
description: "JOIN_OP_DEF True 工程里，op_host 用 BEGIN_TILING_DATA_DEF 定义 TilingData 后构建系统会自动生成 kernel 侧同名类并经 kernel_tiling/kernel_tiling.h 注入；若 kernel 又手动 #include <op>_tiling.h 定义同名类、并 REGISTER_TILING_DEFAULT + reinterpret_cast 直接访问字段，编译报 no member named 'minBits'/'maxBits'/'scaleBits'。判别=核 kernel 是否同时存在手动 tiling 头与自动生成头、是否绕开 GET_TILING_DATA。"
tags: ["task.debugging", "topic.implementation.tiling", "topic.compilation"]
status: draft
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: []
aliases: ["kernel_tiling_h", "no_member_named"]
---

# 手动 tiling 头遮蔽自动生成类致 no member 判别

## 现象

在 Ascend 910B（CANN 8.5.0-beta.1，`JOIN_OP_DEF True` 代码生成路径）上开发 Histogram 自定义算子：op_host 用 `BEGIN_TILING_DATA_DEF` / `TILING_DATA_FIELD_DEF` 定义 `HistogramTilingData`，aclnn 接口由 judge 调用 `aclnnHistogramGetWorkspaceSize`。Kernel 文件 `op_kernel/histogram.cpp` 同时手动 `#include "histogram_tiling.h"`、在 `extern "C"` 入口里 `REGISTER_TILING_DEFAULT(HistogramTilingData)`、并 `reinterpret_cast<__gm__ HistogramTilingData*>(tiling)` 后直接访问 `tilingData->minBits` / `maxBits` / `scaleBits`。执行 `make` 构建时，op_host 的 `cust_optiling` 库与 op_info_cfg 正常生成，但到 kernel 代码生成阶段报：

```
op_kernel/histogram.cpp:27:47: error: no member named 'minBits' in 'HistogramTilingData'
          minValue_ = BitsToFloat(tilingData->minBits);
                                  ~~~~~~~~~~  ^
op_kernel/histogram.cpp:28:47: error: no member named 'maxBits' in 'HistogramTilingData'
op_kernel/histogram.cpp:29:44: error: no member named 'scaleBits' in 'HistogramTilingData'
```

随后 ld.lld 因 `.o` 未生成连锁报 `cannot open .../kernel_meta_Histogram_..._1.o: No such file or directory`，最终 `RuntimeError: Kernel Compilation Error`。

## 适用场景

- **工程形态**：自定义算子工程（ops-registry-invoke 风格，op_host + op_kernel + 手写 tiling 头），CANN 8.5.0-beta.1，`JOIN_OP_DEF True` 代码生成路径。
- **API 路径**：`BEGIN_TILING_DATA_DEF` / `TILING_DATA_FIELD_DEF`（op_host 侧定义）→ 构建系统 `get_op_tiling.py` 自动生成 kernel 侧 `HistogramTilingData` 类，经自动生成的 `kernel_tiling/kernel_tiling.h` 注入 kernel 编译单元；kernel 侧用 `GET_TILING_DATA` 宏从 GM 拷贝 tiling 到本地。
- **验证过的平台与 CANN 版本**：芯片 Ascend 910B（不在注册平台词表 `950/a3/a2` 中，故 `platforms: []` 未定位）；CANN 8.5.0-beta.1（构建路径 `cann-8.5.0-beta.1`）。
- **适用粒度**：`operator_family`——任何用 `BEGIN_TILING_DATA_DEF` + 手写 tiling 头的 `JOIN_OP_DEF True` 自定义算子均可能踩此坑。
- **路线优先级**：`diagnostic_only`——本卡只给判别方法与根因解释；修复实现的终版 kernel 代码未从 trace 逐字完整恢复。
- **不适用或未验证场景**：非 `JOIN_OP_DEF True` 的旧式算子工程（可能仍需手动 tiling 头）；CANN 9.x 的自动生成类成员可见性未在本 trace 验证。

## 根因

构建系统在 `JOIN_OP_DEF True` 下会从 op_host 的 `BEGIN_TILING_DATA_DEF` / `TILING_DATA_FIELD_DEF` 自动生成 **kernel 侧** `HistogramTilingData` 类（由 `get_op_tiling.py` 的 `get_dynamic_tiling_struct` 产生），并经自动生成的 `kernel_tiling/kernel_tiling.h` 注入 kernel 编译单元。Kernel 又手动 `#include "histogram_tiling.h"` 引入同名 `HistogramTilingData`，二者冲突——编译器看到的 `HistogramTilingData` 不是 kernel 直接 `->minBits` 所期望的形态，故 `no member named 'minBits'`。手动 `REGISTER_TILING_DEFAULT(HistogramTilingData)` 在 `GET_TILING_DATA` 路径下亦属多余/冲突注册。

机制链：op_host `BEGIN_TILING_DATA_DEF`（约束）↔ 构建系统自动生成 kernel 侧同名类 + `kernel_tiling/kernel_tiling.h` 注入 ↔ kernel 手动 `<op>_tiling.h` 再定义同名类（冲突）↔ 编译器解析到非预期形态 ↔ `no member named 'minBits'/'maxBits'/'scaleBits'` ↔ `.o` 缺失 ↔ 链接失败 ↔ Kernel Compilation Error。

## 判别方法

**触发条件**（tool_observed 失败症状）：`make` 构建到 kernel 代码生成阶段报 `error: no member named '<field>' in '<Op>TilingData'`（多个 tiling 字段同时报），并连锁引发 `cannot open .../<op>_kernel_..._.o: No such file or directory` 与 `Kernel Compilation Error`；而 op_host 的 `cust_optiling` 库与 op_info_cfg 阶段正常通过。

**可执行探针**：
1. 读 kernel 文件头部 `#include` 段，检查是否同时出现手动 `<op>_tiling.h` 与自动生成的 `kernel_tiling/kernel_tiling.h`。
2. 读 kernel `extern "C"` 入口段，检查是否出现 `REGISTER_TILING_DEFAULT(<Op>TilingData)` + `reinterpret_cast<__gm__ <Op>TilingData*>(tiling)` + 直接 `-><field>` 访问，而非 `GET_TILING_DATA(<var>, tiling)`。
3. 确认工程为 `JOIN_OP_DEF True`（CMakeLists/工程配置），即构建系统会自动生成 kernel 侧 tiling 类。
4. 三者同时成立即为根因：手动头遮蔽自动生成类，编译器看到的 `<Op>TilingData` 不含 kernel 直接访问的字段。

**原始观测**（Ascend 910B，CANN 8.5.0-beta.1，Histogram 自定义算子构建）：
- `make` 在 kernel 代码生成阶段对 `tilingData->minBits` / `maxBits` / `scaleBits` 三处分别报 `no member named`，op_host 阶段（`cust_optiling`、op_info_cfg）正常。
- 移除手动 `#include "histogram_tiling.h"` + `REGISTER_TILING_DEFAULT` 并改用 `GET_TILING_DATA` 后，下一次构建的编译错清单中 `minBits` / `maxBits` / `scaleBits` 类 `no member named` 错误**不再出现**（仅剩 `GET_TILING_DATA` 首参误用导致的 `no matching function for call to 'InitTilingData'`，属另一独立问题）。
- `minBits` 类错误消失即证明手动头与自动生成类的冲突是 `no member named 'minBits'` 的根因，而非字段名拼写或 op_host 定义缺字段。

**机制解释**（根因分析，属 interpretation）：`JOIN_OP_DEF True` 下构建系统从 op_host 的 `BEGIN_TILING_DATA_DEF` 自动生成 kernel 侧 `<Op>TilingData` 类（经 `kernel_tiling/kernel_tiling.h` 注入），该自动生成类对 kernel 侧暴露了 `minBits` 等字段（移除手动头后直接访问不再报错即可反证）。手动 `<op>_tiling.h` 再定义同名类形成遮蔽，编译器解析到的定义不含 kernel 直接访问的字段，故报 `no member named`。判别核心是"手动头与自动生成头并存 + 绕开 `GET_TILING_DATA` 直接 `->` 访问"，而非 op_host 字段定义缺失或字段名错误。

## 预防

- 在 `JOIN_OP_DEF True` 工程里，kernel 侧不要手动 `#include "<op>_tiling.h"`、不要 `REGISTER_TILING_DEFAULT`；tiling 数据经自动生成的 `kernel_tiling/kernel_tiling.h` + `GET_TILING_DATA` 获取本地拷贝。
- `GET_TILING_DATA` 首参是变量名而非类型名（误传类型名会声明同名变量遮蔽类型，引发 `InitTilingData` 模板实参失效）。
- 以 built-in 同名算子 kernel（`opp/built-in/op_impl/ai_core/tbe/impl/...`）为参照模板确认 tiling 访问模式：built-in `histogram_v2` kernel 不手动 include tiling 头、用 `GET_TILING_DATA` 取本地拷贝。

## 验证信号

- `make` 构建在 kernel 代码生成阶段对 `tilingData->minBits` / `maxBits` / `scaleBits` 报 `no member named '...' in 'HistogramTilingData'`，op_host 阶段正常（来源平台：未定位（Ascend 910B，不在注册词表）；证据等级：tool_observed）
- 移除手动 `#include "histogram_tiling.h"` + `REGISTER_TILING_DEFAULT` 并改用 `GET_TILING_DATA` 后，下一次构建编译错清单中 `minBits` / `maxBits` / `scaleBits` 类 `no member named` 错误消失（来源平台：未定位；证据等级：tool_observed）

## 失效边界

- 推断可迁移至同样使用 `BEGIN_TILING_DATA_DEF` + `JOIN_OP_DEF True` 的 CANN 8.5/9.x 自定义算子工程——未验证，推断可迁移。
- 非 `JOIN_OP_DEF True` 或不自动生成 kernel 侧 tiling 类的旧路径，可能仍需手动 tiling 头——未验证。
- CANN 9.x 自动生成类的成员可见性（public vs private+getter）未在本 trace 验证，迁移时应先读生成的 `tiling_data.h` 确认字段访问方式。

## 坏实践

- 同时保留手动 tiling 头 + 自动生成头，依赖"哪个先 include"的未定义顺序来决定可见的 `<Op>TilingData` 定义——必然踩 `no member named X` 编译错。
- 看到 `no member named 'minBits'` 就去 op_host 的 `BEGIN_TILING_DATA_DEF` 里改字段名或补字段，不先核 kernel 是否手动引入了冲突的同名 tiling 头。

<!-- cannbot:related:start -->
## 相关

- [COPY_TILING_WITH_STRUCT](../../apis/simd_api/basic_api/kernel_tiling/copy_tiling_with_struct.md)（`exemplifies`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；手动 tiling 头遮蔽自动生成类致 no member 判别正文说明“JOIN_OP_DEF True 工程里，op_host 用 BEGIN_TILING_DATA_DEF 定义 TilingData 后构建系统会自动生成 kernel 侧同名类并经 kernel_tiling/kernel_tiling.h 注入；若 kernel 又手动 #i”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [Kernel Tiling](../../apis/simd_api/basic_api/kernel_tiling/kernel_tiling.md)（`exemplifies`）：手动 tiling 头遮蔽自动生成类致 no member 判别说明JOIN_OP_DEF True 工程里，op_host 用 BEGIN_TILING_DATA_DEF 定义 TilingData 后构建系统会自动生成 kernel 侧同名类并经 kernel_tiling/kernel_tiling.h 注入；若 kernel 又手动 #include <op>_tiling.h 定义同名类、并 REGISTER_TILING_DEFAULT + reinterpret_cast 直接访问字段，编译报 no member named 'minBits'/'maxBits'/'scaleBits'。判别=核 kernel 是否同时存在手动 tiling 头与自动生成头、是否绕开 GET_TILING_DATA。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](register_tiling_default_struct.md)（`related`）：focal 的冲突注册来自自动生成类上再次占用 default；该卡进一步给出一个算子不同 struct 只能有一个 default、其余须按 TilingKey 注册的框架约束。
- [RmsNormTiling 与 CANN 内置类型冲突 — 改名隔离](tiling_type_name_does_not_shadow_cann_builtin.md)（`related`）：两卡都涉及公共/自动生成 tiling 类型与本地同名定义相遇；目标卡以字段解析到错误类型的 no-member 表现，本卡以 using target 冲突和 ambiguous 表现。
- [TILING_DATA_DEF 迁移 rebase 字段失配判别](tiling_data_def_rebase.md)（`related`）：两卡都以 kernel 所需字段不在实际注入的 TilingData 类型中为判据；目标卡补充自动生成类被手写同名类遮蔽时的 no-member 分流。
- [rebase 引入新 kernel 文件旧 tiling 类型致编译失败](rebase_kernel_tiling.md)（`related`）：两类问题都会报 tiling 字段/类型不存在，但该卡补充了手写头遮蔽自动生成类这一不同根因，可用于区分 rebase 残留与 include 遮蔽。
- [GET_TILING_DATA 首参传类型名致变量遮蔽类型](get_tiling_data.md)（`same_topic`）：移除手动 tiling 头与多余 REGISTER_TILING_DEFAULT 后，下一条确定错误正是 GET_TILING_DATA 首参传类型名；两卡串成同一次迁移的连续诊断链。
- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](get_tiling_data_with_struct.md)（`same_topic`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《手动 tiling 头遮蔽自动生成类致 no member 判别》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [TilingData 须 host 与 kernel 各定义一份](tilingdata_host_kernel.md)（`same_topic`）：TilingData 须 host 与 kernel 各定义一份：本故障来自host不可见kernel侧struct；TilingData定义/注册/属性传递卡给出正式契约，struct.h include与手写头遮蔽、rebase字段失配卡覆盖同一双侧类型同步链的具体失败。 目标卡《手动 tiling 头遮蔽自动生成类致 no member 判别》补充：JOIN_OP_DEF True 工程里，op_host 用 BEGIN_TILING_DATA_DEF 定义 TilingData 后构建系统会自动生成 kernel 侧同名类并经 kernel_tiling/kernel_tiling.h 注入；若 kernel 又手动 #include <op>_tiling.h 定义同名类、并 REGISTER_TILING_DEFAULT + reinterpret_cast 直接访问字段，编
<!-- cannbot:related:end -->
