---
type: "Runbook"
title: "aclnn TilingData 缓存致 runtime attr 陈旧"
description: "aclnn L2 executor 对可 repeat 算子按 (算子, shape, dtype) 缓存整块 TilingData；若算子把每次调用都不同的 runtime scalar attr（如 beta/threshold）写进 TilingData，则同 (op,shape,dtype) 的第二批调用会跳过 tiling 函数、复用第一批的陈旧 attr，kernel 据此取错分支。判别=单跑通过 + 批跑失败 + 同 shape 不同 attr + tiling 函数日志两批只出现一次。"
tags: ["task.debugging", "topic.precision", "topic.tiling", "topic.implementation.operator_registration"]
status: stable
sources: []
created_at: "2026-08-17T17:21:52Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["repeat_cache"]
---

# aclnn TilingData 缓存致 runtime attr 陈旧

## 现象

在 Ascend950PR（RegBase / arch35、CANN cann-9.0.0-beta.2、build `--soc=ascend950`）上调试 `softplus_v2_grad` 算子精度。失败集中在 **scalar shape `()` 的 L1 case**：例如 L1_037（beta=-127.75, threshold=-0.0065, self∈(2,10), gradOutput∈(-1,1)）。正确结果应为 bx = beta*self = -127.75*(2..10) ∈ (-1277.5, -255.5)，全部 ≪ threshold(-0.0065) → sigmoid 分支 → grad_sig ≈ 0 → golden=0；但批跑时 actual ≈ gradOutput，即 kernel 取了**线性分支**（gradInput = gradOutput）。

关键差异：**L1_037 单跑通过；紧接 L1_001（同为 scalar shape `()`、但 beta=0.0023）后跑则失败**。把 L1_037 排在 L1_001 之后，actual 正好等于"用 beta=0.0023 算"的结果：bx = 0.0023*(2..10) ∈ (0.0046, 0.023) > threshold(-0.0065) → 线性分支 → gradInput = gradOutput。即第二批 case 复用了第一批的 beta/threshold。

## 适用场景

- **工程形态**：aclnn L2 接口 + RegBase 算子仓（op_host/op_api/op_kernel），kernel 经 aclnn executor 走。
- **API 路径**：`aclnnSoftplusV2GradGetWorkspaceSize` → `uniqueExecutor` → `ReleaseTo(executor)`；tiling 函数把 `beta`/`threshold` 写进 `TilingData`。
- **验证过的平台与 CANN 版本**：Ascend950PR（注册平台 `950`），CANN cann-9.0.0-beta.2，arch 目录 arch35，build `--soc=ascend950`。
- **适用粒度**：`operator_family`——所有把 runtime scalar attr 写进 `TilingData`、且 aclnn L2 接口对同 (op,shape,dtype) 复用 executor 的算子都会踩。
- **路线优先级**：`recommended_fastpath`（在 op_api 的 `ReleaseTo` 前调 `AbandonCache(true)` 禁用 repeat/tiling cache，是最小改动且经本 trace 实测有效；根治方向是把 attr 移出 TilingData 改走 per-call workspace）。
- **明确不适用/未验证场景**：TilingData 内本就不含 runtime attr 的算子不适用；不走 aclnn L2 executor 的 kernel 直调场景不适用；a2/a3 未验证（推断可迁移，见 `## 失效边界`）。

## 根因

aclnn L2 executor 对"可 repeat"的算子以 **(算子, shape, dtype)** 为 key 缓存整块 `TilingData`。本算子把 `beta`/`threshold` 这两个**每次调用都不同**的 runtime scalar 写进了 `TilingData`。当第二批调用 shape/dtype 与第一批相同（scalar shape `()` + 同 dtype）时，框架**跳过 tiling 函数**、直接复用第一批的 `TilingData`——里面的 beta/threshold 是第一批的陈旧值，kernel 据此取错分支。shape 越是"撞 key"（scalar、或同 shape 反复跑）越容易触发；多 case 批跑必发，单跑看不出来。

机制链：`aclnnSoftplusV2GradGetWorkspaceSize` 内 `CREATE_EXECUTOR` → L0 op 经 `ADD_TO_LAUNCHER_LIST_AICORE(... OP_ATTR(beta, threshold))` 把 attr 喂给 launcher → tiling 函数把 beta/threshold 写进 `TilingData` → `CommonOpExecutorRun` 时若 executor 可 repeat 则按 (op,shape,dtype) 复用整块 `TilingData`（含陈旧 attr）→ kernel 读到陈旧 beta/threshold。

## 判别方法

触发（tool_observed）：批跑时同 (op,shape,dtype)、不同 runtime attr 的 scalar case 取错分支——单跑该 case 通过，紧接另一个同 shape 不同 attr 的 case 后跑则失败，且 actual 数值正好等于"用前一批的 attr 算"的结果。

探针：① 对怀疑的 scalar case 单跑，记录通过/失败；② 紧接一个同 scalar shape `()` 但不同 beta/threshold 的 case 后再跑同一 case，记录 actual；③ 在 tiling 函数入口加日志探针（如 `GetShapeAttrsInfo` 调用点打印一行），跑两批同 (op,shape,dtype) 调用，数日志出现次数。

