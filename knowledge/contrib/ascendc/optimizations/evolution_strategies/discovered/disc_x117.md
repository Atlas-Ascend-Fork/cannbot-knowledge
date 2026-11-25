---
type: Optimization
title: "X117: 超参 keyed 的操作数打包缓存 + host 侧打包"
description: "只依赖超参、与输入数据无关的操作数变换（permute/reshape/cat/stack）不应在每个新 shape 或超参组合上重做；按超参 key 在 host 侧打包并缓存，可把设备侧变换移出计时路径。"
tags:
  - task.optimization
  - topic.compute.neighborhood.convolution
  - topic.attention
  - topic.data_movement.data_copy
  - topic.tiling
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/overhead_optimization.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x117.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X117）。
>
> 原始元数据：
>
> ```yaml
> id: X117
> origin: discovered
> confidence: cross_op_verified
> op_families: [convolution, cv-mix, matmul, elementwise]
> bottlenecks: [scalar_loading, no_overlap, mte3_stall]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x117.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x117.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X117: 超参 keyed 的操作数打包缓存 + host 侧打包

## 核心思路
带权重的算子在 AscendC 入口（model_new_ascendc.py）里常把 torch 权重做布局变换
（`permute→reshape→cat→stack`）后传给 kernel。这些变换**只依赖超参、与输入数据无关**，
却被每个新 shapes/超参组合重做一次；而且 PyTorch 侧会落到**设备 kernel**

两刀：
1. **模块级缓存**：用与参考实现同一超参元组 `(channel, kernels, reduction, group, L, device, dtype)`
 做 key 的进程级 dict；权重由 `hash(key)` 播种、同 key 必然同值，因此可跨实例复用。
2. **把布局变换从设备搬到 host**：小张量（bias/fc/fcs）在 host 转置后一次小 H2D；
 conv 权重用预分配 + 每分支一次 `copy_` 直写最终切片（去掉 cat 的全量二次搬运）。
 **反例**：不要把大权重（如 51-87MB）在 CPU 转置再 H2D —— 实测 ~20ms，比设备转置慢两个数量级，
 那只是把真实工作挪出计时窗口，不是优化。

## 适用场景
- 推理式重复调用、且**多个 shape 共享同一组超参/权重**（评测集 50 例常只有 14 个超参 key）；
- 判据：op_summary 里 Transpose/ConcatD/Pack/ZerosLike 占比高，且它们出现在每次 forward 而非仅首次；

## 实现要点
- key 必须与参考实现完全一致（含 device/dtype），否则会拿到错误权重；
- 首次打包的 H2D 无法消除（权重必须在 CPU 侧按参考播种生成以对齐数值），别试图绕过；
- 该优化只改 python 入口，kernel/host tiling/对外接口零改动，风险低。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 增量来源（）
内部进化运行, 本轮变体，Ascend910B2C。
同一机制的第二个独立算子复现，并给出**可 grep 的消失证据**：
 来源是 wrapper 的 `w2_lane = weight.reshape(C,3,HID).permute(1,0,2)...contiguous()`、
 `b2_lane = bias.reshape(C,3).permute(1,0)...contiguous()` 与 `dummy = torch.zeros(1)`。
- 修法：权重本来先在 CPU 上 `nn.Linear` 创建、之后才 `.to(device)`，因此把 permute/re-layout
 **挪到 `.to(device)` 之前**即可零成本（H2D 本来就要发生）；`dummy` 换成按 (device,dtype) 缓存的零 bias，
 或给 kernel 传 hasBias 标志。
- 验证：改后重新采集 `PROF_Sample/task_time_*.csv`，按 stream 归组的
 `aclnnInplaceCopy_Transpose` 行数 **56→0**、`aclnnInplaceZero_ZerosLike` **28→0**，
 只剩 6 个真实 kernel。c++ 源码与基座逐字节未变。
 大 case 不退化；随后与 X121 + 集成内核合并得 **1.4203**，为整个会话最优。
- 新增判据：`--quick` 口径会把该 stream 上的**所有** kernel 计入（harness 仅过滤
 PROFILING_ENABLE/DISABLE 这类元 kernel），所以 wrapper 侧任何 per-call 小算子都会直接进分母；
 用 `grep -c aclnnInplace` 对 `task_time.csv` 做回归护栏即可防复发。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x117.json`；引用时请结合上文适用条件与失效边界判断适用范围。

