---
type: Concept
title: AscendC 目标架构与构建环境的选择依据
description: 以产品型号核对已公布的架构版本，再为 bisheng 指定 --npu-arch；区分 asc-ar-dev 的 DEVKIT_PATH/CANN_PATH/SOC_ARCH/TASK_GOAL 输入约定与工程侧 SoC 注册。结合固定源码界定构建元信息能证明的行为及各阶段故障，与具体修复个案分工。
tags:
- task.design
- task.migration
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/asc-ar-dev/references/02_local_environment.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/asc-ar-dev/references/05_build_meta.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/language_extension/simd_builtin_keywords.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/getting_started/quick_start/simd_programming/hello_world.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/getting_started/environment_setup.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/getting_started/ascend_c_overview_and_learning_path.md
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/docs/zh/guide/programming_guide/compilation_and_execution/operator_compilation/bisheng_compiler.md
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/tools/build/asc_op_compile_base/asc_op_compiler/kernel_info_infer.py
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/tools/build/asc_op_compile_base/asc_op_compiler/compile_op.py
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/tools/build/asc_op_compile_base/asc_op_compiler/ascendc_compile_base.py
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/tools/build/asc_op_compile_base/asc_op_compiler/ascendc_compile_dfx.py
  role: supporting
created_at: '2026-10-23T02:30:00Z'
updated_at: '2026-10-27T20:24:00Z'
platforms:
- '950'
- a2
- a3
- '310p'
- '910'
- kirin_x90
- kirin_9030
---

# AscendC 目标架构与构建环境的选择依据

## 定义

- **目标架构**：编译时用 `--npu-arch=dav-<架构版本号>` 指定目标 NPU 架构；Device 代码中的 `__NPU_ARCH__` 宏标识架构版本。所引资料没有给出运行期自动选择目标架构的机制。
- **构建环境**：完成目标工程编译所需的路径、工具和构建配置。所引 asc-ar-dev Skill 将 `DEVKIT_PATH`（仓路径）、`CANN_PATH`（CANN 包安装路径）、`SOC_ARCH`（目标 SoC 架构，例如 `dav-2201`）、`TASK_GOAL`（任务目标）列为该流程的输入；它们不是 bisheng 或所有 Ascend C 工程的统一必填参数。可直接用 bisheng 编译简单 `.asc` 用例；使用 CMake 编译 Ascend C 算子时，所引环境准备文档要求 CMake 3.16 及以上。
- **三种名称不要混用**：产品系列（如 Ascend 950PR/950DT）、架构版本（`dav-*` 的数字）与工程侧 SoC 注册串（如特定工程中的 `ascend950`）。官方宏映射表列出 950PR/950DT → 3510、Atlas A3/A2 → 2201、Atlas 200I/500 A2 → 3002、Atlas 推理系列 → 2002、Atlas 训练系列 → 1001；未给出 Kirin X90/9030 的架构号。`SOC_ARCH` 是所引 Skill 的输入名，不能直接当作 CMake 的 `ASCEND_COMPUTE_UNIT`、OpDef `AddConfig` 或平台配置中的 `SocVersion` 的取值约定；这些应按具体工程分别核对（个案见相邻卡）。
- 所引 asc-ar-dev 流程的输入解析约束（并非通用编译器要求）：**不要用硬编码路径替换任何一个输入值**；解析不出来就问，不要猜。

## 机制一：目标架构怎么定（三步，按序）

1. **定 `DEVKIT_PATH`**：所引 Skill 在 asc-devkit 仓内使用时，从当前工作区或技能目录逐级向上找仓根；候选根通常包含 `CMakeLists.txt`、`include/`、`impl/`、`tools/`、`.agent/`。目标是其他仓库时按任务相关文件校验用户提供的路径；找不到有效根就向用户要，不要猜。这不是所有 Ascend C 工程的通用目录要求。
2. **定 `CANN_PATH`**：先看 `ASCEND_HOME_PATH`，再看 `ASCEND_TOOLKIT_HOME`（若它指向 `toolkit` 子目录且父目录下有 CANN 的 `tools/` 树，要归一到父目录），然后用探针校验，例如 `${CANN_PATH}/tools/bisheng_compiler/bin/bisheng`、`${CANN_PATH}/tools/show_kernel_debug_data`；环境变量缺失或校验失败时向用户索取安装路径。
3. **定 `SOC_ARCH`（此 Skill 的目标架构输入）**：对映射表已列出的产品型号查对应版本号，构造 `dav-<版本号>`；表中未列架构号的产品（如 Kirin X90/9030）不能由该表推定。针对简单 `.asc` 用例，先解析 CANN 路径，再按入门文档的完整命令形态 `bisheng hello_world.asc --npu-arch=dav-2201 -o demo` 编译；这里的 `dav-2201` 仅适合相应目标，其他目标须替换。此例是可执行文件编译示例，不意味着每个 `.asc` 都能脱离其工程独立链接运行。

