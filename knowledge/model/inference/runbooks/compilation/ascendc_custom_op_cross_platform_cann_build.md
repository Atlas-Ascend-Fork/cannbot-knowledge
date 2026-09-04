---
type: Runbook
title: cann-recipes-infer ops/ascendc 自定义算子的跨平台 / 跨 CANN 版本构建与加载失败
description: cann-recipes-infer 的 ops/ascendc 融合算子库默认面向 Atlas A3（README 首句"基于昇腾 Atlas A3 和 950PR/DT 的融合算子库"，build.sh 的 -c|--compute-unit 默认 ascend910_93），DeepSeek-V3.2-Exp 等模型的 docker 镜像也是 A3 面向。把这些 A3 制品搬到别的平台 / 别的 CANN 版本时，有三类失败会各自阻断——一类在算子加载期（平台不匹配，失败一），两类在编译期（CANN 8.5+ 删了 version.info 硬中断，失败二；version.info 钉内部 T-tag 使社区版子版本永不匹配，失败三）；此外在 A2/arm64 上跑还会出三条良性告警（非失败，见文末），别与失败一混淆。
tags:
- task.debugging
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/22
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/268
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/56
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/122
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/70
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/62
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/49
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/76
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:33:02Z'
platforms:
- a2
- a3
---

# cann-recipes-infer ops/ascendc 自定义算子的跨平台 / 跨 CANN 版本构建与加载失败

## 适用场景

cann-recipes-infer 的 [ops/ascendc](../../concepts/frameworks/ascendc.md) 融合算子库**默认面向 [Atlas A3](../../concepts/platforms/atlas_a3.md)**（README 首句"基于昇腾 Atlas A3 和 950PR/DT 的融合算子库"，`build.sh` 的 `-c|--compute-unit` 默认 `ascend910_93`），[DeepSeek-V3.2-Exp](../../concepts/models/deepseek_v3_2_exp.md) 等模型的 docker 镜像也是 A3 面向。把这些 A3 制品搬到别的平台 / 别的 CANN 版本时，有三类失败会各自阻断——一类在**算子加载期**（平台不匹配，失败一），两类在**编译期**（CANN 8.5+ 删了 `version.info` 硬中断，失败二；`version.info` 钉内部 T-tag 使社区版子版本永不匹配，失败三）；此外在 A2/arm64 上跑还会出三条**良性告警**（非失败，见文末），别与失败一混淆。

## 失败一：A3 算子二进制跑在 Atlas A2（910B3）→ 加载期报错

### 信号

已正确映射 device（`npu-smi info` 能识别卡）后，最小 torch_npu 代码仍在算子 init 阶段报错：

```
q = torch.randn((1,2,3,4), dtype=torch.float16, device="npu:1")
RuntimeError: normal_:...NPU function error: call aclnnInplaceNormal failed, error code is 561103
EZ9999: Inner Error!  ... Parse dynamic kernel config fail.
       Failed to ParseDynamicKernels.  AclOpKernelInit failed opType
       Cast ADD_TO_LAUNCHER_LIST_AICORE failed.
```

去掉 `device="npu"` 走 CPU 则正常——佐证是 NPU 侧算子/平台问题、非 torch 代码问题。

### 根因

910B3 属 **Atlas A2**，而镜像/CANN 包/算子二进制是 **A3** 面向。A3 制品的算子内核在 A2 芯片上无法匹配加载，报 `Parse dynamic kernel config fail` / `AclOpKernelInit failed`（维护者确认）。判据：症状落在算子 init 阶段而非 device 枚举阶段（此时 `npu-smi` 已正常）。

### 修法

换用 **A2 对应的 CANN 包 / 镜像**（维护者首选）。若要在 A2 复用本仓 ascendc 源码，则针对 A2（soc_version=`ascend910b`）重编：

```bash
bash build.sh -c ascend910b                        # A2 编译执行 ops/ascendc 算子（SwigluClipQuant、GatherSelectionKvCache 等）
bash build.sh -c "ascend910_93;ascend910b"         # -c 支持分号分隔多型号
bash build.sh -c ascend910b --disable-check-compatible   # 用不配套 CANN 包时再加，跳过配套性校验
```

