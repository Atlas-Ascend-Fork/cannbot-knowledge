---
type: Runbook
title: bringup 前置准备与缺文件误报：未内置上游建模代码 / checkpoint 拷贝不完整 + 清 ATC 缓存 / 减层跑通功能验证
description: bringup 前置准备与缺文件误报：未内置上游建模代码 / checkpoint 拷贝不完整 + 清 ATC 缓存 / 减层跑通功能验证。bringup 早期的一类报错根因是缺文件 / 文件不完整 / 环境残留，报错信息却指向别处（PYTHONPATH、NoneType、算子）。另有两条bringup 期功能验证的操作技巧（清缓存、减层）能省事。
tags:
- task.debugging
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/178
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/54
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/31
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/72
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# bringup 前置准备与缺文件误报：未内置上游建模代码 / checkpoint 拷贝不完整 + 清 ATC 缓存 / 减层跑通功能验证

## 适用场景

bringup 早期的一类报错根因是**缺文件 / 文件不完整 / 环境残留**，报错信息却指向别处（PYTHONPATH、NoneType、算子）。另有两条**bringup 期功能验证的操作技巧**（清缓存、减层）能省事。

## 缺文件 / 不完整的误报（对号入座）

### A. ModuleNotFoundError：上游建模代码未内置

- 信号：拉起某模型报 `ModuleNotFoundError: <upstream_module>`（如 `hunyuan_image_3`）。
- 根因：**不是 PYTHONPATH 问题**——仓未内置上游建模代码。
- 修法：按 readme 从官方开源仓下载该建模代码、拷入工作目录后才能导入。

### B. config NoneType subscript / safetensors 0% 段错误：checkpoint 拷贝不完整

- 信号：`load_weights` 里 `self.config.architectures[0]` 抛 `TypeError: 'NoneType' object is not subscriptable`，并伴 safetensors 加载 0% 处 Segmentation fault。
- 根因：`config.json 未正常 load`，实测由**权重/checkpoint 文件拷贝不完整**引起。
- 修法：校验整份权重目录（含 config.json）拷贝完整后重试，别去查建模代码。

## bringup 功能验证的操作技巧

### C. 跨用例先清 ATC 算子编译缓存

- 同一昇腾 NPU 环境跨用例复用时，残留的算子编译缓存（默认落 `/root/atc_data/`）可能污染当前用例，应在 bringup / 环境初始化阶段**先清该缓存再启动推理**。
- ⚠️ 该路径是容器内目录，容器外直接 `rm -rf` 有误删宿主机文件的风险，须按实际部署环境调整缓存路径。

### D. 减少层数在少卡上跑通功能

- 想在不满足全量部署卡数（如 8 卡 910C / 16 芯起步）的机器上「跑通功能」时，可把建模 config 的 `self.num_hidden_layers`（如默认 61）调小到至少 4 层，让流水线在更少卡上启动做**功能性验证**（非精度/性能）。

## 通用先验

- bringup 报 `ModuleNotFound` / config `NoneType` / safetensors 段错误，优先怀疑**缺建模代码 / checkpoint 不完整**，而非代码逻辑。
- 跨用例复用同环境先清算子编译缓存；少卡只做功能验证时减层数。

## 风险 / 边界

- 容器外 `rm -rf` ATC 缓存有误删风险，按部署环境定路径。
- 减层只验功能、不代表精度/性能；验完须换回全层。

## 相关经验

- 初始化/HCCL 报错根因在驱动/设备层见 [bringup-error-root-cause-env-driver-platform](bringup_error_root_cause_env_driver_platform.md)。
- set-env 清缓存与 weight_convert 需 source setenv 见 [quant-weight-conversion-path-selection](../../guides/experience/interventions/quant_weight_conversion_path_selection.md)。

## Evidence

- `维护者确认`（@2c45117）：`hunyuan_image_3` 未内置、须下载上游代码；config NoneType 由 checkpoint 拷贝不完整引起；清 `/root/atc_data/` 缓存；减 `num_hidden_layers` 到 ≥4 做功能验证。
- 溯源下探：[cann-recipes-infer-issue-178-bug-report-models-hunyuan-image-3-0](https://gitcode.com/cann/cann-recipes-infer/issues/178)、[cann-recipes-infer-issue-54-bug-report-deepseek-v3-2-exp-w8a8c8-8p-16](https://gitcode.com/cann/cann-recipes-infer/issues/54)、[cann-recipes-infer-issue-31-question-set-env-sh-rm-rf](https://gitcode.com/cann/cann-recipes-infer/issues/31)、[cann-recipes-infer-issue-72-question-8-910c](https://gitcode.com/cann/cann-recipes-infer/issues/72)

<!-- cannbot:related:start -->
## 相关

- [config/tokenizer 侧车与属性约定的 bringup 陷阱：MoE 属性名别名、yaml 布尔透传丢失、tokenizer chat_template 缺失](config_tokenizer_sidecar_and_attr_alias.md)（`related`）：HF 权重目录里缺 chat_template；缺文件 / 文件不完整 / 环境残留。前者给出 tokenizer sidecar 缺 chat_template 的具体症状与修复，后者给出 bringup 阶段缺件误报的通用检查顺序；联合可先验证权重目录完整性再追查框架属性错误。
- [昇腾 bringup 初始化/HCCL 报错的根因常在环境/驱动/平台层，顶层 ACL/HCCL 码是泛化包装](bringup_error_root_cause_env_driver_platform.md)（`related`）：缺文件 / 文件不完整 / 环境残留；先怀疑环境/驱动/平台不匹配，别急着改模型或并行代码。前者覆盖模型代码、checkpoint 与编译缓存准备问题，后者覆盖驱动、设备透传和平台错配；二者合并成 bringup 早期按阶段排除环境侧根因的互补诊断树。
<!-- cannbot:related:end -->
