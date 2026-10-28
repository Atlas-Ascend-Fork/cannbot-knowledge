---
type: Concept
title: AscendC 芯片别名与 NpuArch 映射表
description: AscendC 统一芯片调用名、产品系列别名（A2/A3/A5）、SocVersion 与 __NPU_ARCH__ 数值的对应关系，以及为什么产品名不能直接推断接口支持面、映射漂移时从哪里发现。
tags:
- task.lookup
- task.migration
- topic.architecture
status: stable
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/asc-npu-arch/references/npu-arch-facts.json
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/asc-npu-arch/references/npu-arch-guide.md
  role: supporting
created_at: '2026-10-23T02:00:00Z'
updated_at: '2026-10-26T01:55:14Z'
platforms: [a2, a3, '950', '310p', '910']
---

# AscendC 芯片别名与 NpuArch 映射表

一张卡上的同一颗芯片可能同时有四种"名字"：设备面板上的产品名、文档与脚本里的统一调用名、软件层的 SocVersion 字符串、以及决定指令集与条件编译的架构号。本卡给出这四者之间的登记映射，并说明为什么**不能**从产品名直接推出接口支持面，以及映射发生漂移时如何发现。

## 定义：四个不同层次的标识

| 标识 | 形态 | 定位 |
|---|---|---|
| 产品名 / 芯片型号 | `Ascend910B3`、`Ascend950PR`、`Ascend310P3`、Atlas A5 | 人读的机型名，出现位置最杂（设备面板、设计文档、算子包路径） |
| 统一调用名 | `ascend910`、`ascend910b1`、`ascend310p`、`ascend950pr_9599` | 各 skill、脚本、测试应优先复用的入参名或文档名 |
| SocVersion | `ASCEND910`、`ASCEND910B`、`ASCEND310P`、`ASCEND310B`、`ASCEND950` | 片上系统版本，软件命名标识 |
| NpuArch / `__NPU_ARCH__` | `1001`、`2002`、`2201`、`3002`、`3510` | 芯片架构号，定义指令集与微架构；四位数值，同时是 Device 侧条件编译宏 |

除上表四层之外，还有一层产品系列别名（A2 / A3 / A5）。它只在来源的人读章节里出现，不属于机器可消费事实——见下文"失效边界"。

## 主映射表

| 统一调用名 | 别名 / 产品系列 | SocVersion | `__NPU_ARCH__` | 来源登记的芯片型号 |
|---|---|---|---|---|
| `ascend910` | Atlas 训练系列 | `ASCEND910` | 1001 | Ascend910 |
| `ascend910b1` | A2 / Atlas A2 训练·推理 | `ASCEND910B` | 2201 | Ascend910B1~B4、Ascend910B2C |
| （未单独登记） | A3 / Atlas A3 训练·推理 | `ASCEND910B` | 2201 | Ascend910_93 |
| `ascend310p` | Atlas 推理系列 | `ASCEND310P` | 2002 | Ascend310P1、Ascend310P3 |
| `ascend610` | Atlas 推理系列 | `ASCEND310P` | 2002 | Ascend610 |
| `ascend310b1` | Atlas 200I/500 A2 推理 | `ASCEND310B` | 3002 | Ascend310B1~B4 |
| `ascend950pr_9599` | A5 / Atlas A5 推理 | `ASCEND950` | 3510 | Ascend950PR |
| （未单独登记） | A5 / Atlas A5 训练 | `ASCEND950` | 3510 | Ascend950DT |

注：来源只在 `ascend910b1` 条目上标注"与 A3 共用 2201"，A3 与 Ascend950DT 都**没有**自己的统一调用名条目——A2/A3 同属 `ASCEND910B`、两台 A5 机型同属 `ASCEND950`，只能通过产品系列行区分。Ascend950DT 也只登记在来源的人读映射表里，机器入口 `chips` 中没有对应条目。

## 结构化字段：`enum_name` 与 `arch_dir`

机器入口为每个统一调用名同时登记枚举名与算子样例目录名，二者都是调用名的派生，不是新的架构事实：

| 统一调用名 | `enum_name` | `arch_dir` |
|---|---|---|
| `ascend910` | `ASCEND910` | `ascendc_case_ascend910` |
| `ascend910b1` | `ASCEND910B1` | `ascendc_case_ascend910b1` |
| `ascend310p` | `ASCEND310P` | `ascendc_case_ascend310p` |
| `ascend610` | `ASCEND610` | `ascendc_case_ascend610` |
| `ascend310b1` | `ASCEND310B1` | `ascendc_case_ascend310b1` |
| `ascend950pr_9599` | `ASCEND950PR_9599` | `ascendc_case_ascend950pr_9599` |