- `--disable-check-compatible`（含拼写别名 `--disable-check-compatiable`）把 `CHECK_COMPATIBLE=false`，跳过 CANN 配套性校验，属绕过手段——README 建议优先用配套镜像，用不配套 CANN 包属自担风险。
- 硬件本就是 A3 / 950PR/DT 时无需指定 `-c`（默认即 `ascend910_93`）。
- correctness：编译后可用仓内自带算子测试脚本验证（如 `python3 test_npu_swiglu_clip_quant.py`）。
- rollback：回 A2 配套 CANN 镜像/包、不加 `--disable-check-compatible`、按默认配套编译。

## 失败二：CANN 8.5+ 删了 version.info → 编译期版本校验硬中断

### 信号

在 `cann-recipes-infer/ops/ascendc/` 下 `bash build.sh` 直接编译报错。CANN 8.3 能编过、CANN 8.5 编不过（仓自报）。

### 根因

最新 CANN 版本包里已不再有 `version.info` 文件，而 `ops/ascendc/cmake/scripts/check_version_compatible.py` 的 `VersionChecker` 仍依赖读它做版本校验，在"文件缺失 / 取不到版本 / 版本不匹配"5 处都 `raise ValueError` 硬中断编译（含 `cann_sub_version != code_sub_version` 时的 `Please install version {code_sub_version} of the cann package.`）。

### 修法

把 `VersionChecker` 全部 5 处 `raise ValueError(...)` 降级为 `logging.warning(...)` + `return None`（维护者确认的修法），校验失败只告警、不拦截编译：

```python
- raise ValueError(f"CANN version info file({cann_version_info_file}) not exist.")
+ logging.warning(f"CANN version info file({cann_version_info_file}) not exist.")
+ return None
```

维护者确认："版本检验改成 warning 而不拦截，请先用该修复编包"。

- **代价**：版本兼容性不再被强制拦截——`cann_sub_version != code_sub_version` 也只 warning，需使用者自行确认 code 与所用 CANN 包版本一致。
- 与失败一相通：两处都指向 ops/ascendc 构建期的 CANN 配套/版本校验；`--disable-check-compatible`（失败一）与该 warning 降级（失败二）都是放宽这层校验的手段。

## 失败三：version.info 钉内部 T-tag → 社区/通用版 CANN 子版本永不匹配 → `--disable-check-compatible`

### 信号

在 `ops/ascendc/` 下 `bash build.sh`（`CHECK_COMPATIBLE` 默认 ON）用**社区 / 通用版 CANN**（如 8.2.0.0、8.3.RC1.alpha00x、8.3.RC1、8.5.0.alpha001）编译，被版本兼容性门拦下：

```
check_version_compatible.py [ERROR] The version number of the current code is 8.3.T14.0,
  and the version number of the cann package used is 8.2.0.0.
  Please install version 8.3.T14.0 of the cann package.
CMake Error at cmake/config.cmake ... Check version compatibility failed.
```

（修复前是 `raise ValueError` → CMake `FATAL_ERROR` 硬中断；软化为 warning 后仍会持续告警。）

### 根因

`ops/ascendc/version.info` 钉的是**内部 / 开发版 CANN 版本号**（钉定 sha 处 `Version=8.5.T4.0`、issue 时 `8.3.T14.0`，`T` 系内部 tag）。校验（`VersionChecker._check_compatible`）对代码侧与 CANN 侧两个 `version.info` 各取 `rsplit('.', 1)[0]` 的子版本比较——社区 / 通用版 CANN 发行号（`8.2.0.0 → 8.2.0`）与内部 T-tag 子版本（`8.5.T4.0 → 8.5.T4`）永远不等，故**任何用非配套 CANN 的用户都会命中**。这是仓内 pin 内部版本号的固有行为、非某次提交，与失败二（文件缺失）区分：失败三是文件**在**、但钉的号社区版永远对不上。

