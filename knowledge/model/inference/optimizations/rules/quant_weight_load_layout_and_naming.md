---
type: Optimization
title: 昇腾量化权重的加载期布局/命名处理：W4A8 MoEGMM 三件套、剔除零 offset、scale 改名门控、NZ 按 dtype 门控
description: 昇腾量化权重的加载期布局/命名处理：W4A8 MoEGMM 三件套、剔除零 offset、scale 改名门控、NZ 按 dtype 门控。给昇腾算子喂量化权重时，converter 产出的布局和加载器的命名/格式处理有一组固定约定；无条件套用（不门控、不清理）会让权重与算子契约对不上、或参数被静默漏加载。
tags:
- task.optimization
- topic.precision
- topic.compilation
- topic.data_movement.layout_transform
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/13
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/464
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/205
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/296
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/422
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/4797
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:29:20Z'
platforms:
- agnostic
---

# 昇腾量化权重的加载期布局/命名处理：W4A8 MoEGMM 三件套、剔除零 offset、scale 改名门控、NZ 按 dtype 门控

## 适用场景

给昇腾算子喂量化权重时，converter 产出的布局和加载器的命名/格式处理有一组固定约定；无条件套用（不门控、不清理）会让权重与算子契约对不上、或参数被静默漏加载。

## 一、W4A8 MoEGMM 的 int4 专家权重三件套布局

给昇腾 W4A8 MoEGMM 算子喂 int4 专家权重时，光有「逐元素 int4 + FP32 scale」不够，converter 须产出**三件套**随权重同目录保存，共同满足算子输入契约：

- **int4 权重两两沿输出通道打包进一个 byte**；
- **per-channel FP32 scale 转成 UINT64**（低 32 位放 fp32 bit、高位补零）；
- **一份 `assistance_bias`**（`(scale·weight·8)` 沿输入维求和；`8` = INT4 最大值，用于归一化辅助 bias 的量化范围），以 `.bias` 落盘。

（陈述为「converter 当前产出此布局」；这是该 W4A8 MoEGMM 参考实现的输入约定。）

## 二、对称 W8A8 的恒零 offset 要剔除

对称 [W8A8](../../concepts/quantization/w8a8c8.md) 量化产出的 safetensors 仍带**恒零 `weight_offset` 张量**；交给昇腾 sglang 加载前须先**剔除这些 offset 张量并同步重建 `weight_map` 索引**，否则权重与 index 不一致。

## 三、scale→weight_scale 改名必须门控

量化权重加载中把参数名里的 `scale` 改写为 `weight_scale` 这一步**必须按 `any("w13_weight_scale" in key for key in params_dict)` 条件门控**——无条件改写会在 params_dict 不使用 `weight_scale` 专家命名的量化配置下把参数名改错，导致该参数在随后的 `if name not in params_dict: continue` 处被**静默跳过、权重漏加载**。

## 四、NZ 格式转换按 dtype 门控，别按模块名

加载期决定是否做 NZ（[weight-nz](../../concepts/techniques/weight_nz.md)）格式转换（`npu_format_cast(w, 29)`），应**按权重 dtype 门控**（`is_nz and weight.dtype != torch.float32`）、**而非按模块名字符串匹配**——float32 的 MoE gate/router 打分层天然被排除。转置/布局按 NZ 开关统一取 MatMul 最优组合（ND→nk、NZ→kn，维护者确认）。

## 五、取 MoE experts 量化方法：别假设有聚合权重键，按 experts 前缀扫描聚合

给 MoE 模型取「某层量化方法 / 是否 skip 量化」时，量化后端常按 `prefix + '.weight'` 去量化描述表（`quant_description`）里查一个聚合权重键。对普通 linear 层这成立，但 **MoE experts 的量化配置往往按逐专家序号 + 投影名命名**，形如：

```
"model.layers.3.mlp.experts.255.gate_proj.weight":        "W8A8_DYNAMIC"
"model.layers.3.mlp.experts.255.gate_proj.weight_scale":  "W8A8_DYNAMIC"
"model.layers.3.mlp.experts.255.down_proj.weight":        "W8A8_DYNAMIC"
... (up_proj 同)
```

