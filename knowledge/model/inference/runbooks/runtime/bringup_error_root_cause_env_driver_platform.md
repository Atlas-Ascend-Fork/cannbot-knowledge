---
type: Runbook
title: 昇腾 bringup 初始化/HCCL 报错的根因常在环境/驱动/平台层，顶层 ACL/HCCL 码是泛化包装
description: 昇腾 bringup 初始化/HCCL 报错的根因常在环境/驱动/平台层，顶层 ACL/HCCL 码是泛化包装。拉起阶段（torch_npu init / 首次集合通信 / 前向前）报错时，先怀疑环境/驱动/平台不匹配，别急着改模型或并行代码。昇腾的顶层 ACL/HCCL 错误码往往是泛化包装，真因在更深的日志行或部署环境里。以下几类症状对号入座即可定位。
tags:
- task.debugging
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/177
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/182
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/22
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/190
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/39
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/issues/2210
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- a3
---

# 昇腾 bringup 初始化/HCCL 报错的根因常在环境/驱动/平台层，顶层 ACL/HCCL 码是泛化包装

## 适用场景

拉起阶段（torch_npu init / 首次集合通信 / 前向前）报错时，**先怀疑环境/驱动/平台不匹配，别急着改模型或并行代码**。昇腾的顶层 ACL/HCCL 错误码往往是泛化包装，真因在更深的日志行或部署环境里。以下几类症状对号入座即可定位。

## 症状 → 根因 → 修法（逐条）

### A. torch_npu init 报 ACL/precision-mode 500001（真因在 EC0010）

- 信号：`AclSetCompileopt(ACL_PRECISION_MODE) error code 500001` + `ERR00100 PTA call acl api failed`。
- 根因：顶层 ACL/precision-mode 报错只是泛化壳；真因在昇腾日志更深处的 `EC0010: Failed to import Python module`——本例是宿主 Python 依赖 `attr` 缺失。
- 修法：**直接读 EC0010 明细行**看缺哪个 Python 模块并补装，别去追 precision_mode / ACL 编译选项。

### F. 同一 500001/EC0010 壳，真因是 numpy>=2.0 与 CANN 8.2.1 不兼容（op-store 初始化炸）

- 信号：`torch.npu.set_device(0)`（或任何触发 GE/TBE 初始化的 torch_npu 首次用设备）抛 `RuntimeError: SetPrecisionMode ... AclSetCompileopt(ACL_PRECISION_MODE) error code 500001`，ascend log 深处出现 `EC0010: Failed to import Python module [AttributeError: np.float_ was removed in the NumPy 2.0 release]` → `AOE Failed to call InitCannKB` → `Failed to init tbe` → `Initialize op store adapter failed, OpsStoreName[tbe-custom]` → `GEInitialize failed`。
- 根因：与 A 同属 EC0010「import Python 模块失败」家族，但缺的不是宿主依赖，而是 **CANN 8.2.1 的 TBE/GE 算子库 Python 适配层（`python_adapter_manager.cc::InitCannKB`）仍引用 NumPy 2.0 已移除的 `np.float_`**；装了 `numpy>=2.0`（如 2.0.2）后该模块 import 直接 `AttributeError`，逐级把 `InitTbeFunc → InitTeFusion → op store adapter → OpsManager → GEInitialize` 整条图初始化链带崩。表面的 `set_device` 500001 / `SetPrecisionMode` 是泛化壳，容易被误读为「ACL 本身坏了」或去抢卡 / 排查驱动。
- 修法：把 numpy 钉到 `< 2.0`（环境约束层修法，非改代码）。命中判据：ascend log 同时出现 `np.float_ was removed` + `InitCannKB` + `Failed to init tbe` 即可直接降 numpy，不必追驱动或设备透传。
- 边界：证据限定在 **CANN 8.2.1**；这是「CANN 版本的算子库 Python 适配尚未跟进 NumPy 2.0 的 API 移除」这一时间点约束，后续 CANN 版本适配后可能解除。它给 A 补了一个**新根因分支**——同样的 EC0010 抬头下，除「宿主缺 Python 模块」外，还有「宿主 numpy 版本与 CANN 算子库 Python 适配不兼容」。

### B. docker 内 aclInit 107001 / Invalid device ID

- 信号：`aclInit error code 107001` / `Invalid device ID` / `invalid drv devId`。
- 根因：`docker run` 未把 NPU 设备（`--device=/dev/davinci*` 等）透传进容器。
- 修法：按 README 的容器拉起命令映射 NPU 设备。

### C. A3 首个 reduce_scatter 报 HCCL error 15 + AICPU 异常（真因驱动过旧）

- 信号：第一个 `reduce_scatter` 处 `HcclReduceScatter error code 15` + AICPU 异常 `RunAicpuKfcResInitV2`（`libccl_kernel.so`, errorCode=0x2a）/ 运行时 507018。
- 根因：不是模型/并行代码，是 **NPU 驱动版本过旧**。
- 修法：升级驱动。

