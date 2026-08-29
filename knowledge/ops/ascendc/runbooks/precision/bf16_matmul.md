---
type: "Runbook"
title: "bf16 多 matmul 链累积漂移判别"
description: "direct-launch 融合算子 plugin 用 torch::matmul/torch::einsum 直接消费 bf16 输入时，每个 matmul 边界把中间结果量化回 bf16（尾数 8 位、ULP≈3.9e-3），误差沿多步 matmul 链累积放大，最终 query 输出 max_diff=0.125、allclose(1e-2)=False。判别=逐步探针把全链拆成 Step1..Step4 逐段对比 NPU vs CPU fp32 golden，定位累积起点在 matmul 边界量化而非单步 einsum。"
tags: ["task.debugging", "topic.precision", "topic.compute.elementwise.type_conversion"]
status: draft
sources: []
created_at: "2026-08-18T07:55:31Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: []
---

# bf16 多 matmul 链累积漂移判别

## 现象

在为一个含 4 次 CUBE MatMul + 2 次 RMSNorm + 2 次 RoPE 的 Multi-Head Latent Attention 前处理融合算子（FusedComposite，direct-launch op 结构：`op_kernel` + `op_plugin` + `cann_bench/__init__.py`）编写 `op_plugin/<op>_plugin.cpp` 的 NPU 实现时，plugin 用 `torch::matmul` / `torch::einsum` 直接消费 bf16 输入，VEC 算子（RMSNorm/RoPE）的 helper 虽然内部 `x.to(torch::kFloat32)` 再 `.to(bf16)`，但每个 matmul 边界仍产出 bf16 张量。用 cann-bench 的 golden（CPU fp32 全链路）做单 case 对比时，`query` 不达标、其余三输出在 bf16 容差内：

```
query: max_diff=0.125000, mean_diff=0.010265, max_rel=282.574127, allclose(rtol=1e-2,atol=1e-2)=False
query_rope: max_diff=0.015625, ..., allclose=True
c_kv: max_diff=0.015625, ..., allclose=True
k_rope: max_diff=0.003906, ..., allclose=True
```

当时代码处于"bf16 输入直送 matmul、helper 内部 fp32 再回 bf16"的状态。

## 适用场景

- **工程形态**：direct-launch op（FusedComposite）的 `op_plugin/*.cpp` torch 绑定实现（g++ 编译层），算子主体是多步 `torch::matmul`/`torch::einsum` + VEC 归一化/位置编码的复合计算，非单一自定义 Ascend C kernel。
- **API 路径**：`torch::matmul` / `torch::einsum` / `torch::bmm`（派发到 NPU CUBE），RMSNorm/RoPE 用 `torch` eager 算子组合；算子经 `TORCH_LIBRARY_FRAGMENT` + `TORCH_LIBRARY_IMPL(..., PrivateUse1, ...)` 注册。
- **验证过的平台与 CANN 版本**：ASCEND910B / NpuArch `DAV_2201`，CANN 9.0.0，bisheng（`--npu-arch=dav-2201`），torch 2.10.0 + torch_npu。`platforms` 为空表：trace 仅给出 `ASCEND910B`/`DAV_2201`，无 `npu-smi` 精确型号，不足以区分 A2（910B1~B4）与 A3（910_93），按规范不写入注册平台。
- **适用粒度**：`operator_family`（任何"多步 matmul 链 + bf16 入出"的融合算子 plugin 都适用，不限本算子）。
- **路线优先级**：`diagnostic_only`——本卡只给判别方法与根因解释；fp32 端到端修复的逐字 after 代码与修后闭环信号未从 trace 恢复。
- **不适用或未验证场景**：单一 matmul 且 golden 也是 bf16 的算子（无累积）；输入本身就是 fp32 的算子（`is_low_prec` 分支不触发）；真 Ascend C kernel 内部实现（kernel 内搬运/cast 另有 `DataCopyPad`+`Cast` 路径，不在此卡范围）；A2/A3 的具体区分未验证（见 `## 失效边界`）。

## 判别方法

**触发条件**（tool_observed 失败症状）：direct-launch 融合算子 plugin 直接以 bf16 输入送 `torch::matmul`/`torch::einsum`，与 CPU fp32 全链 golden 单 case 对比时，长链路输出（本例 `query`，链路含 ≥2 次 matmul + reduce）`max_diff=0.125000`、`allclose(rtol=1e-2,atol=1e-2)=False`，而链路更短或 reduce 维更小的输出（`query_rope`/`c_kv`/`k_rope`）仍在容差内 allclose=True。

**可执行探针**（逐步探针，把全链拆段对比 NPU vs CPU fp32 golden）：
1. 在 plugin 里为全链每一步中间张量加 `.cpu().float()` dump 钩子，CPU 侧用同样输入跑 fp32 golden 链路并 dump 对应中间张量。
2. 逐段计算 `max_diff = (npu_step.cpu().float() - cpu_step).abs().max()`，记录 Step1..StepN 每段的 max_diff。
3. 把怀疑的单步算子（如 `einsum`）单独抽出来在 NPU vs CPU golden 上对比一次，隔离"单步自身误差"与"链路累积误差"。
4. 若单步误差很小（如 einsum 0.000977）而全链 max_diff 沿链单调放大（Step1 0.015625 → Step3 0.0625 → 最终 0.125），即可定位累积发生在多步 matmul 边界的中间量化、而非单步算子自身。