配置里**根本不存在**聚合的 `model.layers.3.mlp.experts.weight` 键——它带专家序号（`255`）与投影名（`gate_proj/down_proj/up_proj`）。此时无条件走「查聚合键」分支会抛 `KeyError: model.layers.N.mlp.experts.weight not in quant_description`，加载中断。

**信号（现象）**：加载按 per-expert-index 命名的 W8A8（乃至任意逐专家命名）MoE 量化模型时报 `KeyError`，缺失键形如 `...mlp.experts.weight`——即代码把 experts 当成有一个聚合权重键，而配置按逐专家键铺开，两者对不上。

**通用修法（思想）**：识别到 `experts` 前缀时不再查单一聚合键，而是**扫描 `quant_description` 中所有命中该 experts 前缀的键、聚合其量化类型**。前提假设：**同一 MLP 内所有专家用同一量化方法**——因此聚合结果应收敛到单一量化类型：

- 判「是否 skip 量化」：取该前缀下全部专家键的量化类型，`any(== "FLOAT")` 即视为该 experts 块跳过量化。
- 取「linear 量化类型」：把命中键的量化类型收进 set，若 set 元素多于一个（同一 MLP 内专家量化类型不一致）应 `RuntimeError` 明确报错，否则取唯一值。

这条把「按名字查一个键」纠正成「按前缀聚合一组键」，是逐专家命名量化配置的通用取数方式，不绑定具体模型。

### 参考实现及其约束（vLLM-Ascend）

vLLM-Ascend 昇腾量化后端 `vllm_ascend/quantization/` 在两处各加一条 `elif "experts" in prefix:` 分支实现上述聚合：

```python
# quant_config.py  is_layer_skipped_ascend
elif "experts" in prefix:
    experts_quant_description = [
        self.quant_description[layer]
        for layer in self.quant_description if prefix in layer
    ]
    is_skipped = any(quantization == "FLOAT"
                     for quantization in experts_quant_description)

# utils.py  get_linear_quant_type
elif "experts" in prefix:
    experts_quant_description = set(quant_description[layer]
                                    for layer in quant_description
                                    if prefix in layer)
    if not len(experts_quant_description) == 1:
        raise RuntimeError(
            f"{prefix} has different quantization type: {experts_quant_description}.")
    quant_type = experts_quant_description.pop()
```

约束（属该参考实现、非技术本身）：

- **只在 eager 模式路径上验证过**；仅要求「整块 experts 量化一致」，专家间量化类型混用会被 `RuntimeError` 挡下。
- **匹配边界**：参考实现用 `prefix in layer` 子串匹配，复用时应核对命名边界并考虑 `layer.startswith(prefix + ".")`。不能把子串匹配当作严格的命名边界校验，也不能仅据这一写法断言某一具体层号已经误归组。

## 通用先验

- 量化加载里凡是「改名 / 剔张量 / 转格式」的操作都要**先按 config/dtype 门控**，不要无条件套——无条件处理在不同量化配置下会漏参数或错位。
- converter 产出布局是「当前产出」，不等于「算子只能吃这一种」；写文档时区分二者。

## 相关经验
- [复用共享融合算子/量化方法到不同结构模型时的静默规格失配（MoE 默认 SiLU 遇 GEG](../../runbooks/runtime/shared_fused_op_default_spec_mismatch.md)

- compressed-tensors 方案识别门控见 [compressed-tensors-scheme-gating-pitfalls](../../runbooks/precision/compressed_tensors_scheme_gating_pitfalls.md)。
- 量化制备路径选择见 [quant-weight-conversion-path-selection](../../guides/deployment/quant_weight_conversion_path_selection.md)；分片 vocab embedding padding_idx / MTP 层号本地化见 [shard-local-index-vocab-padding-mtp-layer](../../runbooks/runtime/shard_local_index_vocab_padding_mtp_layer.md)。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/13)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/464)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/205)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/296)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/422)（evidence）
- [远程来源](https://github.com/vllm-project/vllm-ascend/pull/4797)（evidence）
