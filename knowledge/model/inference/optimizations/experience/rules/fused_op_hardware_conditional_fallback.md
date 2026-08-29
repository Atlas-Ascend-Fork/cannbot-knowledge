---
type: Optimization
title: 昇腾融合算子按硬件条件门控回退到非融合等价路径（SoC 白名单 / matmul 65535 轴上限）
description: 昇腾融合算子按硬件条件门控回退到非融合等价路径（SoC 白名单 / matmul 65535 轴上限）。在昇腾上适配模型时，融合算子（单算子融合 / NZ 权重 / 融合 matmul）并非对所有 SoC 和所有 shape 都可用。它们常带硬件/形状条件的门控：不满足时须回退到"小算子拼接 / 普通 matmul(ND) / 非融合"的等价路径，否则精度/加载出问题。移植或调优时，检查融合算子路径是否有 SoC 白名单或轴上限守卫，并确保有对应 fallback。下面两条是已固化进本仓的实例（写"路由把这组条件当作融合路径不适用"、而非"算子在该硬件上不能运行"）。
tags:
- task.optimization
- topic.model_architecture
- topic.parallelism
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/393
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/395
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a3
---

# 昇腾融合算子按硬件条件门控回退到非融合等价路径（SoC 白名单 / matmul 65535 轴上限）

## 条件 → 优先尝试什么

在昇腾上适配模型时，融合算子（单算子融合 / NZ 权重 / 融合 matmul）并非对所有 SoC 和所有 shape 都可用。它们常带**硬件/形状条件的门控**：不满足时须回退到"小算子拼接 / 普通 matmul(ND) / 非融合"的等价路径，否则精度/加载出问题。移植或调优时，检查融合算子路径是否有 SoC 白名单或轴上限守卫，并确保有对应 fallback。下面两条是已固化进本仓的实例（写"路由把这组条件当作融合路径不适用"、而非"算子在该硬件上不能运行"）。

## 实例一：hc_pre 算子按 SoC 版本门控，命中即强制走 composite

[hc_pre](../../../concepts/kernels/mhc_hcpre_hcpost.md)（[MHC](../../../concepts/modules/mhc.md) / hyper-connection 预处理）AscendC 自定义算子 `npu_hc_pre_npu` 有两条实现分支：`hc_pre_fusion`（单融合算子 `aclnnHcPre`）与 `hc_pre_composite`（一串小算子拼接 fallback）。

修复前，非 Ascend950 的 Ascend910 分支只按 batch 判路由，会在满足 bs 条件时在 A3（`Ascend910_9362 / Ascend910_9372`）等 SoC 上进入融合单算子。diff 新增 SoC 黑名单门控：

```cpp
static const std::set<std::string> invalid_versions = {"Ascend910_9362", "Ascend910_9372",
                                                       "Ascend910B3", "Ascend910B4-1", "Ascend910B4"};
const bool isValidAscend910 = socName != nullptr && invalid_versions.count(std::string(socName)) == 0;
...
} else {  // 非 Ascend950 的 Ascend910 分支
    if (!isValidAscend910 || bs > SINGLE_OP_MAX_BS || bs % SINGLE_OP_BS_ALIGN_FACTOR != 0) {
        return hc_pre_composite(...);   // 命中 invalid_versions → 无论 bs 都走 composite
    }
    return hc_pre_fusion(...);          // aclnnHcPre 融合单算子
}
```

合并后完整路由：① 非 Ascend950 且 `d == 7168` → composite；② Ascend950（`socName` 前缀 `"Ascend950"`）→ bs 满足时 fusion 否则 composite；③ 其它 Ascend910 → 仅当 `isValidAscend910` 且 bs 满足时 fusion，否则 composite——即 `invalid_versions` 内的 SoC **无论 bs 都走 composite**。命中路径可从 `ASCEND_LOGI`（`"Use fused operator..."` vs `"...concatenation of small operators."`）区分。

- SoC 名对应平台（常识注释）：`Ascend910_9362/9372` 属 Atlas A3（910_93 系）、`Ascend910B3/B4-1/B4` 属 Atlas A2（910B 系）。
- 这组 SoC「为何 invalid」（精度差 / 未实现 / 崩溃）仓未披露、维护者仅 `/lgtm /approve`——不断言原因，只知路由把它们当作融合路径不适用。

## 实例二：matmul 轴超 65535 → 融合 matmul + NZ 权重不可用，回退 torch.matmul(ND)

在 [A3](../../../concepts/platforms/atlas_a3.md) 上适配大注意力维度模型（[DeepSeek-V4](../../../concepts/models/deepseek_v4.md) 的 pro 变体，注意力维度更大）时，注意力相关 matmul 轴（`n_heads*head_dim`，或按 oproj [张量并行](../../../concepts/parallelism/tensor_parallel.md)切分后的 per-rank 轴）会超过常量 `MATMUL_MAX_AXIS_VALUE = 65535`。超过它时避开融合算子 `torch_npu.npu_transpose_batchmatmul` 与 [NZ 权重格式](../../../concepts/techniques/weight_nz.md)，回退到普通 `torch.matmul`（ND）：

