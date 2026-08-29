---
type: Runbook
title: 调用昇腾融合算子撞 host-tiling 参数/布局拦截：按报错对号量化场景·cacheMode 维度·TND 必填输入契约
description: The ckvkrRepoMode expected %d, but got %d. / The quantScaleRepoMode expected %d, but got %d. / The queryQuantMode expected %d, but got %d.；Only support cacheMode (BSND, TND, PA_BSND, PA_NZ), actually is .；When tokenX dim is 3, Only support cacheMode (BSND, PA_BSND, PA_NZ)...（及 KVCache dim / BSND 侧对称文案）；expected shape is , the first dim should not be 0.；when the layout of key and value is TND, the actualSeqLengths of key and value shoule not be empty.（shoule 为源码原文拼写）
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/136
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/101
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 调用昇腾融合算子撞 host-tiling 参数/布局拦截：按报错对号量化场景·cacheMode 维度·TND 必填输入契约

## 信号（现象）

在昇腾上调用 AscendC 融合算子（MLA-Prolog 融合算子 `npu_mla_prolog_v3` / 稀疏 FlashAttention SFA），算子还没真正执行、host tiling 阶段就被拦截失败，报错形如：

- `The ckvkrRepoMode expected %d, but got %d.` / `The quantScaleRepoMode expected %d, but got %d.` / `The queryQuantMode expected %d, but got %d.`
- `Only support cacheMode (BSND, TND, PA_BSND, PA_NZ), actually is <cacheMode>.`
- `When tokenX dim is 3, Only support cacheMode (BSND, PA_BSND, PA_NZ)...`（及 KVCache dim / BSND 侧对称文案）
- `expected shape is <...>, the first dim should not be 0.`
- `when the layout of key and value is TND, the actualSeqLengths of key and value shoule not be empty.`（`shoule` 为源码原文拼写）

这些不是随机崩溃，而是 host-tiling 校验按「量化场景 / cacheMode / 布局」逐项核对入参、任一不符即以 `OPS_LOG_E`+`GRAPH_FAILED` 或 `GRAPH_PARAM_INVALID` 精确拦截。报错文案带期望值 vs 实际值，可直接对号定位违约参数。

## 触发条件

- 量化推理走 MLA-Prolog 融合算子，传入 `weightQuantMode` / `kvQuantMode` / `queryQuantMode` / `ckvkrRepoMode` / `quantScaleRepoMode` 组合。
- 用 paged / 非 paged KV cache 走 MLA-Prolog，传 `cacheMode` 字符串 + tokenX / kvCache 张量。
- 用 [SFA](../../concepts/kernels/sparse_flash_attention.md) 且 `qk_layout` / `layoutKV = TND`（路径 0/3）。

## 契约（对号入座）

### MLA-Prolog 融合算子（[mla-prolog](../../concepts/kernels/mla_prolog.md)）量化场景参数

量化场景由 `weightQuantMode`（PARTIAL/FULL_QUANT）+ `kvQuantMode`（NO_QUANT / PER_CHANNEL / PER_TILE / PER_TENSOR）推定（不再把 `queryQuantMode` 揉进场景判定，改为逐参数独立校验）。对该场景，两个 repoMode 与 `queryQuantMode` 必须严格对号：

- **repoMode（ckvkrRepoMode & quantScaleRepoMode）**：PER_TILE 类场景（`PARTIAL/FULL_QUANT_KV_QUANT_PER_TILE`）→ 两者都 `== COMBINE`；其余所有量化场景 → 两者都 `== DIVIDE`。
- **queryQuantMode**：`PARTIAL_QUANT_KV_QUANT_PER_CHANNEL` 场景 → `== PER_TOKEN_HEAD`；其余场景 → `== NO_QUANT`。

逐参数独立校验、任一非法即失败并打印 `The <param> expected %d, but got %d`。据报错参数名 + 当前量化场景（由 weight/kv QuantMode 决定）查上表，即知该改成 COMBINE / DIVIDE / PER_TOKEN_HEAD / NO_QUANT 中的哪个。

### MLA-Prolog 融合算子 cacheMode / 张量维度

- **cacheMode 收窄**到 `{BSND, TND, PA_BSND, PA_NZ}`；`PA_BLK_BSND` / `PA_BLK_NZ` 已删除。任何白名单外字符串（含旧的 block-paged 模式）都会命中 `Only support cacheMode (...)`。
- **cacheMode ↔ tokenX/kvCache 张量秩绑定**：`TND` → (tokenX 2D, kvCache 3D)；`BSND` → (tokenX 3D, kvCache 4D)。维度与 cacheMode 不匹配即报 `When tokenX/KVCache dim is N, Only support cacheMode (...)`。校验为累加器式，一次调用把所有 cacheMode/维度违规都报出、不再只报第一个。

### SFA TND 布局必填输入

[sparse-flash-attention](../../concepts/kernels/sparse_flash_attention.md) 在 `qk_layout = TND` 下 host tiling 强制两条前置条件，违反以 `ge::GRAPH_PARAM_INVALID` 拦截：

- 必须传**非空 key**（空 key → keyT/keyD=0 → expected shape 首维=0 → `expected shape is <...>, the first dim should not be 0.`）。
- 必须传**非空 actualSeqLengths**（未传 → `when the layout of key and value is TND, the actualSeqLengths ... shoule not be empty.`）。

