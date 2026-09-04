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

<!-- cannbot:related:start -->
## 相关

- [TransposeBatchMatMulWeightNZ 950 ACLNN 算子知识](../../../../ops/ascendc/operators/aclnn/nn/matmul/transpose_batch_mat_mul_weight_nz_950.md)（`related`）：WeightNZ 改变的是 `x2` 的 FRACTAL_NZ 物理存储；准备权重时需同时满足算子的格式和对齐要求。
- [TransposeQuantBatchMatMul 950 ACLNN 算子知识](../../../../ops/ascendc/operators/aclnn/nn/matmul/transpose_quant_batch_mat_mul_950.md)（`related`）：普通 TransposeQuantBatchMatMul 不支持 WeightNz/FRACTAL_NZ，采用 NZ 权重时需选择匹配的专用入口。
- [TransposeQuantBatchMatMulWeightNz 950 ACLNN 算子知识](../../../../ops/ascendc/operators/aclnn/nn/matmul/transpose_quant_batch_mat_mul_weight_nz_950.md)（`related`）：它与 `aclnnTransposeQuantBatchMatMul` 共用内部 `TransposeQuantBatchMatMul` L0 op，但独有“x2 必须 FRACTAL_NZ”校验，不能把 ND 权重接口视为 WeightNz 版本。；将 Matmul 类算子的权重 Tensor 转成昇腾 NPU 亲和的 **NZ 分形布局**（512 字节对齐），提升硬件访存带宽效率，加速 DeepSeek-R1 等模型的 Prefill / Decode Matmul 计算。算子格式校验由 Weight NZ 概念卡补充制备目的与布局语义。
- [sglang 单卡 tp1 拉起 OOM：关 ACL/NZ 权重格式转换（SGLANG_NPU_DISABLE_ACL_FORMAT_WEIGHT=1）](../../runbooks/performance/sglang_tp1_oom_disable_nz_weight.md)（`related`）：将 Matmul 类算子的权重 Tensor 转成昇腾 NPU 亲和的 **NZ 分形布局**（512 字节对齐），提升硬件访存带宽效率，加速 DeepSeek-R1 等模型的 Prefill / Decode Matmul 计算。；**触发**：tp1（单卡承载全权重）+ 昇腾把权重转成 ACL/NZ（fractal）格式的额外显存开销，一起超出单卡容量。概念卡说明 NZ 性能收益，runbook 给出单卡 OOM 时关闭格式转换的反向边界与验证信号。
- [weight-NZ 与 MC2 mm_all_reduce 融合按层互斥：走 MC2 的 RowParallel 层权重必须留 ND](../../optimizations/experience/rules/weight_nz_mc2_mm_all_reduce_exclusion.md)（`related`）：将 Matmul 类算子的权重 Tensor 转成昇腾 NPU 亲和的 **NZ 分形布局**（512 字节对齐），提升硬件访存带宽效率，加速 DeepSeek-R1 等模型的 Prefill / Decode Matmul 计算。；**凡走 MC2 融合的 RowParallelLinear 层，其权重必须留 ND、不转 NZ**；非 MC2 层照常按 `enable_weight_nz` 转 NZ。前者定义 NZ 优化，后者给出与 MC2 融合同时启用时必须逐层排除的布局边界。
- [自建 PyPTO 融合算子在社区版 CANN 上因缺 TileFwk 头文件编译失败 + 算子 NZ 格式由 pass 指定](../../runbooks/compilation/pypto_tilefwk_headers_and_nz_format.md)（`related`）：PyPTO 在编译期通过 pass 指定 NZ 排布，OpInfo 可仅声明 ND；权重准备仍需匹配实际布局。
<!-- cannbot:related:end -->