观测（tool_observed）：单跑通过 + 接同 shape 不同 attr 后跑失败，actual 对应陈旧 attr 取值；tiling 函数日志在两批同 (op,shape,dtype) 调用中只出现一次——第二批根本没进 tiling 函数，TilingData（含 beta_scalar/threshold_scalar）被框架直接复用。

解释（interpretation）：aclnn L2 executor 的 repeat/tiling cache 以 (op,shape,dtype) 为 key 缓存整块 TilingData；runtime attr 写进 TilingData 后，同 key 的第二批调用复用陈旧 attr，kernel 据陈旧 beta/threshold 取错分支。在 op_api 的 `ReleaseTo(executor)` 之前调 `uniqueExecutor->AbandonCache(true)` 禁用 repeat/tiling cache、强制 tiling 函数每次调用都执行，可消除该症状（本 trace 实测：加探针后 tiling 函数从"两批只跑一次"变为"每批都跑"，beta/threshold 不再陈旧）。

## 验证信号

- 单跑 L1_037（scalar shape `()`、beta=-127.75）通过；紧接 L1_001（同 shape、beta=0.0023）后跑则失败、actual 对应陈旧 beta=0.0023 的取值（来源平台:950；证据等级:tool_observed）
- tiling 函数 `GetShapeAttrsInfo` 日志：修复前两批同 (op,shape,dtype) 调用只出现一次、修复（AbandonCache(true)）后每批都出现（来源平台:950；证据等级:tool_observed）
- AbandonCache(true) 后 scalar shape 失败用例数大幅下降、PyTorch ST 总通过率显著上升（来源平台:950；证据等级:tool_observed）

## 失效边界

- 平台：本 trace 只在 Ascend950PR（`950`）实测。a2/a3 上同 CANN aclnn L2 executor cache 机制预期一致，但**未验证，推断可迁移**；如要落到 a2/a3 须重测。
- 算子族：本卡根因（aclnn executor 按 (op,shape,dtype) 缓存整块 TilingData）对一切"把 runtime attr 写进 TilingData 且经 aclnn L2 接口 repeat 调用"的算子都成立，不止 softplus_v2_grad。
- 边界：TilingData 内不含 runtime attr 的算子不受影响；不走 aclnn L2 executor 的 kernel 直调场景不适用。

## 坏实践

- 看到 scalar case "单跑通过"就当环境/种子问题放行——掩盖了 cache 陈旧真因。
- 把 scalar 失败归因为"极端 beta 值导致溢出"——但 beta=-127.75、self∈(2,10) 算出 bx∈(-1277.5,-255.5) 远未溢出，且单跑通过，与"溢出"假设矛盾；真因是 cache 陈旧，非数值溢出。
- 没卸载旧 vendor 包就开测——曾误判为"两个 SoftplusV2Grad vendor 冲突"，卸载旧 vendor 后结果不变，排除该干扰项后才定位到 tiling cache。

<!-- cannbot:related:start -->
## 相关

- [Attr（OpDef）](../../apis/utils_api/prototype_register_management/op_def/attr.md)（`exemplifies`）：运行卡说明每次调用变化的 Attr 若经 TilingData 传给 Kernel，会受 aclnn repeat cache 影响而变陈旧，给出属性从原型进入运行时后的缓存边界。
- [OpAttrDef](../../apis/utils_api/prototype_register_management/op_attr_def/op_attr_def.md)（`exemplifies`）：OpAttrDef 与《aclnn TilingData 缓存致 runtime attr 陈旧》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [通过TilingData传递属性信息](../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_data_attributes.md)（`related`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“aclnn TilingData 缓存致 runtime attr 陈旧”明确aclnn L2 executor 对可 repeat 算子按 (算子, shape, dtype) 缓存整块 TilingData；若算子把每次调用都不同的 runtime scalar attr（如 beta/threshold）写进 TilingData，则同 (op,shape,dtype) 的第二批调用会跳过 t…。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [ACLNN L2 缓存键漏 scalar 致批跑误命中](../compilation/aclnn_l2_cache_key_missing_scalar_partial_mismatch.md)（`same_topic`）：两张卡都定位到同 shape/dtype、不同 runtime scalar 时 ACLNN repeat cache 复用陈旧 TilingData；该卡进一步用 tiling 函数日志和 AbandonCache(true) 闭环验证。
- [TilingKey 缓存 correction 致 tilingdata 复用](../compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`same_topic`）：TilingKey 缓存 correction 致 tilingdata 复用 与《aclnn TilingData 缓存致 runtime attr 陈旧》的实质衔接是：该问题由 GE 按 TilingKey 缓存 correction 造成同 shape 调用复用旧 TilingData；属性传递指南和注册/判定宏共同说明如何让变化属性进入正确 tiling 分派。
- [标量属性入 TilingData 致同 shape 跨调用陈旧](tilingdata_shape.md)（`same_topic`）：两卡都以同 shape 不同 runtime scalar 连跑复现 TilingData 陈旧；一张是 softplus ACLNN 实例，一张提炼 shape-only 缓存根因。
<!-- cannbot:related:end -->
