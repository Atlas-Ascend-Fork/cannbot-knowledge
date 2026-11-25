---
type: Optimization
title: "F28: `Pattern::Reduce::RA` 的 workspace ≈2B/元素会撑爆 UB，且 row-stride ≠ padLast 时静默算错"
description: "Pattern::Reduce::RA 的 workspace 约 2B/元素，大 shape 会撑爆 UB；且 ReduceSum 按 padLast 推导行距，实际行距不一致时不报错但结果错。"
tags:
  - task.debugging
  - topic.attention
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceSum_interface/GetReduceSumMaxMinTmpSize.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceSum_interface/ReduceSum.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f28_reduce_ra_workspace_and_stride_910b2c.json
    role: evidence
created_at: "2026-10-29T00:00:00Z"
updated_at: "2026-10-29T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 reduce-ra-workspace-and-stride）。
>
> 原始元数据：
>
> ```yaml
> confidence: single_op
> phenomenon: strategy_infeasible
> severity: medium
> occurrences: 1
> failed_combination: [P94, P110]
> op_families: [reduction, elementwise, attention]
> operator_type: [reduction]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/f28_reduce_ra_workspace_and_stride_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f28_reduce_ra_workspace_and_stride_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F28: `Pattern::Reduce::RA` 的 workspace ≈2B/元素会撑爆 UB，且 row-stride ≠ padLast 时静默算错

## 现象

在一段「沿归约轴（通道轴）做加权求和」的内层，把原来的
`cb 次 Axpy + 每轮 8 次 UB→标量 GetValue`（或 `ReduceSum<AR>` 逐行）
改成「整 tile × 权重列广播 Mul + 一次 `ReduceSum<float, Pattern::Reduce::RA>`」时：

1. **workspace 爆 UB**：`RA` 的临时区约 **2B/元素**。shape `(64, 2048)` 即 256KB > UB 192KB，
 直接编译期/运行期失败；而同一份 kernel 若同时还要放 fp32 工作 tile、双缓冲输入、常驻权重，必然装不下。
2. **结果不符（更危险）**：当 UB 侧每行的实际 stride 与 API 内部推导的
 `padLast = AlignUp(cols, 32/sizeof(reduce_dtype))` 不一致时，**不报错但结果错**
 （实测会出现明显数值偏差）。典型成因：fp16/bf16 源 tile 的行距按 32B 取整为
 `AlignUp(len, 16)` 个元素；Cast 成 fp32 后若沿用该行距（`len=325` 时为 336 floats），
 而 fp32 `ReduceSum` 按 `cols=325` 推导 `padLast = AlignUp(325, 8) = 328` floats，二者不等，
 API 从第二行起按 328 定位就会错读。

## 根因

`ReduceSum<Pattern::Reduce::AR/RA>` 要求「参与归约的张量各行首地址落在固定的 32B 对齐行距上」，
API 用 `padLast` 推导该行距而不校验调用方传入的 stride；一旦调用方另有更宽的行距（例如为整 tile Cast 统一了行距），
归约就会跨行取错元素。`RA` 还额外需要与元素数成正比的 workspace。

## Resolution

- **让实际行距等于 API 推导的 `padLast`**：reduce dtype 为 fp32 时，行距必须是
 `AlignUp(cols, 8)` 个 float。若源 tile 是 fp16/bf16，Cast 后不能沿用源行距，必须把每个 UB 行
 重新排成 `AlignUp(len, 8)` 个 fp32；否则只能选择一个 `cols'`，使 `AlignUp(cols', 8)` 恰好等于实际行距，
 并保证多出的 padding 元素为 0 或不在归约范围内。
 **仅把 `cols` 改成 `len` 而保留源 dtype 的行距不能修复跨行错读**（`len=325`：half 行距 336、
- **AR 路径的 padding 约束**：额外参与归约的 padding 元素必须为 0（或调整归约范围），否则会改变行和。
- **UB 吃紧时不要用 RA**：改用「一次 2-D DMA + 向量 Add 链」做沿行累积，
 或退回 `ReduceSum<AR>`（每 tile 出 `rows` 个行和，workspace 与 `rows` 成正比而非元素数）。
- 验收必须包含：① `(64,2048)` 这类最大 shape 的 workspace 实算；② 一个非对齐 `len`（如 325）的 case，

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f28_reduce_ra_workspace_and_stride_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