**照抄示例的陷阱**：入门 Hello World 文档里的编译命令写的是 `bisheng hello_world.asc --npu-arch=dav-2201 -o demo`，而同一页说明该样例支持 950PR/950DT、A3、A2，并要求将 `dav-` 后的版本号替换为实际版本。映射表中 950PR/950DT 为 3510、A3/A2 为 2201；直接照抄会将编译目标指定为 2201，不能据此认定 950 产物已按 3510 编译。

**输入缺件时怎么办**：来源给了固定的缺失输入索取格式，只问仍然缺的值（`DEVKIT_PATH`、`CANN_PATH`、`SOC_ARCH`、`TASK_GOAL`）；能从当前工作区/技能目录解析出的 `DEVKIT_PATH`、已写进 `TASK_GOAL` 或可从环境变量解析的项就不再问用户。

**代码里的架构分支**：Device 侧 AI Core 代码用 `__NPU_ARCH__` 预处理宏标识架构版本，可按它写差异化分支（如 `#if __NPU_ARCH__ == 2201`）。`--npu-arch=dav-2201` 是编译选项，宏示例用数值 `2201` 比较；具体工程的宏值应从实际编译配置/预处理结果核对，不能将两个字符串直接等同。

## 机制二：构建环境里决定产物的还有三件事

- **文件形态与仓内分区**：bisheng 文档允许 `.asc` 包含 Device-only、Host-only 或混合代码，不能假定每个文件都同时含 Host 与 Device。asc-devkit 中 `include/`、`impl/`、`tools/`、`scripts/`、`cmake/` 分别是 API 声明、实现、编译工程工具、辅助脚本和工具链集成的定位入口；这些目录不是其他工程的通用结构要求。
- **选构建入口**：做仓内回归前，先看当前的 `build.sh`、`tests/test_parts.sh` 以及相关 `tests/**/CMakeLists.txt` 再决定测试目标；简单用例才走"直接 bisheng 编译"的快捷路径。
- **构建元信息**：所引 `05_build_meta.md` 概述仓库编译器脚本的调测编译标记及元信息处理入口；它本身不是各脚本行为或运行时生效的实测记录：

| 脚本（位于仓内 `tools/build/asc_op_compile_base/asc_op_compiler/`） | 与产物的关系 |
|---|---|
| `kernel_info_infer.py` | 固定源码从预处理文件识别确定性标记、kernel 类型和 tiling 信息等；参考文档另称它推断 `printf`/`assert` 编译标记，但本次所核对的该脚本不直接证实这一具体归属 |
| `compile_op.py` | 固定源码构造 `.ascend.meta` 中的版本、调试、动态/可选参数节，保存 `ascendc_meta_info` 并追加到生成源码；调试位表包含 `printf`/`dumptensor`/`assert` 等，具体置位条件须分别检查 |
| `ascendc_compile_base.py` | 固定源码的 `link_relocatable_meta_file` 用链接器将元信息文件并入目标文件；仅在相应构建分支调用，非每次独立 bisheng 编译都必经此路径 |
| `ascendc_compile_dfx.py` | 固定源码定义 TLV 类型 `F_TYPE_KTYPE=1`、`F_TYPE_L0_EXCEPTION_DFX=4`、`F_TYPE_L0_EXCEPTION_DFX_ARGSINFO=5`、`F_TYPE_L0_EXCEPTION_DFX_IS_TIK=6`，按编译分支生成对应元信息 |

- 由此可得的结论：源码能证明特定生成和链接分支存在，不能证明所有构建路径均写入这些节，也不能单凭调试位表或参考文档证明 `printf`/`assert` 运行时生效。**不要凭记忆自造 `.ascend.meta` 布局**；改动时先按具体编译分支核对源码与产物。常规 Ascend C kernel 开发无须展开这份元信息参考。

## 机制三：选错会在哪一步暴露

| 阶段 | 暴露形态 | 判读方向 |
|---|---|---|
| 环境解析 | 探针失败/路径不存在（如 bisheng 探测不到） | 这是 `CANN_PATH`/`DEVKIT_PATH` 没定对，先按机制一重解析并校验，不要先改代码 |
| CMake 配置 / opbuild | `The soc version of op ... is not configured` 之类的配置期失败 | 相邻个案中变体名不被识别；改为 `ascend950` 后与工程的 `ASCEND_COMPUTE_UNIT` 一致且构建成功，但个案未能区分“不被识别”和“必须相等”两种内部原因 |
| Device 编译 / 工程源码扫描 | 架构不支持的代码形态编译失败（[PipeBarrier 个案](../../../ops/ascendc/runbooks/compilation/pipebarrier_pipe_s_is_not_supported.md)）；另有工程把 dav-3510 专属源码当作跨架构文件编译而在 dav-2201 构建中找不到符号（[CMake arch 子目录个案](../../../ops/ascendc/runbooks/compilation/cmake_arch_dav_3510_api.md)） | 分别核对编译目标与 API 支持、工程的源码收集规则；后一个案不能直接归因为 `--npu-arch` 写错 |
| 链接 / 元信息产物 | 若链接失败或元信息与预期不符 | 核对实际链接命令、构建分支和产物；本卡引用的参考没有给出通用错误码或运行时验证结论 |