### 修法

编译加 `bash build.sh --disable-check-compatible`（含拼写别名 `--disable-check-compatiable` → `CHECK_COMPATIBLE="false"` → `-DCHECK_COMPATIBLE=false`），整段 `check_code_compatible` 被 `if (CHECK_COMPATIBLE)` 短路跳过，即可用社区 / 非配套 CANN 编出 `CANN-custom_ops-<ver>-linux.<arch>.run`。README FAQ「非标准镜像 CANN 包如何编译执行 ascendc 算子」已收录此开关；维护者首选建议仍是用配套镜像。`--disable-check-compatible` 对三条路径（缺 `version.info` / 走 FATAL 老路径 / 子版本永不匹配）都是最稳的**显式**绕过口——绕过后配套性不再保证，运行时兼容性自担。原诉求「把 `version.info` 改用社区通用版本号」未被采纳。

## 非失败：910b/arm64 上的三条良性告警（勿排查）

在 910b（arm64）上跑 `ops/ascendc/examples/` 自定义算子测试（eager 与 graph 两种模式）稳定出现三条告警，易被误当问题：

1. `Warning: Version: 8.5.0.alpha001 is invalid.` —— CANN 环境版本字符串格式解析告警。
2. `[WARNING] [ascend910b] Not found tiling so file, use default api soc verison` —— AscendC 算子在目标 soc 缺对应 tiling so、回退 default api soc version（库为 A3/950 构建，910b 上对应 soc 的 tiling so 缺失）。
3. `Warning: record_context_cpp is not support on non-linux non-x86_64 platforms` —— torch profiler `record_context` 在 arm64 禁用。

**三条均为良性**：不来自本仓源码，由 CANN 工具链 / torch_npu 运行时 / AscendC tiling 基础设施发出，不影响算子正确性与性能（维护者确认「自验证过程同样出现、不影响性能」；测试 npu-vs-cpu 精度 100% / ~99.96%–99.99% 佐证）。识别即继续，**不必为它们排查算子是否损坏**。注意告警 2 正是「A3/950 构建的库在 A2/910b 上跑」的跨 soc **回退**信号——与失败一（A3 算子在 A2 **加载期硬报错**）区分：告警只是回退、不是加载失败。

## 适用边界

限于 cann-recipes-infer 的 ops/ascendc 算子构建（`build.sh` / `check_version_compatible.py` 路径）；不外推为"所有 cann-recipes-infer 用法都不能在 A2 跑"或整个昇腾栈通用律。平台面向也随镜像/CANN 版本漂移，以目标 recipe 当时 pin 的版本为准。

## 相关经验
- [昇腾 bringup 初始化/HCCL 报错的根因常在环境/驱动/平台层，顶层 ACL/HC](../runtime/bringup_error_root_cause_env_driver_platform.md)

## Evidence

失败一（A3 算子跑 Atlas A2 → 加载期报错）：