**原始观测**（ASCEND910B/DAV_2201，mla_prolog 单 case B1S1，bf16 直送链）：
- 修复前全链：`query max_diff=0.125000, allclose(rtol=1e-2,atol=1e-2)=False`；`query_rope`/`c_kv` max_diff=0.015625、`k_rope` 0.003906，均 allclose=True。
- 逐步探针 max_diff 沿链放大：Step1 `token_x@W_DQ` = 0.015625（≈4×bf16-ULP）→ Step2 RMSNorm = 0.001953 → Step3 `c_q@W_UQ_QR` = 0.0625（≈16×ULP）→ Step4 `einsum` = 0.0625 → 最终 `query` = 0.125。
- 单步隔离：单独 `einsum`（per-head batched matmul）NPU vs CPU fp32 golden max_diff=0.000977——单步 matmul 自身误差很小。

**机制解释**（根因分析，属 interpretation）：bf16 输入直送 `torch::matmul` 时，NPU CUBE 以 bf16×bf16→bf16 产出中间张量；VEC helper 虽在算子内部 cast 到 fp32 再回 bf16，但**每个 matmul 边界**仍把中间结果量化回 bf16（bf16 尾数 8 位，ULP≈3.9e-3）。多步链路里这种"算一下、量化一次"的往返使误差沿链累积。机制链不跳步：Step1 的 bf16 matmul 输出被量化到 bf16（≈0.015625 ≈ 4×ULP）→ RMSNorm 在 fp32 内做但输入已是量化后的 bf16、输出又回 bf16（0.001953）→ Step3 matmul 再次以 bf16 输入/输出，把已漂移的 c_q 再乘一次大权重矩阵、量化一次（0.0625 ≈ 16×ULP，漂移被放大）→ Step4 einsum 对 D=128 维做 reduce，把 0.0625 的逐元素偏差累加 → 最终 query 0.125。golden 在 CPU 上全程 fp32、无中间量化，故 query 偏 0.125。`query_rope/c_kv/k_rope` 因链路更短或 reduce 维更小，漂移仍在 1e-2 容差内。单步 einsum 0.000977 远小于全链 0.125，证明累积发生在多步 matmul 链的边界量化、而非单步算子自身精度。

## 失效边界

- 本判别只覆盖"bf16 链累积漂移"这一根因；近零/相消场景的相对误差爆表（MARE 爆而 MERE 极小）非计算路径可修复，本卡不覆盖。
- 平台：trace 仅 `ASCEND910B`/`DAV_2201`，A2 与 A3 未区分；本判别在共享 DAV_2201 微架构的 A2/A3 上**未验证，推断可迁移**（微架构一致），但不得据写入 `platforms`；其他 NpuArch（如 DAV_3510/950、DAV_3002）未验证。
- `torch::matmul` 在 NPU 上的内部精度路径（是否真的 fp32 Cube 还是 fp32 经 SIMT/Vector）本 trace 未指令级验证，仅由"逐步探针的累积模式"间接支持。

## 预防

- 写多步 matmul 融合算子 plugin 时，先确认 golden 的计算精度路径；golden 若全程 fp32，bf16 输入须入口 cast fp32、全链 fp32、末尾回 cast，不要依赖"helper 内部 fp32"——matmul 边界的 bf16 量化才是漂移主源。
- 排查精度时用逐步探针（把全链拆成 Step1..StepN 逐段对比 NPU vs CPU golden）定位累积起点，不要只看最终 max_diff；同时单独隔离可疑单步算子以区分"单步自身误差"与"链路累积误差"。

## 坏实践

- 只改 VEC helper 为 fp32、matmul 仍吃 bf16：逐步探针证明无效，误差主源在 matmul 边界量化而非 helper 内部往返。
- "放宽容差到 5e-2 让 query 过"：属投机取巧捷径，未采用；评测口径是 1e-2，按 1e-2 判定。

## 验证信号

- 修复前单 case：`query max_diff=0.125000, allclose(rtol=1e-2,atol=1e-2)=False`，其余三输出 allclose=True（来源平台:ASCEND910B/DAV_2201，未定位 a2/a3；证据等级:tool_observed）
- 逐步探针：Step1 `token_x@W_DQ` max_diff=0.015625、Step2 RMSNorm 0.001953、Step3 `c_q@W_UQ_QR` 0.0625、Step4 `einsum` 0.0625；单独 einsum NPU vs CPU golden 仅 0.000977——证明累积发生在多步 matmul 链而非单步 einsum（来源平台:ASCEND910B/DAV_2201，未定位 a2/a3；证据等级:tool_observed）
