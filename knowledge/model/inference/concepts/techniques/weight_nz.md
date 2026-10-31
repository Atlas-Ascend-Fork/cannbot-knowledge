---
type: Concept
title: weightNZ Format
description: '将 Matmul 类算子的权重 Tensor 转成昇腾 NPU 亲和的 **NZ 分形布局**（512 字节对齐），提升硬件访存带宽效率，加速 DeepSeek-R1 等模型的 Prefill / Decode Matmul 计算。由 YAML `enable_weight_nz: True` 使能，模型加载阶段由 各模块 `quant_method.process_weights_after_loading` 执行 NZ 转换；`convert_model.py` 负责权重量化转换。'
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:39Z'
platforms:
- a3
---
# weightNZ Format

## Summary

将 Matmul 类算子的权重 Tensor 转成昇腾 NPU 亲和的 **NZ 分形布局**（512 字节对齐），提升硬件访存带宽效率，加速 DeepSeek-R1 等模型的 Prefill / Decode Matmul 计算。由 YAML `enable_weight_nz: True` 使能，模型加载阶段由 各模块 `quant_method.process_weights_after_loading` 执行 NZ 转换；`convert_model.py` 负责权重量化转换。

## Mechanism

- NZ 是昇腾 Cube 单元亲和的"分形"数据布局：内层 16 × 16（或 16 × 32，视 dtype 而定）的 tile 沿外层 row/col 堆叠，满足 **512 字节对齐**。
- 相对于 ND（普通 row-major）布局，NZ 布局使 L1/L0A/L0B 的数据加载指令更长、连续，**目标是提高适配算子的硬件访问效率，实际收益需测量**。
- 转换示例：int8 Tensor shape `[16384, 7168]` → NZ 布局 `[224, 1024, 16, 32]`（内层 16 × 32，int8 下 512 字节对齐：N 维 7168/32=224、K 维 16384/16=1024）。
- 覆盖范围：仅覆盖实际由相应 quant_method 执行 NZ 转换的模块与 dtype，不能概括为所有 Matmul。固定 R1 的遍历明确跳过 kv_b_proj；init_splited_kv_b_weight 仅连续化拆分权重，没有 NZ 转换。module/linear.py 的非量化 Linear 还排除 float32 权重。LayerNorm/RMSNorm/RoPE 等非 Matmul tensor 不在此范围。

### 代码入口

当前R1的process_weights_after_loading和各量化method：

```python
self.enable_weight_nz = self.infer_config.model_config.enable_weight_nz
# ...
if isinstance(quant_method, QuantizeMethodBase):
    quant_method.process_weights_after_loading(
        module, is_nz=self.enable_weight_nz, scales_dtype=scales_dtype)
```

NZ 转换没有独立的 `process_weight_nz` 函数，而是由 module 的 `quant_method`（`QuantizeMethodBase` 派生类）在加载后通过 `process_weights_after_loading(module, is_nz, scales_dtype)` 原地执行（无返回值赋回 `module`）；量化 scales 也配合 `scales_dtype` 做相应转换。

## Applicable Scenarios

- 有对应NZ算子支持的Matmul推理路径。
- BF16 / W8A8 / W8A8C8 都适用；量化路径下权重已是 int8，是否从NZ获益还取决于实际算子和shape。
- DeepSeek-R1 全部 Decode / Prefill YAML 默认 `enable_weight_nz: True`。

## Constraints

- 权重需要一次性转换，加载时间略增；转换后布局必须与消费算子匹配。
- 对训练或需要频繁修改权重的场景不适合。
- 与其他权重格式优化（如 `cache_mode="PA_NZ"` 的 KVCache NZ 布局）相互配合但互不依赖。

## Known Results

源文档未给出 weightNZ 单项提升幅度；其作为 DeepSeek-R1 Prefill/Decode 各 YAML 默认开启的基线优化之一，与其他项叠加的总体吞吐见[R1 Prefill 来源观测](../../optimizations/benchmark_observations/deepseek_r1_a3_prefill_source_benchmark.md)及[R1 Decode 来源观测](../../optimizations/benchmark_observations/deepseek_r1_a3_decode_source_benchmark.md)。**单独 A/B 数据缺失，待验证**。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md)（primary）
- [deepseek_r1_prefill_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md)（supporting）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（implementation）
- [linear.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py)（implementation）

## Links

- [deepseek-r1](../models/deepseek_r1.md)
- [ascendc](../frameworks/ascendc.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [inference-config](inference_config.md)
- [vggt](../../../spatial/concepts/models/vggt.md)（跨域·空间智能：VGGT 二维卷积核 NZ 私有格式提前转换）
