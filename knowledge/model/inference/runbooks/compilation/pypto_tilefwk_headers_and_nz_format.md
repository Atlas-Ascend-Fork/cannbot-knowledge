---
type: Runbook
title: 自建 PyPTO 融合算子在社区版 CANN 上因缺 TileFwk 头文件编译失败 + 算子 NZ 格式由 pass 指定
description: '运行期 ModuleNotFoundError: No module named ''custom_ops''（PyPTO 融合算子包没编出来）； 手动编译 ops/pypto 又报 fatal error: tilefwk/tilefwk.h: No such file or directory，或提示缺 register/op_ct_impl_registry.h；在 Ascend toolkit 的 include/lib 里也找不到这些头。'
tags:
- task.debugging
- topic.compilation
- topic.data_movement.layout_transform
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/100
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/53
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/64
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 自建 PyPTO 融合算子在社区版 CANN 上因缺 TileFwk 头文件编译失败 + 算子 NZ 格式由 pass 指定

## 信号（现象）

要在昇腾上跑依赖 [PyPTO](../../concepts/frameworks/pypto.md) 融合算子的模型（如 DSA 系 Lightning Indexer 快路），若不用官方配套的 pypto 镜像、改用社区版 CANN 包自建环境，会连撞两道：

- 运行期 `ModuleNotFoundError: No module named 'custom_ops'`（PyPTO 融合算子包没编出来）；
- 手动编译 `ops/pypto` 又报 `fatal error: tilefwk/tilefwk.h: No such file or directory`，或提示缺 `register/op_ct_impl_registry.h`；在 Ascend toolkit 的 `include/lib` 里也找不到这些头。

## 触发条件

- 用**社区版 CANN 包**（非配套 pypto 镜像）自建环境，编译仓内 `ops/pypto` 融合算子。
- 目标模型的推理路径依赖 PyPTO 算子（观测于 DeepSeek-V3.2-Exp 的 Lightning Indexer PTO 快路）。

## 根因

`tilefwk/*.h`、`register/op_ct_impl_registry.h` 等头由**独立开源的 PyPTO 编译器仓**（`cann/pypto`）提供，**并不随 Ascend/CANN 安装包分发**；社区版 CANN 未随包携带 TileFwk 头，于是任何依赖它的算子编译单元在预处理阶段即失败。这是「头文件来源与 CANN 发行解耦」的结构性缺口，不是路径/环境变量配错。

## 修法

- 从 `cann/pypto` 获取源码，按其 README 构建 TileFwk / PyPTO 工具链后再引入头与库，重新编译 `ops/pypto` 生成 `custom_ops`；或直接换用官方配套的 pypto 镜像（内已含 TileFwk 头与预编译算子）。
- 判据：报错落在**头文件缺失（预处理期）**而非链接期/运行期，且缺的头名带 `tilefwk/` 前缀 → 直接指向 PyPTO 仓，不必去查 CANN 安装是否损坏。

## 附：写 PyPTO 算子时的一条作者侧约定（NZ 格式由 pass 指定）

给 PyPTO 自定义算子写算子信息库（op def 的 Input/Output `Format`）时：**即使权重输入对外是 NZ（[weight-nz](../../concepts/techniques/weight_nz.md)）格式，op info 也只需声明 `FORMAT_ND`**——NZ 的实际排布由 PyPTO 的 pass 在编译期指定，无需在算子信息库里额外增加 NZ format 条目。误加 NZ format 反而与 pass 的约定冲突。这是 PyPTO 与 AscendC OpDef 不同的一点：AscendC 需逐 SoC/格式显式声明，PyPTO 把格式变换下沉到 pass。

## 风险 / 边界

- 自建 TileFwk 须与目标 CANN 版本 ABI 对齐（版本错配会转成运行期 E19999 等更隐蔽的加载失败，那是另一类问题）。
- NZ-by-pass 约定是 PyPTO 特有，不要迁移到 AscendC OpDef 上。

## 相关经验

- AscendC（非 PyPTO）自定义算子的构建/打包/可用性坑见 [ascendc-custom-op-build-packaging-availability](../compilation/ascendc_custom_op_build_packaging_availability.md)；跨平台/跨 CANN 版本构建失败见 [ascendc-custom-op-cross-platform-cann-build](../compilation/ascendc_custom_op_cross_platform_cann_build.md)。
- 用 PyPTO 落地 DSA 融合注意力的组织方法见 [pypto-dsa-fused-attention-decompose-quant](../../optimizations/rules/pypto_dsa_fused_attention_decompose_quant.md)。

## Evidence

- `diff 事实 / 维护者确认`（@2c45117）：`ops/pypto` 依赖 `tilefwk/*.h` 与 `register/op_ct_impl_registry.h`，社区版 CANN 未随包提供，须从 `cann/pypto` 构建；维护者在 issue 中确认修法。
- `diff 事实`（@87f244c）：PyPTO 算子 op info 库对 NZ 权重仍声明 `FORMAT_ND`，NZ 由 pass 指定。
- 溯源下探：[cann-recipes-infer-issue-100-question](https://gitcode.com/cann/cann-recipes-infer/issues/100)、[cann-recipes-infer-issue-53-bug-report-no-module-named-custom-ops](https://gitcode.com/cann/cann-recipes-infer/issues/53)、[cann-recipes-infer-pr-64-feat-lip-li-dia-pypto](https://gitcode.com/cann/cann-recipes-infer/merge_requests/64)