仓级约定：这类非法入参返回码用 `ge::GRAPH_PARAM_INVALID` 而非 `GRAPH_FAILED`（维护者 review 落定）——这也是本仓 AscendC 算子入参校验错误码的参照，见 [ascendc-op-input-validation-pitfalls](../../optimizations/experience/anti_patterns/ascendc_op_input_validation_pitfalls.md)。

## 修法（改调用侧，不改算子）

按报错参数名 + 上面的契约表把调用侧入参改对：量化场景配齐 COMBINE / DIVIDE / PER_TOKEN_HEAD / NO_QUANT；cacheMode 用四个合法值之一且 tokenX/kvCache 秩对齐；SFA TND 传非空 key + 非空 actualSeqLengths。这些是这些融合算子当前版本的调用契约，不是可绕过的软约束——旧版对错误参数组合的宽松放行已被收紧。

## 相关

- 契约背后「host-tiling 校验为何要逐参数独立 guard、可选输入为何要 nullptr 守卫」的写法侧经验：[ascendc-op-input-validation-pitfalls](../../optimizations/experience/anti_patterns/ascendc_op_input_validation_pitfalls.md)。
- 同类「融合算子调用契约随后端/版本不同、传错即 schema/报错」的另一例：[fia-actual-seq-lengths-kv-backend-type](../runtime/fia_actual_seq_lengths_kv_backend_type.md)。
- MLA-Prolog + paged KV cache 的 Prefill 写法约束：[mla-prolog-zigzag-cp-kv-write](../../optimizations/experience/rules/mla_prolog_zigzag_cp_kv_write.md)。

## Evidence

- diff 事实（clone `@91c9e771`，`ops/ascendc/src/mla_prolog_v3/op_host/mla_prolog_v3_tiling_check.cpp` / `mla_prolog_v3_tiling.cpp`）：`CheckScenarParam` 的 repoMode/queryQuantMode 期望值 + 报错文案；`CheckCacheMode` 白名单收成 `{BSND, TND, PA_BSND, PA_NZ}`、按 cacheMode 校验 tokenX/kvCache 维度、`SetScenarioInfo` 删 `PA_BLK_*` 分支——逐条对上。仓自报 docker fuzz 通过，无独立复测数字。
  - 溯源下探：[cann-recipes-infer-pr-136-fix-mlaprologv3](https://gitcode.com/cann/cann-recipes-infer/merge_requests/136)
- diff 事实 + 维护者确认（clone `@ddce49993e14`，`ops/ascendc/src/sparse_flash_attention/op_host/sparse_flash_attention_tiling.cpp`，`SFATilingCheck::GetExpectedShape` / `CheckActualSeqLens`）：TND 空 key 与漏 actualSeqLengths 两处守卫、返回码 `GRAPH_PARAM_INVALID`、两条错误文案；错误码 `GRAPH_PARAM_INVALID` 为维护者 review 明确要求并落定。
  - 溯源下探：[cann-recipes-infer-pr-101-fix-sfa-0-3-qk-layout-tnd-key-tensor-keyt-keyd-0](https://gitcode.com/cann/cann-recipes-infer/merge_requests/101)

<!-- cannbot:related:start -->
## 相关

- [AscendC 算子入参校验的静默失效陷阱：可选输入漏 nullptr 守卫·&& 串联漏拦截·meta 侧漏守卫](../../optimizations/experience/anti_patterns/ascendc_op_input_validation_pitfalls.md)（`related`）：这些不是随机崩溃，而是 host-tiling 校验按「量化场景 / cacheMode / 布局」逐项核对入参、任一不符即以 `OPS_LOG_E`+`GRAPH_FAILED` 或 `GRAPH_PARAM_INVALID` 精确拦截。报错文案带期望值 vs 实际值，可直接对号定位违约参数。；把多个必需参数的合法性写成一个 `&&` 串联的 guard——语义是「**所有**参数同时非法才报错」，单个参数非法时 guard 不触发、非法配置静默放行。例：PER_TILE 量化场景要求两个 repoMode 都 COMBINE，写成 `ckvkrRepoMode != COMBINE && quantScaleRepoMode != COMBINE` 才报错，则只有一个错时漏拦；NO_QUANT 场景更用 5 路 `&&`（weight/kv/query QuantMode + 两个 repoMode 全部非法才报），几乎形同虚设。。Runbook依赖 host 校验精确拦截量化组合，反模式卡指出用 && 组合非法条件会漏掉单项违约，直接影响该诊断链可信度。
- [昇腾融合算子 host-tiling 的硬编码 shape 白名单 / 必填输入契约拦截新结构模型 bringup](fused_op_host_tiling_hardcoded_shape_whitelist.md)（`related`）：昇腾融合算子把 host tiling 做成「按已知模型的固定 shape 特化」以简化 kernel 分支——特化点表现为**硬编码常量白名单 / assert / 必填输入约束**。它们不是技术本身的限制，而是**该参考实现只覆盖了标定过的那组 shape**。新结构模型的维度落在白名单外时被 host 校验挡下，报错常在 tiling/prepare 阶段而非 kernel 计算阶段。；这些不是随机崩溃，而是 host-tiling 校验按「量化场景 / cacheMode / 布局」逐项核对入参、任一不符即以 `OPS_LOG_E`+`GRAPH_FAILED` 或 `GRAPH_PARAM_INVALID` 精确拦截。报错文案带期望值 vs 实际值，可直接对号定位违约参数。。两卡共同处理 kernel 前的 host-tiling 拦截：一张识别硬编码 shape 白名单，另一张按量化、cacheMode 与布局定位合同违约。
<!-- cannbot:related:end -->
