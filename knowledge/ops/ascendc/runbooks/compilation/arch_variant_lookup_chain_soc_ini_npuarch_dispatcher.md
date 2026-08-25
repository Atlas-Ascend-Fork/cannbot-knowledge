---
type: "Runbook"
title: "Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa"
description: "从芯片型号经 platform_config ini 的 NpuArch/AIC_version 到 dispatcher 头文件的 __NPU_ARCH__ 分支，确定编译期命中的 dav_c* 变体文件，避免误读宏隔离的 C 头文件。"
tags: ["task.lookup", "topic.architecture", "topic.compilation", "topic.implementation.debugging"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa

## 现象

在 Ascend950PR 上调试 `softplus_v2_grad` 的 `Select` API 行为时，agent 用 `grep VSEL_CMPMASK_SPR` 命中 `dav_c100/kernel_operator_vec_cmpsel_impl.h`，误读后断言"arch35 仅支持 VSEL_CMPMASK_SPR"。但 ascend950PR 实际对应 `__NPU_ARCH__==3510` → dispatcher 选中 `dav_c310`（不是 dav_c100），`dav_c310` 支持 `VSEL_TENSOR_TENSOR_MODE`。误读变体文件导致根因判断绕路（手动分段修复而非最小改 MODE）。

宏隔离的 C 头文件（`$ASCEND_HOME_PATH/x86_64-linux/asc/impl/basic_api/dav_c*/`）按 `__NPU_ARCH__` 宏分变体，grep 命中的变体文件可能不是目标 arch 实际编译的变体。须先确认编译期命中的变体，再读其 API 实现。

## 适用场景

- **工程形态**：ops-registry-invoke / ops-direct-invoke（任何需查 arch 特定 AscendC API 实现的场景）。
- **API 路径**：`$ASCEND_HOME_PATH/x86_64-linux/asc/impl/basic_api/kernel_operator_vec_cmpsel_intf_impl.h`（dispatcher 入口）；`dav_c*/` 变体子目录；`$ASCEND_HOME_PATH/x86_64-linux/data/platform_config/*.ini`（SoC 平台配置）。
- **验证过的平台与 CANN 版本**：Ascend950PR（`__NPU_ARCH__==3510` → dav_c310），CANN cann-9.0.0-beta.2。
- **适用粒度**：`platform_wide`（Ascend950PR 上查 arch 特定 API 变体的通用规程）。
- **路线优先级**：`recommended_fastpath`（先 dispatcher + ini 确认变体，再读变体文件）。
- **不适用/未验证场景**：a2/a3 等其他平台的 ini 命名规律与 dispatcher 分支未在本 trace 完整实测（链路结构推断一致，但具体 ini 文件名/NpuArch 值需各自查证）。

## 判别方法

完整链路（两条入口，归一到 `__NPU_ARCH__==<值>` → 变体目录）：

**入口 A（从运行环境/题目上下文拿到芯片型号，如 `Ascend950PR`、`npu-smi` 输出、`build.sh --soc=ascend950`）**：
1. 在 `$ASCEND_HOME_PATH/x86_64-linux/data/platform_config/` 下用通配符匹配 ini（如 `Ascend950PR*.ini`）。
2. grep 该 ini 的 `SoC_version`（精确芯片型号）、`NpuArch`（arch 数值）、`AIC_version`（变体标识，如 `AIC-C-310`）、`CCEC_AIV_version`（如 `dav-c310-vec`）。
3. 用 `NpuArch` 值在 dispatcher 头文件 `kernel_operator_vec_cmpsel_intf_impl.h` grep `#elif __NPU_ARCH__ == <值>`，得到 `#include "dav_c<xxx>/..."` 即编译期命中的变体。
4. 读该 `dav_c<xxx>/` 变体文件确认 API 真实可用性。

**入口 B（从 DESIGN.md 或上下文拿到 DAV_3510 等 arch 名）**：
1. 直接 grep dispatcher 头文件 `__NPU_ARCH__ == 3510` → 得到 `#include "dav_c310/..."`。
2. 读 dav_c310 变体文件。

**关键判别信号**：
- 文件名通配符不可靠（实测）：`Ascend950PR_950z.ini`（有下划线）vs `Ascend910B1.ini`（无下划线）——固定 `Ascend<型号>_*.ini` 形式在 910B 断路。
- 模糊匹配有歧义（实测）：`grep "Ascend910B"` 同时命中 `Ascend910B.ini`（`NpuArch=1001`）和 `Ascend910B1/B2/B3/B4.ini`（`NpuArch=2201`）——误取会导致读错变体。
- 大小写不匹配（实测）：`build.sh --soc=ascend950`（小写无 PR 后缀）vs ini 的 `SoC_version=Ascend950PR_950z`（大写带后缀）——不能直接相等匹配。
- `AIC_version` 与 `NpuArch` 互为印证：`NpuArch=3510` → dispatcher 的 `__NPU_ARCH__==3510` 分支；`AIC_version=AIC-C-310` → `dav_c310/` 目录名。任一即可定位变体，且都来自 ini 硬证据。

## 完整实现

（完整实现单元；逐字代码见下 `## 完整代码`。）

## 完整代码

完整诊断命令（逐字取自 trace 的 bash tool_call 事件，verbatim）：

```bash
# 步骤1: 用芯片型号通配符匹配 ini
cd $ASCEND_HOME_PATH && find . -iname "Ascend950*.ini" 2>/dev/null | head

# 步骤2: grep ini 的 SoC_version / NpuArch / AIC_version（确认 arch 数值与变体标识）
cd $ASCEND_HOME_PATH/x86_64-linux/data/platform_config && \
  echo "=== 950PR ini ===" && head -15 Ascend950PR_950z.ini && \
  echo "=== NpuArch/AIC_version across 950PR variants ===" && \
  grep "Short_SoC_version\|^SoC_version\|NpuArch\|AIC_version=" Ascend950PR_*.ini | head -30

# 步骤3: 用 NpuArch 值在 dispatcher 头文件确认编译期命中的变体
cd $ASCEND_HOME_PATH && \
  grep -n "NPU_ARCH.*3510\|3510" \
  x86_64-linux/asc/impl/basic_api/kernel_operator_vec_cmpsel_intf_impl.h | head

# 步骤4: 读 dav_c310 变体文件确认 API 可用性（如 VSEL_TENSOR_TENSOR_MODE 支持）
cd $ASCEND_HOME_PATH && \
  grep -n "VSEL_TENSOR_TENSOR_MODE" \
  x86_64-linux/asc/impl/basic_api/dav_c310/kernel_operator_vec_sel_impl.h | head -5

# 全场景覆盖核验（可选）：确认所有 ini 都有 SoC_version 字段
cd $ASCEND_HOME_PATH/x86_64-linux/data/platform_config && \
  echo "=== total ini ===" && ls *.ini | wc -l && \
  echo "=== SoC_version field coverage ===" && grep -l "^SoC_version=" *.ini | wc -l && \
  echo "=== missing SoC_version ===" && \
  for f in *.ini; do grep -q "^SoC_version=" "$f" || echo "MISSING: $f"; done | head
```

## 系统信息

- **toolchain/版本**：CANN cann-9.0.0-beta.2；`$ASCEND_HOME_PATH=/home/developer/Ascend/cann-9.0.0-beta.2`。
- **目标平台**：Ascend950PR（`__NPU_ARCH__==3510` → `dav_c310`）。
- **目录布局**：
  - `x86_64-linux/data/platform_config/*.ini` — SoC 平台配置（`SoC_version`/`NpuArch`/`AIC_version` 字段）。
  - `x86_64-linux/asc/impl/basic_api/kernel_operator_vec_cmpsel_intf_impl.h` — dispatcher 入口（`#elif __NPU_ARCH__ == <值> → #include "dav_c<xxx>/..."`）。
  - `x86_64-linux/asc/impl/basic_api/dav_c310/` — ascend950PR 命中的变体子目录。
  - `x86_64-linux/asc/impl/basic_api/dav_c100/` — 另一变体（非 3510，误读对象）。
- **相关文件清单**（与 trace 实际读写一一对应）：
  - `x86_64-linux/data/platform_config/Ascend950PR_950z.ini`
  - `x86_64-linux/asc/impl/basic_api/kernel_operator_vec_cmpsel_intf_impl.h`
  - `x86_64-linux/asc/impl/basic_api/dav_c310/kernel_operator_vec_sel_impl.h`
  - `x86_64-linux/asc/impl/basic_api/dav_c100/kernel_operator_vec_cmpsel_impl.h`（误读对象）

## 设计决策

- 选"ini → NpuArch → dispatcher"三环链路而非文件名联想：宏隔离的 C 头，"哪个变体被编进去"只能由 `__NPU_ARCH__` 宏（编译期）决定，不能靠文件名猜。`NpuArch` 字段是 dispatcher 的 `__NPU_ARCH__` 数值来源，`AIC_version` 是变体目录名来源，二者都来自 ini 硬证据。
- 放弃的设计：直接 `grep` API 名（如 `VSEL_CMPMASK_SPR`）在 `basic_api/` 下全局搜——命中的变体文件可能不是目标 arch 实际编译的变体（本 trace 的误诊路径）。
- 更彻底的验证（本 trace 未做但建议）：编译期 dump 预处理结果（`-E` 或 build log）确认 `__NPU_ARCH__==3510`，或写一行 `#pragma message` 打印宏值上板跑一次——宏隔离下，"哪个变体被编进去"只能由预处理决定。

## 完整实现

见上方"完整诊断命令"。该命令在 trace 中实测验证通过：`Ascend950PR → Ascend950PR_950z.ini → NpuArch=3510/AIC_version=AIC-C-310 → dispatcher #elif __NPU_ARCH__==3510 → dav_c310/`。

## 验证信号

链路实测验证（来源平台：Ascend950PR；证据等级: tool_observed）：
- `Ascend950PR_950z.ini` 的 `NpuArch=3510`、`AIC_version=AIC-C-310`、`CCEC_AIV_version=dav-c310-vec`（来源平台：950；证据等级: tool_observed）。
- dispatcher `kernel_operator_vec_cmpsel_intf_impl.h` 中 `#elif __NPU_ARCH__ == 3510 → #include "dav_c310/..."`（来源平台：950；证据等级: tool_observed）。
- `dav_c310/kernel_operator_vec_sel_impl.h:145` 支持 `VSEL_TENSOR_TENSOR_MODE`，`:187` 每 repeat `sel + i*selOffset` 偏移（来源平台：950；证据等级: tool_observed）。
## 失效边界

- 仅 Ascend950PR/dav_c310 实测；a2/a3 等其他平台的 ini 命名规律与 dispatcher 分支未完整实测（推断链路结构一致，但具体 ini 文件名/NpuArch 值需各自查证），未验证，推断可迁移。
- 文件名通配符形式跨芯片系列不统一（950PR 有下划线、910B 无），不可假定固定形式——须用通配符 `*` 匹配后逐 ini 核 `SoC_version`。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 161001 — ascend910_93 缺算子内核配置](aclnn_161001_ascend910_93.md)（`related`）：查证链可确认 Ascend910_93 对应 arch 和应命中的配置变体。
- [ASCEND350 非 SocVersion 枚举成员致编译失败](ascend350_socversion.md)（`related`）：两卡共同区分 SoC 字符串、NpuArch/3510 与编译期枚举/宏：一个处理 SocVersion 编译错误，一个给出 ini→dispatcher 查证链。
- [Ascend 950PR/Ascend 950DT新增特性导航](../../guides/asc_950_feature_guide.md)（`related`）：该指南从 SoC 配置追到 __NPU_ARCH__ 分支，能验证特性指南中 3510 能力实际命中的头文件实现。
- [NPU架构版本2002](../../guides/programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_2002.md)（`related`）：NPU架构版本2002 与《Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa》的实质衔接是：2002 architecture spec给出硬件组成，constraints给出 Generic Addressing/全局变量限制；GetCurNpuArch和 SoC 查证链用于确认当前目标确实落在2002。
- [NPU架构版本2201](../../guides/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md)（`related`）：Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa说明从芯片型号经 platform_config ini 的 NpuArch/AIC_version 到 dispatcher 头文件的 __NPU_ARCH__ 分支，确定编译期命中的 dav_c* 变体文件，避免误读宏隔离的 C 头文件。
- [NPU架构版本3002](../../guides/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_3002.md)（`related`）：NPU架构版本3002 与《Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa》的衔接是：arch3002 卡给出该架构的核结构与存储约束；基础架构说明、运行时架构查询和 SoC→ini→NpuArch 查证链用于确认实际编译/运行落到该变体。
- [SIMD BuiltIn关键字](../../guides/programming_guide/language_extension/simd_builtin_keywords.md)（`related`）：Runbook 将 __NPU_ARCH__ 从 SoC ini 的 NpuArch 一直追到 dispatcher 与 dav_c* 变体，给出 BuiltIn 宏用于源码分支之外的可执行查证链。
- [arch35 kernel 上板报 507035 实为 arch 不匹配](arch35_kernel_507035_arch.md)（`related`）：arch 不匹配 runbook要求先确认 build 目标与板卡；lookup 配方给出 SoC→ini NpuArch/AIC_version→__NPU_ARCH__ 分支的可执行核对链，能定位实际编译变体。
- [def.cpp 缺 AddConfig 致 SOC_NOT_SUPPORT](def_cpp_addconfig_soc_not_support.md)（`related`）：候选提供 SoC 名、ini、NpuArch、dispatcher 查证链；AddConfig 字符串必须匹配构建系统 token。
- [调用算子时出现无法打开config.ini的报错](../../guides/programming_guide/appendix/faq/config_ini_open_error.md)（`related`）：调用算子时出现无法打开config.ini的报错 与《Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [CMake arch 子目录隔离 dav-3510 专属 API](cmake_arch_dav_3510_api.md)（`same_topic`）：CMake arch 子目录隔离 dav-3510 专属 API 与《Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav](bisheng_npu_arch_requires_lowercase_dav_2201.md)（`same_topic`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
<!-- cannbot:related:end -->
