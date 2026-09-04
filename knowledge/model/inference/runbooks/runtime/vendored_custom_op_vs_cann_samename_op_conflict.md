---
type: Runbook
title: 自带（vendored）自定义算子与 CANN 库同名算子冲突：torch_npu.npu_* 解析走偏 / 接口漂移
description: 两者共同的场景：仓内自带的自定义算子与 CANN 侧提供的同名算子（torch_npu 内建 / ops-transformer 合入的算子）并存，调用解析到了「错的那一份」。
tags:
- task.debugging
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/117
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/130
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 自带（vendored）自定义算子与 CANN 库同名算子冲突：torch_npu.npu_* 解析走偏 / 接口漂移

## 信号（现象）

在昇腾上部署一套「随仓自带（vendored）+ 本地编译安装」的 AscendC 自定义算子后，调用某算子出现两类症状：

- 走 `torch_npu.npu_<op>(...)` 别名调用时报**位置参数个数不符**，声明里的命名空间是 `npu::`（不是仓内的 `custom::`）：

  ```
  RuntimeError: npu::npu_sparse_flash_attention() takes 5 positional argument(s) but 6 was/were given.
  Declaration: npu::npu_sparse_flash_attention(Tensor query, Tensor key, Tensor value,
    Tensor sparse_indices, float scale_value, *, Tensor? block_table=None, ...
    int sparse_block_size=1, ...)   # sparse_block_size 在 * 之后 = 仅限关键字
  ```

- 或某个自带融合算子安装后**运行即失败**，与已装的 CANN 算子库同名算子对不上。

两者共同的场景：仓内自带的自定义算子与 CANN 侧提供的**同名**算子（[torch_npu 内建](../../concepts/frameworks/ascendc.md) / `ops-transformer` 合入的算子）并存，调用解析到了「错的那一份」。

## 触发条件

- 仓内 vendored 一批 AscendC 自定义算子（`custom::` 命名空间，经 `torch.ops.custom.*` 暴露、并 `setattr` 别名挂到 `torch_npu`）。
- CANN / torch_npu 侧发行了**同名**算子，但签名或接口与仓内副本不一致：
  - torch_npu 自身在较新构建里发行了 `npu::npu_<op>` 内建算子（位置参数个数与仓内副本不同）；
  - 或该算子早先合入 CANN `ops-transformer` 时改过接口，而仓内自带副本停在旧接口。

## 根因

- **命名空间碰撞（别名解析走偏）**：仓内 `custom_ops/__init__.py` 把 `torch.ops.custom` 下的每个算子逐个 `setattr(torch_npu, op_name, ...)`，`torch_npu.npu_<op>` 只是**挂载别名、不是真名**。只有先按仓内 README 编译并 `import custom_ops`、`torch.ops.custom` 存在时，该别名才指向仓内副本；一旦较新 torch_npu 自身发行了同名内建算子并抢占该属性解析，`torch_npu.npu_<op>` 就落到内建版本上。仓内 `custom::npu_sparse_flash_attention` 把 `sparse_block_size` 定义为**位置参数**（6 个位置参数），内建 `npu::` 版把它放在 `*` 之后（**仅限关键字**、只收 5 个位置参数），于是同一份 6 位置参数的调用被内建版拒绝。
- **跨仓接口漂移**：同名算子（如 [mla_prolog_v3](../../concepts/kernels/mla_prolog.md)）合入 CANN `ops-transformer` 时改了接口，而仓内自带副本未同步适配 → 安装仓内自定义算子后，自带副本与已装 CANN 库同名算子接口不匹配、运行失败。

## 修法

按优先级：

1. **消歧调用**：编译好仓内自定义算子后，用无歧义的 `torch.ops.custom.npu_<op>(...)` 调用，避开被内建算子抢占的 `torch_npu.*` 别名。
2. **对齐版本**：把 CANN / 算子版本严格对齐到仓 README（或直接用其钉定镜像），不要把仓内自带算子与不匹配的 CANN 算子库混用。
3. **根治——弃用自带副本、改调 op-plugin**：让建模代码统一调 op-plugin 暴露的 `torch_npu.npu_<op>`（如 `torch_npu.npu_mla_prolog_v3`），删除仓内 vendored 同名副本。当前仓已对 `mla_prolog_v3` 走这条路（`ops/ascendc/src` 下不再有它，各建模文件改调 op-plugin 同名算子）。
4. **备选（针对内建抢占）**：若确需仓内副本，可把 torch_npu 降回不发行该内建同名算子的构建，让 `torch_npu.*` 别名回到仓内版本；或直接改用 CANN 包内同名算子并按其签名把差异参数作为**关键字**传。

