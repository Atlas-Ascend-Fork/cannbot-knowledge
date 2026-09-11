---
type: Runbook
title: AscendC 自定义算子的构建/打包/可用性坑：vendor 同名覆盖、build.sh op-name 不匹配、未编译则命名空间缺失、镜像滞后源码、逐 SoC AddConfig、并行编译提速
description: AscendC 自定义算子的构建/打包/可用性坑：vendor 同名覆盖、build.sh op-name 不匹配、未编译则命名空间缺失、镜像滞后源码、逐 SoC AddConfig、并行编译提速。围绕 AscendC 自定义融合算子从「构建 → 打包 → 判定可用」的全链路，有一组反复出现的坑。bringup/联调阶段遇到「算子调不到 / 装完丢了旧算子 / 构建报奇怪错」时对照。
tags:
- task.debugging
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/86
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/87
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/69
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/198
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/41
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/429
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/312
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# AscendC 自定义算子的构建/打包/可用性坑：vendor 同名覆盖、build.sh op-name 不匹配、未编译则命名空间缺失、镜像滞后源码、逐 SoC AddConfig、并行编译提速

## 适用场景

围绕 [AscendC](../../concepts/frameworks/ascendc.md) 自定义融合算子从「构建 → 打包 → 判定可用」的全链路，有一组反复出现的坑。bringup/联调阶段遇到「算子调不到 / 装完丢了旧算子 / 构建报奇怪错」时对照。

## 一、判定某算子是否已就绪（内省注册表，别直接调）

- 仓内 AscendC 算子统一注册在 PyTorch `torch.ops.custom` 命名空间下，`import custom_ops`（build 后的扩展模块）触发注册。
- 判某融合算子是否就绪：`hasattr(torch.ops.custom, name)` 查单个、`dir(torch.ops.custom)` 枚举全部——**而非直接调用**。未注册的算子在 `torch.ops.custom` 上表现为 `AttributeError`（算子未编译进 `custom_ops` 或未 import）。
- 症状：未编译安装自定义算子的基础镜像（如普通 sglang 镜像）里跑示例，调 `torch.ops.custom.<op>`（如 `npu_mla_prolog_v3`）抛 `AttributeError: '_OpNamespace' 'custom' object has no attribute '<op>'` → 先按 `ops/ascendc` 编译安装融合算子 run 包 + `custom_ops` wheel 再跑（A2/910B 加 `-c ascend910b`，非配套 CANN 镜像加 `--disable-check-compatible`）。

## 二、镜像里的算子可能滞后于源码

README 指定的预构建 Docker 镜像内置的 AscendC 算子会**滞后于 `ops/ascendc` 源码**——新合入源码的算子要等一个单独的镜像刷新 PR 把 README 镜像版本号 bump 后才进镜像。判据：源码里有该算子、镜像里 `hasattr` 查不到 → 自建或等镜像刷新，别怀疑代码。

## 三、打包踩坑

### vendor 同名整包覆盖

- 用 `ops/ascendc` 流程编译安装时若沿用默认 `VENDOR_NAME=customize`，新包会**整包覆盖**同名 `customize` vendor 包（如镜像自带的 custom_ops），使新包未包含的旧算子（如 `npu_selected_flash_attention`）从 `exist:True` 变 `exist:False`。
- 修法：把 `ops/ascendc/CMakeLists.txt` 的 `VENDOR_NAME` 改成唯一名（如 `customize_xxxx`），两包各占独立 vendor 目录共存。

### build.sh -n/--op-name 取注册目录名，传错报 No SOURCES

- `bash build.sh -n/--op-name` 取的是 `ops/{ascendc,pypto}/src/` 下的**注册算子目录名**（不带 `npu_` 前缀）。传一个不匹配任何注册算子的名字（典型错误：把 torch 侧 `npu_`-前缀名当构建名）会让 CMake 的 `opsproto`/`optiling` 目标拿到空 SOURCES，报 `No SOURCES given to target: opsproto/optiling` + `ops prepare build failed`，**而非**清晰的「算子不存在」提示。

## 四、逐 SoC 显式 AddConfig（默认只建 A3）

AscendC 算子（`OpDef` 模式）按 SoC 逐个显式注册目标硬件——每个要支持的 SoC 都必须在 `op_host/<op>_def.cpp` 里单写一条 `this->AICore().AddConfig("<soc>")`，**不跨 SoC 自动继承**。只注册 `ascend910_93` 的算子在 `ascend910b` 上不可用，须补 `AddConfig("ascend910b")` 才能在 Atlas A2 / Ascend 910B 上启用。这是「默认构建只支持 A3」的源级根因——某些算子光靠 `build.sh -c ascend910b` 不够，必须先在算子源补 AddConfig。

## 五、构建提速

AscendC 算子的 torch 扩展（`NpuExtension` + `torch.utils.cpp_extension.BuildExtension`）编译慢时，启用 ninja 构建后端 + 按核数并行（`MAX_JOBS`）可显著缩短编译墙钟（仓自报约 5min→1min，无独立复测）。

## 相关经验

- A2/A3 SoC 编译目标不匹配的加载期/编译期失败见 [ascendc-custom-op-cross-platform-cann-build](ascendc_custom_op_cross_platform_cann_build.md)。
- vendored 算子与 CANN 同名算子的运行期命名空间冲突/接口漂移见 [vendored-custom-op-vs-cann-samename-op-conflict](../runtime/vendored_custom_op_vs_cann_samename_op_conflict.md)。
- PyPTO 算子的 TileFwk 头缺失见 [pypto-tilefwk-headers-and-nz-format](pypto_tilefwk_headers_and_nz_format.md)。

## Evidence

- `diff 事实`（@2c45117）：`VENDOR_NAME=customize` 整包覆盖同名 vendor；`build.sh -n` 取 src 注册目录名、错名报 No SOURCES；`torch.ops.custom` 未注册算子 AttributeError；镜像内置算子滞后源码。
- `diff 事实`（@3fa4f62）：`OpDef` 逐 SoC `AddConfig`，只有 ascend910_93 时 A2 不可用。
- `仓自报`（@2ce177b）：ninja + `MAX_JOBS` 并行把算子编译约 5min→1min（无独立复测）。
- 溯源下探：[cann-recipes-infer-issue-86-requirement-ops-custom-ops-custom-ops-custom-ops](https://gitcode.com/cann/cann-recipes-infer/issues/86)、[cann-recipes-infer-issue-87-bug-report-ops-bash-build-sh-op-name-n-op-name](https://gitcode.com/cann/cann-recipes-infer/issues/87)、[cann-recipes-infer-issue-69-requirement-910b-example-readme](https://gitcode.com/cann/cann-recipes-infer/issues/69)、[cann-recipes-infer-pr-198-feat-check-ops-check-more-ops-and-list-all-existing-custom-ops](https://gitcode.com/cann/cann-recipes-infer/merge_requests/198)、[cann-recipes-infer-issue-41-bug-report-readme-pr](https://gitcode.com/cann/cann-recipes-infer/issues/41)、[cann-recipes-infer-pr-429-fix-fix-scatter-nd-update-asc-def-cpp-to-support-910b](https://gitcode.com/cann/cann-recipes-infer/merge_requests/429)、[cann-recipes-infer-pr-312-feat-optimize-ops-ascendc-torch-api-compile-time-cost-using-multi-proces](https://gitcode.com/cann/cann-recipes-infer/merge_requests/312)