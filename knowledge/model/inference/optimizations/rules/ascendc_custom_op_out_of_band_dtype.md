---
type: Optimization
title: 给 AscendC 自定义算子带外传入 torch 无法表示的 dtype（hifloat8/fp8 族）— int? dtype 参数 + TensorWrapper 包裹
description: 给一个走 torch_ops_extension 的 AscendC 自定义算子扩展输入 dtype，而这个 dtype 是 torch 的 scalar_type 无法表达的（典型是 hifloat8，其它 fp8/低比特族同理）。此时把裸 at::Tensor 直接交给 EXEC_NPU_CMD_V1，aclnn kernel 只能按张量自身的 torch dtype 推断 acl 类型，拿不到真实的 hifloat8——需要一条「把 torch 表示不了的 dtype 带外（out-of-band）传给 kernel」的通路。
tags:
- task.optimization
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/443
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- agnostic
---

# 给 AscendC 自定义算子带外传入 torch 无法表示的 dtype（hifloat8/fp8 族）— int? dtype 参数 + TensorWrapper 包裹

## 适用场景

给一个走 `torch_ops_extension` 的 AscendC 自定义算子扩展**输入 dtype**，而这个 dtype 是 torch 的 `scalar_type` 无法表达的（典型是 hifloat8，其它 fp8/低比特族同理）。此时把裸 `at::Tensor` 直接交给 `EXEC_NPU_CMD_V1`，aclnn kernel 只能按张量自身的 torch dtype 推断 acl 类型，**拿不到真实的 hifloat8**——需要一条「把 torch 表示不了的 dtype 带外（out-of-band）传给 kernel」的通路。

- **适用**：为本仓某个 AscendC 自定义算子的 q/k/输入张量新增 fp8 族 dtype 支持；框架侧仍以普通 torch dtype 的张量承载数据、但要告诉 kernel 按 hifloat8 解释。
- **不适用**：dtype 能被 torch `scalar_type` 表达（fp16/bf16/int8 等）时不需要这套——直接传裸张量即可。

## 做什么（三段式手段）

1. **算子 schema 增 `int?` dtype 参数**——在 `TORCH_LIBRARY(custom, m)` 注册处给每个需要带外 dtype 的张量各挂一个可选整型旋钮，缺省 `None` 时行为与原调用完全一致、不影响既有调用方：

   ```cpp
   "... bool return_value=False, int? query_dtype=None, int? key_dtype=None) -> (Tensor, Tensor)"
   ```

2. **带外 dtype 码用 `+256` 偏移编码 / `-256` 解码**——python 侧传入的整型 = `aclDataType` 枚举值 + `G_TO_AClOFFSET`(256)，算子内减回。来源确认的是解码约定；偏移设计的具体原因未核验，不将 `None` 与整型 0 混为同一种状态：

   ```cpp
   const int G_TO_AClOFFSET = 256;
   // 解码：static_cast<aclDataType>(static_cast<int32_t>(query_dtype.value()) - G_TO_AClOFFSET)
   ```

3. **命中目标 dtype 时用 `TensorWrapper` 包裹裸张量再下发**——新增一个 `make_wrapper` 把裸张量与显式 acl dtype 打包成 `TensorWrapper`，走 hifloat8 分支时对相关张量都包成 `ACL_HIFLOAT8` 再 `EXEC_NPU_CMD_V1`；否则走原裸张量分支：

   ```cpp
   inline TensorWrapper make_wrapper(const at::Tensor& tensor, aclDataType tensor_acltype)
   { return {tensor, tensor_acltype}; }

   bool is_hifloat8_qk = query_dtype.has_value() &&
       static_cast<aclDataType>(static_cast<int32_t>(query_dtype.value()) - G_TO_AClOFFSET) == aclDataType::ACL_HIFLOAT8;
   if (is_hifloat8_qk) {
       TensorWrapper query_wrapper = make_wrapper(query, ACL_HIFLOAT8);
       TensorWrapper key_wrapper   = make_wrapper(key,   ACL_HIFLOAT8);
       EXEC_NPU_CMD_V1(aclnnQuantLightningIndexer, query_wrapper, key_wrapper, ...);
   } else {
       EXEC_NPU_CMD_V1(aclnnQuantLightningIndexer, query, key, ...);   // 裸张量
   }
   ```

   meta 函数要同步加同名形参对齐签名（否则 schema 与 meta 不一致）。

