---
type: Concept
title: weightNZ Format
description: '将 Matmul 类算子的权重 Tensor 转成昇腾 NPU 亲和的 **NZ 分形布局**（512 字节对齐），提升硬件访存带宽效率，加速 DeepSeek-R1 等模型的 Prefill / Decode Matmul 计算。由 YAML `enable_weight_nz: True` 使能，模型加载阶段由 `convert_model.py` 对权重做一次性离线/在线转换。'
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_prefill_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a3
---

# weightNZ Format

## Summary

将 Matmul 类算子的权重 Tensor 转成昇腾 NPU 亲和的 **NZ 分形布局**（512 字节对齐），提升硬件访存带宽效率，加速 DeepSeek-R1 等模型的 Prefill / Decode Matmul 计算。由 YAML `enable_weight_nz: True` 使能，模型加载阶段由 `convert_model.py` 对权重做一次性离线/在线转换。

## Mechanism

- NZ 是昇腾 Cube 单元亲和的"分形"数据布局：内层 16 × 16（或 16 × 32，视 dtype 而定）的 tile 沿外层 row/col 堆叠，满足 **512 字节对齐**。
- 相对于 ND（普通 row-major）布局，NZ 布局使 L1/L0A/L0B 的数据加载指令更长、连续，**硬件带宽访问效率显著提升**。
- 转换示例：int8 Tensor shape `[16384, 7168]` → NZ 布局 `[224, 1024, 16, 32]`（内层 16 × 32，int8 下 512 字节对齐：N 维 7168/32=224、K 维 16384/16=1024）。
- 覆盖范围：模型中所有 Matmul 权重（Q/K/V proj、gate_up_proj、down_proj、kv_b_proj、o_proj、MoE experts GroupedMatMul、lm_head 等），不覆盖 LayerNorm/RMSNorm/RoPE 的非 matmul tensor。

### 代码入口

`models/deepseek_r1/models/modeling_deepseek.py:L925` / `L2093` / `L2408`：

```python
self.enable_weight_nz = self.infer_config.model_config.enable_weight_nz
# ...
if isinstance(quant_method, QuantizeMethodBase):
    quant_method.process_weights_after_loading(
        module, is_nz=self.enable_weight_nz, scales_dtype=scales_dtype)
```

NZ 转换没有独立的 `process_weight_nz` 函数，而是由 module 的 `quant_method`（`QuantizeMethodBase` 派生类）在加载后通过 `process_weights_after_loading(module, is_nz, scales_dtype)` 原地执行（无返回值赋回 `module`）；量化 scales 也配合 `scales_dtype` 做相应转换。

## Applicable Scenarios

- 任何以 Matmul 为主的 LLM 推理路径。
- BF16 / W8A8 / W8A8C8 都适用；量化路径下权重已是 int8，转换为 NZ 后带宽优势更明显。
- DeepSeek-R1 全部 Decode / Prefill YAML 默认 `enable_weight_nz: True`。

## Constraints

- 权重需要一次性转换，加载时间略增；对静态权重推理无影响。
- 对训练或需要频繁修改权重的场景不适合。
- 与其他权重格式优化（如 `cache_mode="PA_NZ"` 的 KVCache NZ 布局）相互配合但互不依赖。

## Known Results

源文档未给出 weightNZ 单项提升幅度；其作为 DeepSeek-R1 Prefill/Decode 各 YAML 默认开启的基线优化之一，与其他项叠加的总体吞吐见 [deepseek-r1](../models/deepseek_r1.md) Benchmark 章节。**单独 A/B 数据缺失，待验证**。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-r1/deepseek_r1_prefill_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_prefill_optimization.md) "Matmul 类算子使能 weightNZ 格式"章节；`models/deepseek_r1/config/*.yaml` 中 `enable_weight_nz: True`；`models/deepseek_r1/models/modeling_deepseek.py` 中 `process_weight_nz`。

## Links

- [deepseek-r1](../models/deepseek_r1.md)
- [ascendc](../frameworks/ascendc.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [inference-config](inference_config.md)
- [vggt](../../../spatial/concepts/models/vggt.md)（跨域·空间智能：VGGT 二维卷积核 NZ 私有格式提前转换）
