---
type: Optimization
title: "已验证方案：FA 反向的 CV ring 流水 + BLOCK_N 大块化"
description: "FA 反向的 CV ring 流水 + BLOCK_N 大块化：把 AIC 与 AIV 的严格锁步三段改成多槽 ring 与预发射，让 cube 与 vector 重叠，并减少跨核握手。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/flash_attention_tuning.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/CrossCoreSetFlag_ISASI.md
    role: constraint
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/fa_bwd_cv_ring_pipeline_blockn128.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 fa-bwd-cv-ring-pipeline-blockn128）。
>
> 原始元数据：
>
> ```yaml
> id: fa-bwd-cv-ring-pipeline-blockn128
> op_families: [attention]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/fa_bwd_cv_ring_pipeline_blockn128.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/fa_bwd_cv_ring_pipeline_blockn128.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# 已验证方案：FA 反向的 CV ring 流水 + BLOCK_N 大块化
## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 问题现象
反向 attention 的基线实现把每个 kv 块写成严格锁步的三段：
`AIC(S=Q@K^T, dP=dO@V^T) → 跨核握手 → AIV(P=exp(S-lse), dS=P*(dP-D)) → 跨核握手 → AIC(dQ+=dS@K, dK+=dS^T@Q, dV+=P^T@dO)`。
每块 2 次跨核握手、Cube 与 Vector 零重叠，BLOCK_M=BLOCK_N=64 使每块实际计算量很小，时间主要花在握手、GM 往返与原子写上。

## 方案（两项正交改动，缺一不可）
1. **CV ring 流水（P121+P14）**：workspace 开 `RING_SLOTS=3` 份 S/dP/P/dS，每 slot 独立 flag id；
 AIV 同轮消费同槽并写回同槽。**槽号用跨 task 连续的全局 seq（task 边界不排空）**，这样每个 flag id 上
 set/wait 严格交替、同时最多 1 个未消费事件，不依赖 flag 计数语义（F10/F11 的坑由此规避）。
2. **BLOCK_N 64→128（P122/P17）**：每块工作量翻倍 → 握手次数、MMA 发射组数、A 侧 operand 重搬、
 AIV 逐行标量壳、dQ 原子写 tile 数全部减半；再配 per-matmul 的 L1/L0C 预算（各 168KB/32KB，总 ≤504/96KB）
 —— 基线给三个 MatmulImpl 各分配满额 512KB/128KB（共享一个 TPipe 时是 3 倍 over-commit，tile 放大后直接崩）。
 ⚠ 放大 BLOCK_N 后 `transA` 的 mm4/mm5 必须把 `SetOrgShape` 的 A 侧行距从 BLOCK_M 改成 BLOCK_N
 （两者相等时才是巧合等价，改一个就静默算错）。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/fa_bwd_cv_ring_pipeline_blockn128.json`；引用时请结合上文适用条件与失效边界判断适用范围。

## 流水化之后的瓶颈迁移（给下一轮用）
`aic_fixpipe_ratio 0.895`（最高单项）、`aic_mac 0.248`、`aic_scalar 0.929`（主要是 CrossCoreWaitFlag 自旋计费）、
`aiv_mte2 0.127`。即：CV 解耦后主瓶颈变成 **dQ/dK/dV 的 fp32 atomic RMW 写带宽**（约 192KB/unit 往返），
下一杠杆是把 dQ 的跨 kv 累加搬进 L0C、task 末一次固定写（原子次数 nkv→1，P91/X103 思路）；
AIV 侧双缓冲（P1）在此 profile 下无用（aiv_mte2 仅 0.127）。

## ⚠ 同批变体踩出的反向坑（本例算子 其它车道实证）
- **不要删 `mmX.End()`**：每 gemm 后一次 `End()` 看似冗余，删掉后 dV 出现**非确定性**错误
 （L1/L0 buffer 与 TBufPool 未复位就连续 IterateAll 会串 buffer）。
- **改了 matmul 的 K 维必须用真实 K 重跑 `GetTiling`**：例如把 mm3 的 K 从 BLOCK_N 换成真实 sk 时，
 仍用 K=BLOCK_N 求 tiling 会让 tiling 选出「K 全载 L1」形态、运行期却跑分块 K 循环 → `MPU address access invalid` (507015)。
 参考时间是否同口径，或改用「同 session 兄弟互比 + 纯 kernel 绝对时间」。
- 若要继续压大 case：把 dS 存成每 task 的整行块（支持 task 末一次 K=sk 的 GEMM 直接产出 dQ，

## 适用条件
- MIX_AIC_1_2 的 CV 分离 attention 反向（或任何"cube 产出中间矩阵 → vector 逐元素 → cube 再消费"的多相位结构）；
- 不适用：已经是 online-softmax 单 kernel、无跨核 GM 交接的前向实现。

## 复现要点
- 编译：MIX kernel 必须 `bisheng -xasc` 单 TU + `<<<>>>` 直发（本仓 `RegisterAscendBinary` 路径不支持 MIX，ret 107000）；
- 产物需同时打包成 `<dir>/flex_attention_bwd/_kernel.so` 与 `<dir>/kernel/build/flex_attention_bwd/_kernel.so`
 （ops-profiling wrapper 与 verification_ascendc.py 的 sys.path 起点不同）；
- 精度：`atol+rtol*|golden|` 的 matched_ratio 判定；dQ 逐元素相对误差会被近零 golden 放大，不可用作判据。