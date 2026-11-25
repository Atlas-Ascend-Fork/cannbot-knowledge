---
type: Optimization
title: "F20: 失败模式：融合形态四条死路 + 两条工程陷阱"
description: "融合形态的四类死路与两条工程陷阱：单 kernel 内多 TPipe/TBuf、跨相位单 launch、删除流同步、手工 SetFlag/WaitFlag ping-pong 都会导致精度失败或 hang；融合应使用单 TPipe + TQue。"
tags:
  - task.debugging
  - topic.compute.neighborhood.convolution
  - topic.attention
  - topic.programming_model.execution_unit.vector
  - topic.memory
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/TPipe.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/avoid_tpipe_init_in_object.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f20_multi_tpipe_fusion_and_stale_cmake_910b2c.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 F20-multi-tpipe-fusion-and-stale-cmake-910b2c）。
>
> 原始元数据：
>
> ```yaml
> id: F20-multi-tpipe-fusion-and-stale-cmake-910b2c
> op_families: [attention, convolution, reduction, cv-mix]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/f20_multi_tpipe_fusion_and_stale_cmake_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f20_multi_tpipe_fusion_and_stale_cmake_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# 失败模式：融合形态四条死路 + 两条工程陷阱
## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 现象与边界（每条都在全量 50 case 上复现）

## 另有一条"反向"教训（不是失败，但同源）
`KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIV_ONLY)` 在 CANN 8.5.1 是空宏，MIX_AIC/AI_VECTOR_CORE 由编译器推断；
不要以为它能把 templated 入口强制成 AIV。

## Resolution
1. 需要减少 kernel 数时：合并**同相位**分支（例：conv 三分支→1、attn 三分支→1），保持一个 TPipe + 共享 buffer，
 每条分支顺序跑自己的 task 循环；不要跨相位（写后读）合并。
2. 需要流水时：一律用 TQue，禁止裸 event 对轰。
3. 不要动 `npuSynchronizeDevice`。
4. 并行变体目录：`rm -rf kernel/build` 后重新 cmake（`ASCEND_CANN_PACKAGE_PATH` 指当前 CANN），
 交付前 md5 校验两个 .so，评测前打印 `triplet_attention.__file__` 确认加载路径。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f20_multi_tpipe_fusion_and_stale_cmake_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