## 映射的结构性质：多对多，不是一对一

- **一个架构号对应多个芯片型号或产品系列**。2201 同时覆盖 A2（910B1~B4、910B2C）与 A3（910_93）；2002 同时覆盖 310P1/P3 与 610。
- **一个统一调用名覆盖一整个型号区间**。`ascend910b1` 代表 B1~B4 与 B2C 一族，`ascend310b1` 代表 B1~B4 一族——拿到 `ascend910b1` 不等于拿到了具体型号。
- **目录名不能当架构判据**。`ascendc_case_ascend310p` 与 `ascendc_case_ascend610` 是两个不同目录，架构号同为 2002；样例按调用名分目录，不按架构号分。
- **枚举值存在不等于运行时映射生效**。`Ascend910_93` 的 SocVersion 字符串在运行时映射到 `ASCEND910B`，架构号同为 2201；源码中可能出现 `SocVersion::ASCEND910_93` 这类枚举值，但运行时字符串映射应以本地 `convertMap` 为准。
- **本表不覆盖构建脚本里的 SOC 别名，也不覆盖头文件中的 `SocVersion` 枚举成员清单**。这两者是独立的命名集合；[ASCEND350 非 SocVersion 枚举成员致编译失败](../../../ops/ascendc/runbooks/compilation/ascend350_socversion.md) 记录了把构建侧别名当作枚举成员使用所导致的编译失败及其判别方法，本卡不重复该结论。
- 来源也用 `DAV_<四位数值>` 的形式指称同一个架构号（出现 `DAV_2201`、`DAV_3002`、`DAV_3510`）。这只是写法不同，不构成第五个标识层次；编译命令行里该名字的拼写要求见[该 Runbook](../../../ops/ascendc/runbooks/compilation/bisheng_npu_arch_requires_lowercase_dav_2201.md)。

## 为什么产品名不能直接推断接口支持面

这是本卡最需要被复用的一条结论，来源给了四个互相独立的理由：

1. **名称粒度粗于能力粒度**。既然 2201 同时是 A2 和 A3，仅凭"架构号相同"就无法说明两个产品的接口支持面一致。
2. **产品支持范围是按"产品系列"行声明的，且只覆盖部分系列**。来源的 dtype 产品支持表只有两行：Ascend 950PR&950DT 系列、Atlas A2/A3 训练和推理系列。910、310P、310B 不在该表的任何行里——**不在表内既不等于支持也不等于不支持**，来源对此的明确要求是：未列出的芯片或产品系列不要按名称自行扩大 dtype 支持，必须回查目标 API 文档、声明、impl 和已有 UT。
3. **同一份来源内部会互相冲突**。来源自身记录：dtype 产品支持表把 `complex32`/`complex64` 列在 950PR&950DT 系列，而复数章节又声明这两个类型当前仅昇腾 910_95 AI 处理器支持。来源给出的处置不是二选一，而是"如果与产品支持表或本地代码存在差异，生成 UT 前必须以目标 API 和本地实现为准"。
4. **能力存在不等于 API 支持**。来源在 Ascend950 能力章节明确写：能力存在不等于所有 API 自动支持，必须以设计文档和本地代码为准。

因此架构号一致只是必要条件之一。来源的 API 兼容性检查清单要求同时确认"目标芯片、SocVersion 和 `__NPU_ARCH__` 映射一致"**和**"文档声明的芯片范围与代码分支一致"；只做前一半就会把产品名当成支持面结论。

## 适用与不适用

**适用**：

- 拿到设备名或产品名，要确定统一的调用名、SocVersion 字符串或 `__NPU_ARCH__` 数值时取值。
- 判断两个型号是否真的同架构（例如 910B 与 910_93 同为 2201），进而判断某段代码是否需要按架构条件编译区分，还是只需要按型号区分。
- 迁移或移植前，按来源的 API 兼容性检查清单逐项核对映射一致性，并列出未验证的芯片范围。
- 需要在报告中说明"哪些芯片范围已覆盖、哪些未验证"时，用本表作为范围词表。

**不适用**：

