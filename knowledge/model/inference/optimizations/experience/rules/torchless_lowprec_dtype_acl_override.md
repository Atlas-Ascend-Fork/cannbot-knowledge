---
type: Optimization
title: torch 无对应 dtype 的硬件低精度格式（如 HiFloat8 KV 量化）：在 aclnn 算子调用边界覆写 acl dtype
description: torch 无对应 dtype 的硬件低精度格式（如 HiFloat8 KV 量化）：在 aclnn 算子调用边界覆写 acl dtype。在昇腾 torch_ops_extension 里给自定义 aclnn 算子喂一种硬件低精度格式（如 hif8 / HiFloat8）的张量，而 PyTorch / torch_npu 没有对应的张量 dtype 时——不要试图在 torch 侧构造一个该格式的 dtype 张量（构造不出来）。改走：「按原始字节存的张量 + 在 EXEC_NPU_CMD 调用边界用 TensorWrapper 显式覆写 acl dtype」，让算子把底层字节按目标 aclDataType（如 ACL_HIFLOAT8）解读。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/196
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# torch 无对应 dtype 的硬件低精度格式（如 HiFloat8 KV 量化）：在 aclnn 算子调用边界覆写 acl dtype

## 条件 → 优先尝试什么

在昇腾 [torch_ops_extension](../../../concepts/frameworks/ascendc.md) 里给自定义 aclnn 算子喂一种**硬件低精度格式**（如 hif8 / HiFloat8）的张量，而 PyTorch / torch_npu **没有对应的张量 dtype** 时——不要试图在 torch 侧构造一个该格式的 dtype 张量（构造不出来）。改走：**「按原始字节存的张量 + 在 `EXEC_NPU_CMD` 调用边界用 `TensorWrapper` 显式覆写 acl dtype」**，让算子把底层字节按目标 `aclDataType`（如 `ACL_HIFLOAT8`）解读。

## 依据（参考实现）

KV cache 用 hif8 量化后，KV 张量在 device 上是按 hif8 的字节存的，但 torch 没有 hif8 这个 dtype，**无法通过张量自身 dtype 把「这是 HIFLOAT8」传给底层 aclnn 算子**。若沿用「直接把 KV optional 张量透传给 `EXEC_NPU_CMD_V1`」的老路径（fp8 e4m3 等走的路径），算子无从得知这批字节应按 HIFLOAT8 解读。

参考实现在稀疏注意力 KV 量化算子 QSAS（`aclnnKvQuantSparseAttnSharedkv`，对应 [sparse-attn-sharedkv](../../../concepts/kernels/sparse_attn_sharedkv.md)）：新增一个把张量 + 显式 acl dtype 打包成 `TensorWrapper` 的工具，并在调用点按 `kv_quant_mode` 分支处理——

```cpp
inline TensorWrapper make_wrapper(const at::Tensor& tensor, aclDataType tensor_acltype) {
    return {tensor, tensor_acltype};
}
...
if (kv_quant_mode == 10) {                 // 10 for hif8 kv quant
    at::Tensor null_tensor;
    auto ori_kv_value = ori_kv.has_value() ? ori_kv.value() : null_tensor;   // optional 解成实值，空则 undefined 占位
    auto cmp_kv_value = cmp_kv.has_value() ? cmp_kv.value() : null_tensor;
    TensorWrapper ori_kv_wrapper = make_wrapper(ori_kv_value, ACL_HIFLOAT8);  // 显式覆写 acl dtype
    TensorWrapper cmp_kv_wrapper = make_wrapper(cmp_kv_value, ACL_HIFLOAT8);
    EXEC_NPU_CMD_V1(aclnnKvQuantSparseAttnSharedkv, q, ori_kv_wrapper, cmp_kv_wrapper, ...);
} else {
    EXEC_NPU_CMD_V1(aclnnKvQuantSparseAttnSharedkv, q, ori_kv, cmp_kv, ...);  // fp8 e4m3 及其它模式：透传 optional，不覆写
}
```

关键对比：**hif8 分支显式覆写 `ACL_HIFLOAT8`，fp8 e4m3 / 其它模式分支不覆写、直接透传 optional 张量。** 这正是「torch 无 hif8 dtype，须在算子边界显式给 acl dtype」这条规则的体现。

## 迁移面

适用于走 `EXEC_NPU_CMD_*` / `TensorWrapper` 调用约定的自定义 aclnn 算子：当要传入一种硬件低精度格式（hif8 等，尤其新增的 [C8 类](../../../concepts/quantization/w8a8c8.md) KV 量化 / [低精度 attention](../../../concepts/quantization/fp8_attention.md) 路径）而 torch 侧没有对应 dtype 时，走「原始字节张量 + 边界覆写 acl dtype」，而非构造一个 torch 侧的该格式张量。

## 反例 / 边界

- torch 已有对应 dtype 的低精度格式（如 fp8 e4m3 有 `torch.float8_e4m3fn`）**无需覆写**，直接透传张量即可——覆写只在「torch 无法表达该 dtype」时才需要。
- 「因为 torch 无 hif8 dtype 才需覆写」为合理推断（源码注释仅标 `10 for hif8`，未明写此因），不作硬事实。
- 该规则只讲**如何正确传递**该格式，不保证任一 SoC / CANN 版本都支持该量化格式本身（可用性门控见 [quant-format-dtype-platform-cann-version-gating](../../../runbooks/precision/quant_format_dtype_platform_cann_version_gating.md)）。收益 / 正确性无独立数据（源未给 benchmark / 精度）。

## Evidence

- **diff 事实**（clone `@a34ce8e16efb`）：`npu_kv_quant_sparse_attn_sharedkv.cpp` 的 `make_wrapper` + `kv_quant_mode == 10` 分支 + `ACL_HIFLOAT8` 覆写、以及「fp8 走透传 / hif8 走覆写」的对比，均为读到的真实 diff。
  - 溯源下探：[cann-recipes-infer-issue-196-requirement-a5-qsas-kv-quant-fp8-e4m3-hifp8-kv-quant](https://gitcode.com/cann/cann-recipes-infer/issues/196)