- **代码事实**（clone `@2c45117`）：`models/deepseek-v3.2-exp/README.md` 产品型号为 Atlas A3 系列；`ops/ascendc/README.md` FAQ 载明"ascendc 算子默认基于 A3 环境编译""A2 环境用 `bash build.sh -c ascend910b`"；`build.sh` 的 `-c|--compute-unit` 默认 `ascend910_93`，`--disable-check-compatible` 置 `CHECK_COMPATIBLE=false`。报错文本为用户复现原文。
- **维护者确认**："910B3 是 Atlas A2，需使用 A2 的 CANN 包或镜像"。同一失败在另一事件从**编译目标**侧印证：`ops/ascendc/build.sh` 默认 `-c ascend910_93`（A3），A2 上直接跑默认构建的 `torch.ops.custom.npu_lightning_indexer` / `npu_sparse_flash_attention` 运行报错，维护者确认「A2 使用需编译时指定 `-c ascend910b`」（clone `@2c45117`：`CMakeLists.txt` 的 `ASCEND_COMPUTE_UNIT` 默认 `ascend910_93` + README FAQ「A2 环境如何编译执行 ascendc 算子」）。
- 溯源下探：[cann-recipes-infer-issue-22-bug-report-readme-torchnpu](https://gitcode.com/cann/cann-recipes-infer/issues/22)、[cann-recipes-infer-issue-56-bug-report-torch-ops-custom-npu-lightning-indexer-torch-ops-custom-npu-s](https://gitcode.com/cann/cann-recipes-infer/issues/56)

失败二（CANN 8.5+ 缺 version.info → 编译期硬中断）：

- **代码事实**（clone `@44f99af789d0`）：单文件 `check_version_compatible.py` 改动（+12 −7），5 处 `raise ValueError` 逐处降级为 `logging.warning` + `return None`。
- **维护者确认**：版本校验改成 warning 而不拦截，请先用该修复编包（报障侧 issue：CANN 8.3 能编过、8.5 编不过，`version.info` 已不存在）。
- 溯源下探：[cann-recipes-infer-pr-268-fix-version-check](https://gitcode.com/cann/cann-recipes-infer/merge_requests/268)、[cann-recipes-infer-issue-122-bug-report-cann-recipes-infer-ops-ascendc](https://gitcode.com/cann/cann-recipes-infer/issues/122)

失败三（version.info 钉内部 T-tag → 社区版子版本永不匹配）：

- **代码事实**（clone `@2c45117`）：`build.sh` 的 `--disable-check-compatible` → `CHECK_COMPATIBLE=false`；`cmake/config.cmake` 的 `option(CHECK_COMPATIBLE ON)` + `if (CHECK_COMPATIBLE)` 门 + `message(FATAL_ERROR "Check version compatibility failed.")`；`check_version_compatible.py::_check_compatible` 取 `rsplit('.',1)[0]` 子版本比对；`ops/ascendc/version.info` = `Version=8.5.T4.0`（内部 T-tag）；README FAQ 收录 `--disable-check-compatible`。**维护者确认**：讨论区多名维护者以 `--disable-check-compatible` 为解法 + 建议镜像版本。报错行号/版本串按符号锚定、不复用旧行号。
- 溯源下探：[cann-recipes-infer-issue-70-requirement-ops-cann](https://gitcode.com/cann/cann-recipes-infer/issues/70)、[cann-recipes-infer-issue-62-bug-report-x86-npu-cann8-3rc1](https://gitcode.com/cann/cann-recipes-infer/issues/62)、[cann-recipes-infer-issue-49-question-ops-ascendc-cann8-2](https://gitcode.com/cann/cann-recipes-infer/issues/49)

非失败（910b/arm64 三条良性告警）：

- **grep 事实**（clone `@2c45117`）：三条告警字符串（`Not found tiling so file` / `record_context_cpp` / 版本 `is invalid`）全库 grep 均不在本仓源码，确认由 CANN 工具链 / torch_npu / AscendC tiling 基础设施发出；`ops/ascendc/README.md` 库定位「Atlas A3 / 950PR/DT」与 `[ascend910b] Not found tiling so file` 的跨 soc 回退对上。**维护者确认**：告警自验证过程同样出现、不影响性能。精度佐证（100% / ~99.96%）为仓自报、无独立复测。
- 溯源下探：[cann-recipes-infer-issue-76-question-example](https://gitcode.com/cann/cann-recipes-infer/issues/76)

<!-- cannbot:related:start -->
## 相关

- [AscendC 自定义算子的构建/打包/可用性坑：vendor 同名覆盖、build.sh op-name 不匹配、未编译则命名空间缺失、镜像滞后源码、逐 SoC AddConfig、并行编译提速](ascendc_custom_op_build_packaging_availability.md)（`related`）：源码注册要求“每个要支持的 SoC 都必须在 `op_host/<op>_def.cpp` 里单写一条 `this->AICore().AddConfig("<soc>")`”，A2 目标重编命令为“bash build.sh -c ascend910b”；源码注册与目标 SoC 重编共同组成跨平台可用性的完整修复链。
<!-- cannbot:related:end -->