### D. A3 变体核数少于硬编码值 → limit_core EE1001

- 信号：`SetStreamResLimit ... EE1001 The value exceeds the total number of cores (value=24, total=20)`。
- 根因：多流控核 `enable_limit_core` 把 aic 总核数硬编码为 24（`total_aic_num=24`，仅 A3），且 infer.py 只校验 `platform_version=="A3"`、**不校验设备实际核数**；在实际核数少于 24 的 A3 变体（如一站式平台）上越界。
- 修法：把 `enable_limit_core` 设为 `False`（或按实际核数调整）。

### E. A3-only 部署样例在 A2（910B3）上静默卡死

- 信号：照 A3 样例 README 配置在 910B3（Atlas A2）双机启动，**静默卡死在初始化、进不了前向**（无明确报错）。
- 根因：部署样例只面向 Atlas A3 集群，**硬件平台不匹配**（维护者确认 A2 不支持），不是 config 参数问题。
- 修法：换 A3 平台，或另寻该平台原生支持路径；不要在 config 里反复调参试图救活。

## 通用先验

- 顶层报 ACL/HCCL 泛化码时，**往日志深处找带 `EC####` / AICPU / 驱动 的明细行**——那才是根因层。
- bringup 报错先排除五类环境因素：设备透传、驱动版本、宿主 Python 依赖（缺模块）、**宿主关键库版本与 CANN 算子库 Python 适配的兼容性（如 numpy 与特定 CANN 版本）**、平台/核数是否匹配部署样例的目标。
- 同一顶层码（如 500001/`SetPrecisionMode`）+ 同一 EC0010「import Python 模块失败」抬头下，深层真因可能是不同分支（缺依赖 vs 依赖版本不兼容），须读 EC0010 明细里的具体报错文本（`np.float_ was removed` 之类）才能区分，不能只看顶层码。

## 相关经验
- [Ascend 310P 不支持图模式：aclgraph capture 抛 ACL_MODE](ascend_310p_graph_mode_unsupported_enforce_eager.md)

- 缺文件/checkpoint 不完整导致的误报见 [bringup-preparation-missing-files-and-reduced-config](bringup_preparation_missing_files_and_reduced_config.md)。
- 部署镜像组件版本对齐见 [ascend-deployment-image-version-alignment](../../optimizations/experience/rules/ascend_deployment_image_version_alignment.md)；跨平台算子构建见 [ascendc-custom-op-cross-platform-cann-build](../compilation/ascendc_custom_op_cross_platform_cann_build.md)。
- 非默认平台（310P/950）部署适配见 [ascend-deploy-parallel-variant-and-nondefault-platform](../../optimizations/experience/rules/ascend_deploy_parallel_variant_and_nondefault_platform.md)。
- 「拉起后长时间无输出、看似 hang」常是 warmup 静默长耗时而非真故障，先辨阶段见 [warmup-silent-slow-and-dummy-cache](../performance/warmup_silent_slow_and_dummy_cache.md)。

## Evidence

- `diff 事实 / 维护者确认`（@2c45117）：EC0010 缺 `attr`；107001 为 device 未透传；A2 静默卡死为平台不匹配（维护者确认）；`enable_limit_core` 硬编码 24 且只校验 platform_version=="A3"。
- `维护者确认`（@2c45117）：A3 首 reduce_scatter HCCL 15 + AICPU 0x2a 根因驱动过旧、升级解决。
- `维护者确认 + 一手 traceback`（F，vllm-ascend v0.10.0rc1 发布 checklist）：release manager（collaborator）明写「CANN 8.2.1 仍需 pin `numpy < 2.0`」并贴出完整复现栈——`SetPrecisionMode ... error code 500001` → `EC0010 ... AttributeError: np.float_ was removed in the NumPy 2.0 release` → `AOE Failed to call InitCannKB` → `Failed to init tbe` / `op store adapter failed` → `GEInitialize failed`；checklist 项标注「numpy>2.0 not work with CANN 8.2.1」。范围按证据限定到 CANN 8.2.1。
- 溯源下探：[cann-recipes-infer-issue-177-question-torch-npu](https://gitcode.com/cann/cann-recipes-infer/issues/177)、[cann-recipes-infer-issue-182-bug-report-a3-ds4flash](https://gitcode.com/cann/cann-recipes-infer/issues/182)、[cann-recipes-infer-issue-22-bug-report-readme-torchnpu](https://gitcode.com/cann/cann-recipes-infer/issues/22)、[cann-recipes-infer-issue-190-bug-report-models-deepseek-v4-deepseek-v4-flash-runtimeerror-customize-d](https://gitcode.com/cann/cann-recipes-infer/issues/190)、[cann-recipes-infer-issue-39-question-910b3-w8a8-b3](https://gitcode.com/cann/cann-recipes-infer/issues/39)、[vllm-ascend-issue-2210-release-release-checklist-for-v0-10-0rc1](https://github.com/vllm-project/vllm-ascend/issues/2210)