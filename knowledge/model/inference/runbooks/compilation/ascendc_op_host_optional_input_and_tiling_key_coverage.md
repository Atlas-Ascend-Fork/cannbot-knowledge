---
type: Runbook
title: AscendC 算子 host 侧未覆盖运行时可达配置空间：缺省可选输入被无条件读取、模板参数取值未全枚举 → 特定 config 崩溃 / npu fail / 无 tiling key
description: 在昇腾上开发 / 适配 AscendC 自定义算子（proto 的 InferShape/InferDataType 回调、op_host tiling 校验、模板 tiling-key 定义）时，出现「某一部分 config 路径运行时失败、另一些 config 正常」的分裂现象：不传某个可选输入就崩、开/关某个量化开关就报「tiling key 缺失」。根因几乎都在算子 host 侧没有覆盖到运行时实际可达的那个配置——缺省的可选输入仍被无条件读取，或模板实例化矩阵漏枚举了某个会被走到的参数取值。失败落在 host 侧 tiling/prepare 阶段或直接 npu fail，不在 kernel 计算阶段。
tags:
- task.debugging
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/84
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/129
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/166
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# AscendC 算子 host 侧未覆盖运行时可达配置空间：缺省可选输入被无条件读取、模板参数取值未全枚举 → 特定 config 崩溃 / npu fail / 无 tiling key

## 适用场景

在昇腾上开发 / 适配 [AscendC](../../concepts/frameworks/ascendc.md) 自定义算子（proto 的 InferShape/InferDataType 回调、op_host tiling 校验、模板 tiling-key 定义）时，出现「某一部分 config 路径运行时失败、另一些 config 正常」的分裂现象：不传某个可选输入就崩、开/关某个量化开关就报「tiling key 缺失」。根因几乎都在**算子 host 侧没有覆盖到运行时实际可达的那个配置**——缺省的可选输入仍被无条件读取，或模板实例化矩阵漏枚举了某个会被走到的参数取值。失败落在 host 侧 tiling/prepare 阶段或直接 npu fail，不在 kernel 计算阶段。

## 症状 → 根因 → 修法

### A. host 回调无条件读 / 解引用可选（OPTIONAL）输入 → 该输入缺省时崩溃 / npu fail

两个观测实例：

1. **InferDataType 用输入推输出 dtype，却把 DataType 枚举当输入索引传**。[LightningIndexer](../../concepts/kernels/lightning_indexer.md) 的 `InferDataTypeLightningIndexer` 里写 `outputType = context->GetInputDataType(ge::DT_INT32)`——`GetInputDataType(size_t index)` 形参是**输入索引**，而 `ge::DT_INT32` 枚举值恰为 3，调用退化成读 input idx 3 的 dtype。idx 3 是可选输入 `actual_seq_lengths_query`；当它未传入时读缺席可选输入的 dtype 得非法结果并回写输出 dtype → npu fail。而输出 `sparse_indices` 本就恒为 INT32、不该依赖任何输入。
   - 修法：输出 dtype 固定就直接硬编码常量 `ge::DT_INT32`，不从输入推导。

2. **tiling 校验无条件解引用可选输入指针**。`lightning_indexer_quant` 的 tiling `ValidateInputShapesMatch`（非 PA_BSND 的 BSND 布局分支）校验各输入首维是否等于 batch size 时，对可选输入 `actualSeqLengthsK` 直接 `.tensor->GetShapeSize()`，未判空；缺省时 `tensor == nullptr` → 空指针解引用崩溃。
   - 修法：解引用前加 `tensor != nullptr &&` 短路守卫——缺省时跳过该维一致性校验、提供时仍校验 `GetShapeSize() == bSize_`。

根因共性：host 回调把「可选输入一定存在」当默认前提。OPTIONAL 输入按定义可以不传，host 代码却无条件读它的 dtype / shape / 指针。

可迁移原则：AscendC host 侧（InferDataType / InferShape / tiling 校验）碰到 OPTIONAL 输入，必须**先判是否传入再读**；输出 dtype/shape 若固定（如恒为 INT32）就硬编码常量而非从输入推。并警惕把 DataType 枚举误当输入索引传给 `GetInputDataType(idx)`——`DT_INT32==3` 这类会掩盖语义错误、恰好读到某个下标的可选输入。

### B. 模板 tiling-key 未枚举某参数的全部运行时可达取值 → 该 config 无 tiling key 无法分派