判读原则：**先用“在哪一阶段失败”区分路径解析、工程 SoC 注册、源码收集/编译与链接问题**，再按该工程的实际构建命令和日志确认原因；阶段本身不是唯一根因的证明。

## 动手前先看仓内哪里

来源给出了仓内可复用区域与检索入口，按要做的事定位，避免自己另起一套：

| 要做的事 | 仓内位置 |
|---|---|
| 查基础 API / 高阶 API 声明 | `include/` |
| 查基础 API / 高阶 API 实现 | `impl/` |
| 用编译工程工具 | `tools/` |
| 改构建或辅助脚本 | `scripts/` |
| 改 CMake 与工具链集成 | `cmake/` |
| 找启动与入门样例 | `examples/01_simd_cpp_api/00_introduction` |
| 找调测工具样例 | `examples/01_simd_cpp_api/01_utilities` |
| 找兼容性与内存通路样例 | `examples/01_simd_cpp_api/05_compatibility_guide` |
| 追编译与元信息流水线 | `tools/build/asc_op_compile_base/asc_op_compiler` |

## 适用与不适用

- **适用**：新算子/新工程开工前固定目标架构与构建环境；跨代迁移前确认目标；写 CI 或脚本时决定编译目标；排查"这份产物到底是给哪个架构编的"。
- **不适用**：运行期的设备与流选择（device id、stream）、算子包安装与部署、以及某个具体报错的修复步骤——后者走各自的 Runbook。
- **适用粒度**：工程/构建级；不针对单个 API 的语义。

## 与其他概念的边界

- **目标架构 vs 产品型号 vs 工程 SoC 名称**：见“定义”；例如 `dav-3510` 不等于某工程的 `ascend950` 注册串，不能将二者互换。
- **`DEVKIT_PATH` vs `CANN_PATH`**：前者是 asc-devkit 仓库（`include/`、`impl/`、`tools/`、`cmake/` 等源码与工具），后者是 CANN 安装包（提供 bisheng 编译器、运行时与工具）；所引 asc-ar-dev 仓内开发流程要求解析并校验两者；仅使用已安装 CANN 编译独立用例时，不能据此要求额外检出 asc-devkit。
- **架构版本 vs `__NPU_ARCH__` 宏**：前者作为 `dav-<数字>` 输入，后者以数值标识架构版本，用于 Device 代码分支。
- **构建元信息 vs 产物**：元信息是对产物的标记/描述（含调测特性开关的编译标记），改元信息不等于改计算逻辑。
- **构建环境 vs 运行环境**：`source ${INSTALL_DIR}/set_env.sh` 属于把环境变量准备好；来源还提到 Ascend C 开发并非必须装驱动固件，非昇腾设备上可以先用 CPU 仿真环境开发测试，再上昇腾设备加速。

## 与相邻卡的分工

- 本卡给**选择依据与判定顺序**（选哪个架构、环境怎么定、错了在哪一步暴露）；具体个案的修复步骤归各自的 Runbook：[CMake arch 子目录隔离 dav-3510 专属 API](../../../ops/ascendc/runbooks/compilation/cmake_arch_dav_3510_api.md)（构建系统按 arch 隔离代码导致找不到专属符号）与 [AddConfig 产品变体名致 SoC 未配置构建失败](../../../ops/ascendc/runbooks/compilation/addconfig_product_variant_name_invalid.md)（型号注册串写错在 CMake 配置期暴露）。
- 架构号写法与宏的核对链路：[bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav](../../../ops/ascendc/runbooks/compilation/bisheng_npu_arch_requires_lowercase_dav_2201.md)（`--npu-arch` 的取值形式）、[Ascend arch 变体查证链路 SoC→ini→NpuArch→dispatcher](../../../ops/ascendc/runbooks/compilation/arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md)（从型号追到编译期命中的变体文件）。
- 目标架构决定"哪些代码形态能编过"的实例：[PipeBarrier：只保留目标架构支持的管线](../../../ops/ascendc/runbooks/compilation/pipebarrier_pipe_s_is_not_supported.md)。

## 失效边界

- 平台面取自官方概述页的 Ascend C 支持列表；`__NPU_ARCH__` 映射表只覆盖其明确列出的产品，不给出 Kirin X90/9030 的版本号。两份 asc-ar-dev 参考按仓与工具链组织，没有按型号分档；具体型号的架构号不能从“支持 Ascend C”直接推出。
- `05_build_meta.md` 是 Skill 参考而非编译器规范；本卡另核对了所列四个固定提交脚本的相关段落。未核对所有调用分支或 `.ascend.meta` 完整布局，也没有实际编译、产物对比和运行时调测实测。
- 本卡未执行环境解析、编译或元信息比对；`DEVKIT_PATH`/`CANN_PATH`/`SOC_ARCH` 的具体取值随环境变化，不是常量。
- 与版本相关：来源提到的探针路径、脚本名与常量可能随 CANN/asc-devkit 版本变化，跨版本使用前按当前仓与当前安装重新核对。
