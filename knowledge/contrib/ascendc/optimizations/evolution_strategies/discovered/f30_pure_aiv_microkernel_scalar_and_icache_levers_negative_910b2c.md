---
type: Optimization
title: "F30: 纯 AIV 微内核上「标量地址链 / 代码体积 / 运行时 mask / 少开 block」四类看似合理的杠杆实测无效或负向"
description: "纯 AIV 微内核上「标量地址链 / 代码体积 / 运行时 mask / 少开 block」四类看似合理的杠杆，在同窗口 A/B 下实测无效或负向。"
tags:
  - task.debugging
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
  - topic.tiling
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/vector_compute/low_latency_instruction.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/general_description_and_constraints.md
    role: constraint
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f30_pure_aiv_microkernel_scalar_and_icache_levers_negative_910b2c.json
    role: evidence
created_at: "2026-11-06T00:00:00Z"
updated_at: "2026-11-06T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 pure-aiv-microkernel-scalar-and-icache-levers-negative-910b2c）。
>
> 原始元数据：
>
> ```yaml
> confidence: single_op
> phenomenon: perf_regression
> severity: medium
> occurrences: 1
> failed_combination: [P94, P97, P54]
> op_families: [matmul, quantization, elementwise, cv-mix]
> operator_type: [matmul, quantization]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/f30_pure_aiv_microkernel_scalar_and_icache_levers_negative_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f30_pure_aiv_microkernel_scalar_and_icache_levers_negative_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F30: 纯 AIV 微内核上「标量地址链 / 代码体积 / 运行时 mask / 少开 block」四类看似合理的杠杆实测无效或负向

## 现象（本例算子 本轮，Ascend910B2C / CANN 8.5.1，纯 AIV direct-launch，内核 5.9-7.3us）

## 根因

纯 AIV 微内核（每核 600 余条向量指令、每 case 2-17M MAC）的成本是**每核向量指令条数 × 发射延迟（32-76 cycle，前面挂暴露 UB 标量读时取上界）**，
不是标量地址算术、不是代码体积、也不是 block 数（block 启动按波摊薄）。任何把「独立标量计算」改成「循环携带依赖」的
"优化"，都会直接吃掉标量单元与向量单元的并行发射窗口。

## Resolution

- 微内核调优先做**每核向量指令条数**的账，而不是地址算术/代码体积的账
- 保留循环内**编译期常量 mask**；不要在热循环里引入运行时 mask 或循环携带指针
- 并行度纪律：**最大化并行、最小化每核行数**；不要为了「复用 dequant」把多个 m 行合并到少数 block
- 落盘：亚 32B 行间隙只能用逐行 `DataCopyPad`；单次 2D 形式仅当行字节是 32B 整数倍

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f30_pure_aiv_microkernel_scalar_and_icache_levers_negative_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