```python
# o 投影（Attention.forward）：per-rank 轴超限 + 平台 A3 → torch.matmul 回退
if self.n_heads * self.head_dim // self.oproj_tp_size > MATMUL_MAX_AXIS_VALUE and \
   self.platform_version == "A3":
    o = torch.matmul(o.transpose(0, 1), self.wo_a.weight).transpose(0, 1).contiguous()
else:
    o = torch_npu.npu_transpose_batchmatmul(o, self.wo_a.weight, perm_x1=(1, 0, 2), perm_y=(1, 0, 2))

# wq_b 权重（process_weights_after_loading）：未切分轴超限 → 禁 NZ、保持 ND
is_wq_b_transpose = hf_config.num_attention_heads * hf_config.head_dim > MATMUL_MAX_AXIS_VALUE
is_weight_nz = False if "compressor" in module_name or (is_wq_b_transpose and "wq_b" in module_name) \
                     else self.enable_weight_nz
```

- 两处条件不同、须分别对待：o 投影用 **per-rank** 轴（`//oproj_tp_size`）且**带** `== "A3"` 平台门控；`wq_b` 用**未切分**轴 `num_attention_heads*head_dim` 且**不带**平台门控。
- "65535 是 matmul 轴硬件/算子上限"这一"为何"由常量名 + A3 门控 + 主动避开融合算子反推，源未给算子规格或维护者确认——不并入事实面；核心动作（超限回退）是 diff 事实。
- 迁移警示：o 投影回退用 `== "A3"` 门控，950/FP8 分支是否需同样处理未有定论（reviewer 曾问"是否也影响 950 fp8 分支"，答复未捕获），迁移到其它平台须复核。同 diff 另把 oproj 张量并行度上界从硬编码 `>8` 改为配置驱动 `> config.o_groups`。

## 相关经验
- [Ascend 310P 不支持 Triton kernel：走 Triton 的算子须补纯](../../../runbooks/runtime/ascend_310p_no_triton_kernel_eager_fallback.md)
- [256-expert MoE 的融合 allgather-EP 专家链（四算子融合，硬门控在](fused_allgather_ep_moe_256expert_deepseek_v3r1.md)

- 另见 [weight-NZ 与 MC2 mm_all_reduce 融合按层互斥：走 MC2 的 RowParallel 层权重必须留 ND](weight_nz_mc2_mm_all_reduce_exclusion.md)。


## Evidence

- **代码事实**（实例一，clone `@339549a2ceae`）：同 sha 下 `npu_hc_pre.cpp` `npu_hc_pre_npu` 全函数——SoC 门控集合 `invalid_versions` 与回退路由为 diff 事实；SoC「为何 invalid」仓未披露。
- **代码事实**（实例二，clone `@e988315e9334`，3 文件全量）：`modeling_deepseek.py` o 投影回退、`runner_deepseek.py` `wq_b` 禁 NZ、各自条件/平台门控均按 diff 原文核对；`65535` 作为"轴上限"的语义为推断，已标层级。
- **维护者确认**：实例一 SoC 门控经维护者 `/lgtm /approve` 合入，未披露「为何 invalid」的原因（精度差 / 未实现 / 崩溃）。
- **归因边界**：归因主语为 cann-recipes-infer 的算子路由 / 这两条改动，非上游模型厂商；适用面限本仓这些算子，不升为通用律。
- 溯源下探：[cann-recipes-infer-pr-393-fix-a3-hcpre](https://gitcode.com/cann/cann-recipes-infer/merge_requests/393)、[cann-recipes-infer-pr-395-feat-adapt-dsv4-pro-on-a3](https://gitcode.com/cann/cann-recipes-infer/merge_requests/395)

<!-- cannbot:related:start -->
## 相关

- [昇腾融合算子 host-tiling 的硬编码 shape 白名单 / 必填输入契约拦截新结构模型 bringup](../../../runbooks/compilation/fused_op_host_tiling_hardcoded_shape_whitelist.md)（`related`）：昇腾融合算子把 host tiling 做成「按已知模型的固定 shape 特化」以简化 kernel 分支——特化点表现为**硬编码常量白名单 / assert / 必填输入约束**。它们不是技术本身的限制，而是**该参考实现只覆盖了标定过的那组 shape**。新结构模型的维度落在白名单外时被 host 校验挡下，报错常在 tiling/prepare 阶段而非 kernel 计算阶段。；在昇腾上适配模型时，融合算子（单算子融合 / NZ 权重 / 融合 matmul）并非对所有 SoC 和所有 shape 都可用。它们常带**硬件/形状条件的门控**：不满足时须回退到"小算子拼接 / 普通 matmul(ND) / 非融合"的等价路径，否则精度/加载出问题。移植或调优时，检查融合算子路径是否有 SoC 白名单或轴上限守卫，并确保有对应 fallback。下面两条是已固化进本仓的实例（写"路由把这组条件当作融合路径不适用"、而非"算子在该硬件上不能运行"）。。Runbook识别参考实现 shape 白名单，规则卡给出硬件或 shape 门控失败时切换非融合等价路径的处置原则。
<!-- cannbot:related:end -->