- 具体 API 的参数、语义与 dtype 支持矩阵——回目标 API 文档与对应平台卡，例如 [NPU 内存层次与数据通路模型](npu_memory_model.md)（存储层次与容量、数据通路映射，与本卡的取值映射是不同维度）与 [Ascend950 微架构](ascend950_microarchitecture.md)（950 系列的芯片组成与执行单元，不涉及跨代命名映射）。
- 设备身份（Device ID / Chip ID / 逻辑设备号）与构建链的现场核对——那是[设备身份、芯片型号与编译架构的区别](../../../ops/ascendc/guides/environments/device_identity_and_architecture_selection.md)的分工，本卡只提供它需要用到的取值表。
- 单平台现场确认某个产品名对应的 soc_version 字符串——属于[该实测 Runbook](../../../ops/ascendc/runbooks/compilation/ascend950pr_soc_version_ascend950.md)的分工；本卡说明"为什么设备名与构建名会不一致"（命名层次不同），该卡说明"在一台具体机器上怎么确认"。
- 运行期查询接口的签名与返回值，见 [GetSocVersion](../../../ops/ascendc/apis/utils_api/platform_info/platform_ascend_c/get_soc_version.md) 与 [GetCurNpuArch](../../../ops/ascendc/apis/utils_api/platform_info/platform_ascend_c/get_cur_npu_arch.md)。
- 各架构号内部的能力细节，见按架构拆分的 spec 卡（如 [NPU架构版本2201](../../../ops/ascendc/guides/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md)）；本卡不展开任一架构的能力清单。
- 确认"要迁移"之后的具体 API 兼容性适配方案，见按架构对拆分的迁移指导（如 [基础API迁移指导](../../../ops/ascendc/guides/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/basic_api_migration.md)，2201→3510）；本卡只负责判断"是不是真的换了架构号"这一步。

本卡的平台范围（`a2`/`a3`/`950`/`310p`/`910`）即主映射表覆盖的取值集合，不含 `agnostic`：映射结论与硬件强相关，换芯片即失效。

## 映射变更时如何发现

1. **优先消费机器入口，不要抄人读表格**。来源规定脚本读取同目录的结构化事实文件消费映射，Markdown 表格只供人工说明、不作为脚本解析入口。抄表会随文档更新而静默过期，读结构化文件不会。
2. **单一维护点决定"发现的顺位"**。来源要求：出现新芯片调用名时，先补映射、再同步更新相关脚本或测试；其他 skill 不再并行维护完整的芯片类型表。所以发现路径是——先在统一维护点找登记，找不到就是**缺口**，按未知项记录并补来源，不要自行扩展映射。
3. **文档与代码冲突时先报告，不扩大范围**。来源的要求是：文档要求的架构分支若与本地代码模式冲突，先记录差异并向用户报告；目标芯片与文档、代码或 UT 约束不一致时，先输出冲突点，不要直接扩大支持范围；未验证的芯片范围要在最终报告里明确列出。
4. **警惕来源指针本身漂移（在所引固定提交核对）**。来源正文的链接显示文字与结构化事实的 `dtype_source` 都写作 `docs/zh/api/context/内置数据类型.md`；所引 `e680c34c...` 提交的树里没有该路径，而链接目标 `docs/zh/api/SIMD-API/basic_api/data_structures/builtin_data_types.md` 存在。本次只核对了树中路径，不读取或复核目标 dtype 文件的内容；使用 dtype 结论前还须另行核验。
5. **条件编译分支要回查数值来源，而不是只看本表**。本表只覆盖登记集合，本仓另有卡以 3003 / 3113 等数值作为 `__NPU_ARCH__` 取值讨论 V220 的守卫条件（见 [OL-142](../../../ops/ascendc/runbooks/compilation/ol_142_npu_arch_numeric_macros_a5_3510_v220_bf16_guards_3.md)）；判断"这个数值是谁"时不能只查本表。

## 失效边界

- **只对登记集合有效**。未在统一维护点登记的芯片调用名或架构号，本卡不给出映射，也不要按名称字面外推（来源明确禁止按名称自行扩大范围）。
- **`ASCEND310B` / 3002 未在本卡声明平台范围**。来源登记了 Ascend310B1~B4、Atlas 200I/500 A2 与架构号 3002，但本仓 platform 注册表没有与该产品对应的取值，故 `platforms` 不声明它。表中该行仅用于映射表的完整性，不代表本卡对该平台作出了可用性结论。
- **dtype 支持面在本卡无来源支持**。来源的 dtype 产品支持表只有 950PR&950DT 与 Atlas A2/A3 两行，910、310P、310B 的 dtype 支持范围不在本卡证据内；具体 dtype 一律回目标 API 文档与本地实现。
- **别名 A2/A3/A5 只是人读叫法**。别名表仅存在于来源的人读章节，结构化事实中没有别名字段，不要把它当成机器可消费的判据。
- **不做能力断言**。本卡是取值映射与边界声明，不含任何芯片的实测行为、性能或精度结论；"能力存在不等于 API 支持"这条约束在本卡对全部平台一致生效。
- 目标芯片信息缺失时按未知项记录在报告中，不要默认选择某个架构或某个平台取值。