- 信号：某个 config（如 dequant 关闭）跑到时用例失败 / 提示 tiling key 缺失，而相邻 config（dequant 开启）正常。
- 根因：AscendC 用 `ASCENDC_TPL_*_SEL` 声明算子的模板实例化矩阵（哪些参数组合会被生成为可分派的 tiling key）。`ASCENDC_TPL_BOOL_SEL(<name>, <values...>)` 枚举某布尔参数被实例化的取值集合；若只登记 `1`（如 [MLA-Prolog](../../concepts/kernels/mla_prolog.md) v3 的 `ASCENDC_TPL_BOOL_SEL(ENABLE_DEQUANT_OPTIONAL, 1)`，在 QUANT_MODE=4/5 两组），运行时走 `ENABLE_DEQUANT_OPTIONAL=0`（dequant 关闭）的配置在矩阵里没有匹配项 → 该 tiling key 不存在 → 分派失败、用例失败。
- 修法：把取值集合补全为 `ASCENDC_TPL_BOOL_SEL(ENABLE_DEQUANT_OPTIONAL, 0, 1)`，让开 / 关两种变体各有 tiling key，运行时按实际取值分派即有匹配。
- 可迁移原则：模板 tiling-key 定义里，某布尔 / 枚举参数在运行时可达的取值必须被 `ASCENDC_TPL_*_SEL` **完整枚举**——缺一个取值就等于缺一个 tiling key，对应配置在运行时无法分派而失败。

## 通用先验

- host 侧算子定义（proto / tiling / tiling-key）是算子对「运行时可达配置空间」的显式声明；任何一处没覆盖到实际会走到的 config（可选输入缺省、参数取值未枚举），都会在运行时那条路径上失败。
- 验证必须覆盖「可选输入不传」和「每个开关 / 量化模式的全部取值」的组合，而不是只测标定过的那组默认配置——默认开关 / 默认传参的自测会掩盖这些分裂失败。

## 风险 / 边界

- 上述具体常量 / 输入次序是各参考实现在其钉定版本的语义，随算子演进可能变；以目标 commit 的算子源为准。
- 放开 tiling-key 取值集合 / 补 tiling 变体后须重新验证：新增变体也要有对应 kernel 实例，否则从「缺 key」变成「有 key 无实现」。

## 参考实现及其约束

- host 回调读可选输入：`lightning_indexer` 的 `InferDataTypeLightningIndexer`（输出 dtype 改硬编码 INT32）、`lightning_indexer_quant` 的 tiling `ValidateInputShapesMatch`（BSND 分支加 nullptr 守卫）。二者的可选输入是 `actual_seq_lengths_query` / `actualSeqLengthsK`。
- 模板 tiling-key：MLA-Prolog v3 的 `mla_prolog_v3_template_tiling_key.h` 的 QUANT_MODE=4/5 两组补 `ENABLE_DEQUANT_OPTIONAL` 的 `0` 取值。
- 范围限本仓这些算子的 host 语义，不外推为整个昇腾栈通用律。观测于 [DSA](../../concepts/modules/dsa.md) 系算子。

## 相关经验

- host tiling 把已知模型的 shape / 必填输入硬编码进白名单、拦截新结构模型 bringup（含 lightning_indexer 在 PA_BSND 下 `block_table`/`actual_seq_lengths_key` 必填契约）见 [fused-op-host-tiling-hardcoded-shape-whitelist](fused_op_host_tiling_hardcoded_shape_whitelist.md)——那是「必填输入契约 / shape 白名单」，与本页「缺省可选输入被无条件读取」互为另一面。
- 自定义算子入图的 InferShape/InferDataType 声明与 converter 的 lowering 正确性（eager 正常、入图才错）见 [custom-op-graph-lowering-converter-meta-correctness](../precision/custom_op_graph_lowering_converter_meta_correctness.md)。

## Evidence

- `diff 事实`（@7aa48998）：`InferDataTypeLightningIndexer` 把 `outputType = context->GetInputDataType(ge::DT_INT32)`（DT_INT32 枚举值 3 被当输入索引、读到可选输入 idx 3）改为硬编码 `ge::DT_INT32`；输入次序经 def.cpp 声明与常量 `ACTUAL_SEQ_K_INDEX=4` 双重确证 idx 3 = `actual_seq_lengths_query`（OPTIONAL）。`DT_INT32==3` 为标准 CANN 枚举取值、未在本仓内定位定义。溯源下探：[cann-recipes-infer-pr-129-fix-fix-path-3-of-li](https://gitcode.com/cann/cann-recipes-infer/merge_requests/129)
- `diff 事实`（@ae8bee2c）：`LIQInfoParser::ValidateInputShapesMatch` 非 PA_BSND 分支对 `actualSeqLengthsK.tensor->GetShapeSize()` 前加 `tensor != nullptr &&` 短路守卫（+2/-1，单 hunk），与「缺省可选输入空指针崩溃」一致。溯源下探：[cann-recipes-infer-pr-166-fix-problem-for-nullptr-in-actual-seqk](https://gitcode.com/cann/cann-recipes-infer/merge_requests/166)
- `diff 事实`（@100bba23）：`mla_prolog_v3_template_tiling_key.h` 的 QUANT_MODE=4/5 两组 `ASCENDC_TPL_BOOL_SEL(ENABLE_DEQUANT_OPTIONAL, 1)` → `(ENABLE_DEQUANT_OPTIONAL, 0, 1)`（+2/-2）。「缺值即缺 tiling key」为宏语义 + 标题「修改tilingkey缺失」+ before→after 推断，未回读宏本体定义。溯源下探：[cann-recipes-infer-pr-84-fix-tilingkey](https://gitcode.com/cann/cann-recipes-infer/merge_requests/84)