## 适用边界

仓内 `ops/ascendc` 仍 vendored 十余个自定义算子（`indexer_compress_epilog` / `kv_compress_epilog` / [gather_selection_kv_cache](../../concepts/kernels/gather_selection_kv_cache.md) / [hc_pre / hc_post](../../concepts/kernels/mhc_hcpre_hcpost.md) / `moe_gating_top_k_hash` / `swiglu_clip_quant` 等）。凡「仓内自带副本」与「CANN 库同名算子」并存者，命名空间碰撞与跨仓接口漂移都是**可复发**的失败类——把「自带算子 vs CANN 库同名算子解析/接口不匹配」列为算子运行失败的**首查根因**，而非默认任意 CANN 安装都兼容。别名挂载机制不随某个样例算子被删而失效，对当前保留的其它自带算子同样成立。部署镜像 CANN 包过旧、被迫保留自带副本过渡的情形见 [ascend-deployment-image-version-alignment](../../optimizations/experience/rules/ascend_deployment_image_version_alignment.md)；跨平台 / 跨 CANN 版本的构建期失败见 [ascendc-custom-op-cross-platform-cann-build](../compilation/ascendc_custom_op_cross_platform_cann_build.md)。

## Evidence

- **命名空间碰撞 · diff 事实**（clone `@98946b6` / `@2c45117`）：`ops_def_registration.cpp` 的 `custom::npu_sparse_flash_attention` 签名确为 6 个位置参数（`sparse_block_size` 在 `*` 前），样例按 6 个位置参数调用；报错声明里的 `npu::` 版为 5 个位置参数（`sparse_block_size` 仅限关键字）——两签名差异精确解释 "takes 5 ... but 6 were given"。`custom_ops/__init__.py` 的 `setattr(torch_npu, op_name, custom_op_func)` 别名挂载在钉定 sha 仍在、且作用于当前保留的其它自带算子。**维护者确认**：建议用 CANN 包内同名算子、或按 README 编译方式调仓内算子，或降 torch_npu 版本。
  - 溯源下探：[cann-recipes-infer-issue-117-bug-report-test-npu-sparse-flash-attention-py](https://gitcode.com/cann/cann-recipes-infer/issues/117)
- **接口漂移 · 维护者确认 + diff 事实**（clone `@239c0c1a`）：`ops/ascendc/src/` 现存 vendored 算子中已**无 `mla_prolog_v3`**（已移除），各建模文件改调 `torch_npu.npu_mla_prolog_v3`。维护者确认根因（算子合入 ops-transformer 时改了接口、recipes 未同步）与修法（已适配、当时用 README 镜像规避）。
  - 溯源下探：[cann-recipes-infer-issue-130-bug-report-mla-prolog-v3-cann-transformer](https://gitcode.com/cann/cann-recipes-infer/issues/130)

<!-- cannbot:related:start -->
## 相关

- [AscendC 自定义算子的构建/打包/可用性坑：vendor 同名覆盖、build.sh op-name 不匹配、未编译则命名空间缺失、镜像滞后源码、逐 SoC AddConfig、并行编译提速](../compilation/ascendc_custom_op_build_packaging_availability.md)（`related`）：安装期存在“新包会**整包覆盖**同名 `customize` vendor 包”，运行期则可能因“仓内自带的自定义算子与 CANN 侧提供的**同名**算子”发生解析与接口冲突；二者共同构成同名自定义算子的打包覆盖与调用消歧排障链。
- [昇腾部署镜像的组件版本对齐（torch_npu / 驱动 HDK / CANN 包）与过渡态规避](../../optimizations/experience/rules/ascend_deployment_image_version_alignment.md)（`related`）：“因为部署镜像的 CANN 包过旧、旧镜像上直接调内置版会缺算子”与“调用解析到了「错的那一份」”分别覆盖内置算子缺失和同名实现解析错误，属于升级镜像后的同一算子来源排查链。
<!-- cannbot:related:end -->
