---
type: Optimization
title: A5(Ascend950) MXFP8 fused-MoE：进分组 matmul 前激活量化 scale 必须打包成 [M, N//2, 2] 并中心化收口
description: A5(Ascend950) fused-MoE MXFP8(w8a8_mxfp8) 推理路径上，进下游分组 matmul(npu_grouped_matmul_swiglu_quant / gmm)前的激活量化 scale 必须做布局归一化：二维 [M,N] scale(dtype FLOAT8_E8M0FNU_DTYPE / E8M0)须 reshape 成打包三维 [M,N//2,2]，相邻两个 scale 打进最后一维。判据「scale 二维 + 最后一维 N 偶数 → 打包成 [M,N//2,2]；N 奇数直接 ValueError，不静默降级」。A5 分组 matmul kernel 期望打包三维布局，而上游 npu_dynamic_mx_quant / npu_dynamic_quant 产出二维，须用中心化 DeviceAdaptor 方法(maybe_normalize_mxfp_scale_layout)统一收口：基类 no-op、A5 override 才 reshape，避免各分支各写一遍漏做。三类接入点：动态量化产 scale 出口(注意 dynamic_scale is None 的提前 return 旁路易漏)、npu_grouped_matmul_swiglu_quant 的 gmm1 输出 scale、MoE MLP quant_apply_mlp 仅 use_mxfp_quant 时归一化。非 A5 硬件与非 MXFP8 路径保持原样。衔接 MoE dispatch-combine v2 与分组 gmm 消费顺序。仓自报 Ascend950DT E2E serving 通过、无独立精度复测。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.precision
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/7573
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- '950'
- a5
---

# A5(Ascend950) MXFP8 fused-MoE：进分组 matmul 前激活量化 scale 必须打包成 [M, N//2, 2] 并中心化收口

## 适用场景

在 [ascend-950](../../../concepts/platforms/ascend_950.md)（Atlas A5，Ascend950）上做 fused-MoE 的 [mxfp8-a8w8](../../../concepts/quantization/mxfp8_a8w8.md) 量化推理（`w8a8_mxfp8`），任意一条把激活量化 scale 送进下游**分组 matmul**（`npu_grouped_matmul_swiglu_quant` / gmm）的路径，都受本规则约束。触发前提：

- 硬件是 A5(Ascend950)，量化 scheme 是 MXFP8，scale 的 dtype 为 `FLOAT8_E8M0FNU_DTYPE`（E8M0）。
- 存在一个产 scale 的算子（如 `npu_dynamic_mx_quant` / `npu_dynamic_quant`）与一个消费 scale 的 A5 分组 matmul kernel，两者的 scale 布局约定不同。

若你正在 A5 上新写或改写 MXFP8 fused-MoE 的 scale 生产 / 传递路径，进入分组 matmul 前不做布局归一化，就会 scale 布局与 A5 kernel 期望不符——这是本页要拦的坑。非 A5 硬件、非 MXFP8 路径不落入本规则（见「反例」）。

## 条件 → 优先做什么

**条件**：A5 + MXFP8 + 激活 scale 将被分组 matmul 消费，且 scale 当前是二维 `[M, N]`。

**优先做**：进分组 matmul 前，把 scale 从二维 `[M, N]` reshape 成打包三维 `[M, N//2, 2]`（相邻两个 scale 打进最后一维），并**用一个中心化的 adaptor 方法统一收口**，而不是在各分支各写一遍 reshape。判据只有一句：

> scale 二维 + 最后一维 N 为偶数 → 打包成 `[M, N//2, 2]`；N 为奇数直接报错，不静默降级。

这样做的理由：A5 MXFP8 分组 matmul kernel 期望激活 scale 为打包三维布局，而上游动态量化算子产出的是二维 `[M, N]`。两者布局不一致时 kernel 拿到的 scale 排布是错的。把归一化抽成单一入口，是因为「产 / 传 scale 的位置有多个」——只要有一处漏做，就会重现布局不一致的 bug；集中收口让「每条路径都过这层」成为结构保证，而非靠人记住每个分支。

该布局约束系于 MXFP8 dtype 与 A5 分组 matmul 算子的固有要求，不依赖某次具体实现：下一个在 A5 上新写 MXFP8 MoE scale 路径的人会撞到同一约束，属可迁移的耐久经验。

### 中心化归一化的形态

用 DeviceAdaptor 分层：基类是 no-op，A5 override 才做打包，从而做到「同一份调用代码在所有硬件上正确」：

```python
# 基类：非 A5 硬件不做任何变换
class BaseDeviceAdaptor:
    @staticmethod
    def maybe_normalize_mxfp_scale_layout(scale):
        return scale

# A5 override：仅二维 scale 生效，最后一维须偶数
class A5DeviceAdaptor(BaseDeviceAdaptor):
    @staticmethod
    def maybe_normalize_mxfp_scale_layout(scale):
        if scale is None or scale.ndim != 2:
            return scale
        if scale.shape[-1] % 2 != 0:
            raise ValueError(f"Invalid MXFP8 scale shape: {tuple(scale.shape)}")
        return scale.reshape(scale.shape[0], scale.shape[1] // 2, 2)
```

要点：`scale is None` 或非二维直接原样返回（幂等、可到处调）；奇数最后一维抛 `ValueError` 而不是静默补齐——布局约束是硬的，静默降级会把错误藏到 kernel 里更难查。

### 所有产 / 传 scale 的位置都要接入

统一收口意味着「凡是产出或转手 MXFP8 scale 的出口」都过这层，典型三类接入点：

1. **动态量化产 scale 的出口**：`npu_dynamic_quant` 返回时 `return hidden_states, maybe_normalize_mxfp_scale_layout(dynamic_scale)`。注意易漏的分支——原来 `dynamic_scale is None` 分支会提前 `return torch_npu.npu_dynamic_mx_quant(...)` 直接吐出未归一化 scale；应改为先 unpack `hidden_states, dynamic_scale = torch_npu.npu_dynamic_mx_quant(...)`，再走同一归一化出口。**提前 return 的旁路分支是最典型的漏点。**
2. **分组 matmul 自身的输出 scale**：`npu_grouped_matmul_swiglu_quant` 的 gmm1 输出 scale 也要归一化：`return out, maybe_normalize_mxfp_scale_layout(out_scale), None`。
3. **MoE MLP 前向组装 scale 的位置**：如 `quant_apply_mlp` 里 `pertoken_scale = maybe_normalize_mxfp_scale_layout(dynamic_scale) if use_mxfp_quant else dynamic_scale`——**仅 MXFP8 路径归一化，非 MXFP8 保持原样**。

这条 MoE 路径与 [moe-dispatch-combine-v2](../../../concepts/techniques/moe_dispatch_combine_v2.md) 的 dispatch/combine + 分组 gmm 消费顺序衔接，scale 归一化必须发生在 scale 抵达 gmm 之前。

## correctness 验证 / rollback

- correctness：A5 MXFP8 fused-MoE 端到端 serving 正常运行即表明 scale 布局与 kernel 对齐；scale 布局归一化为内部实现修复，无用户可见 API 变更。数值精度对比数据见 Evidence 节。
- rollback / 定位：若 A5 上 MXFP8 MoE 出现结果异常而非报错，优先排查是否有某条产 / 传 scale 的旁路（尤其提前 `return` 的 None 分支）绕过了归一化收口。奇数最后一维会以 `ValueError` 显式暴露，反而好查。

## 反例（不落入本规则）

- **非 A5 硬件**：基类 `maybe_normalize_mxfp_scale_layout` 为 no-op，非 A5 后端不做此变换；把 `[M,N//2,2]` 打包硬套到其它硬件上是错的。
- **非 MXFP8 路径**：MoE MLP 里 `use_mxfp_quant` 为假时 scale 保持原样，不归一化。
- **scale 非二维 / 为 None**：adaptor 原样返回，不强行 reshape。
- 布局要求限定在 A5(Ascend950) MXFP8 路径，不外推到其它硬件 / 其它量化。「A5 kernel 只吃打包三维布局」系从 reshape 行为反推的必要条件，故规则按「消费前需归一化成该布局」表述，不断言算子规格本身。

## Evidence

- 实现（merge commit `d452d04656eabc0bf719e1d07093973274eebd6e`，diff 事实）：`vllm_ascend/device/device_op.py` 提供 `BaseDeviceAdaptor.maybe_normalize_mxfp_scale_layout`（no-op）与 `A5DeviceAdaptor.maybe_normalize_mxfp_scale_layout`（reshape + 偶数校验）；`vllm_ascend/ops/fused_moe/moe_mlp.py::quant_apply_mlp` 仅在 MXFP8 路径归一化。归一化收口在动态量化产 scale 出口、分组 matmul gmm1 输出 scale、MoE MLP 前向组装 scale 三处调用；reshape 形状、偶数校验、no-op 基类、None 分支修复均为 diff 事实。
- 测试（仓自报）：CI + Ascend950DT E2E serving 测试通过；无独立复测的数值精度对比数据。
- 溯源下探：[vllm-ascend-pr-7573-a5-bugfix-fix-fused-moe-a5-mxfp8-scale-normalization-load-balance-routin](https://github.com/vllm-project/vllm-ascend/pull/7573)