## 参考实现及其约束

参考实现是本仓的量化版 Lightning Indexer 算子 `npu_quant_lightning_indexer`（[lightning-indexer](../../concepts/kernels/lightning_indexer.md) 的量化算子 `npu_quant_lightning_indexer`，下发 `aclnnQuantLightningIndexer`）在其 `ops/ascendc/torch_ops_extension/custom_ops/csrc/` 下加 hifloat8 q/k 通路。约束（属该参考实现、非手段本身的限制）：

- 该 `int?` 参数被**限定只服务 hifloat8**——若传了值但解码结果不是 `ACL_HIFLOAT8`，直接 `TORCH_CHECK` 报错（"The query_dtype is only used to support hifloat8, and should be default when the dtype of query tensor is not hifloat8."）。即这是 hifp8 专用开关、不是通用 dtype override；要支持别的 fp8 族 dtype 需相应放宽门控。
- 缺省不传 dtype 时走裸张量分支、行为不变。

手段本身（`int?` 参数带外传 acl dtype 码 + `TensorWrapper{tensor, acl_dtype}` 包裹）是 `torch_ops_extension` 自定义算子给「torch 无法表示的 dtype」供路的通用套路，可迁移到本仓其它 AscendC 自定义算子加 fp8 族 dtype；不外推为整个昇腾栈通用律。

## 反例 / 边界

- 别指望裸 `at::Tensor` 能承载 hifloat8——kernel 只会按张量的 torch dtype 推断 acl 类型；不加带外通路则拿不到 hifloat8。
- `+256` 偏移是该实现约定的编码方式，python 绑定侧须按同一约定编码，否则解码错位。

## 验证与风险

- **correctness 验证**：缺省不传 dtype 的既有路径应与改动前逐位一致（走裸张量分支）；hifloat8 分支需以该算子的量化精度基线（cos_sim / 端到端指标）核对。
- **风险**：该实现对显式传入的 dtype 码有 hifloat8 专用校验；这不证明底层字节编码正确。错误的承载数据仍须通过算子精度对照发现，不能只依赖门控。

## 相关

- 同族算子的量化选型时延：[quant-lightning-indexer-latency](quant_lightning_indexer_latency.md)（QLI INT8 量化版压时延；本页是给该算子再加 hifloat8 通路）。
- AscendC 自定义算子的其它 host/构建侧经验：[ascendc-custom-op-cross-platform-cann-build](../../runbooks/compilation/ascendc_custom_op_cross_platform_cann_build.md)（跨平台/跨 CANN 版本构建加载）、[superkernel-ascendc-relocatable-binary](superkernel_ascendc_relocatable_binary.md)（让自定义算子可被 SuperKernel 融合）。
- 本仓同类算子存在多后端实现时的选型：[op-backend-selection-ascendc-pypto-tilelang](op_backend_selection_ascendc_pypto_tilelang.md)。
- 概念页：[ascendc](../../concepts/frameworks/ascendc.md) · [fp8-attention](../../concepts/quantization/fp8_attention.md)。

## Evidence

- `diff 事实`（`cann-recipes-infer@5c8d7183e4a1`）：`make_wrapper` / `G_TO_AClOFFSET=256` / `-256` 解码 / `TORCH_CHECK` hifloat8 门控 / `is_hifloat8_qk` 分支的 `TensorWrapper` 包裹 / schema 新增 `int? query_dtype=None, int? key_dtype=None` 均在合入 diff 中逐条对上（`npu_quant_lightning_indexer.cpp`、`ops_def_registration.cpp`）。
- `推断`（非 diff 直述）：「torch 无法用 `scalar_type` 表示 hifloat8、故需带外传 dtype」是对该设计动机的机制推断；`+256` 偏移的具体缘由 diff 未给（未读 python 绑定侧），仅确证「解码 = int − 256」。
- 源未给 before→after 性能/精度数字。
- 溯源下探：[cann-recipes-infer-pr-443-feat-qli-hifp8](https://gitcode.com/cann/cann-recipes-infer/merge_requests/443)。
