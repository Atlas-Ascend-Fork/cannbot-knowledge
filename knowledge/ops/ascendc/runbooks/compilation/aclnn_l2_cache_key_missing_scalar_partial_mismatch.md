---
type: "Runbook"
title: "ACLNN L2 缓存键漏 scalar 致批跑误命中"
description: "DFX_IN 遗漏影响 TilingData 的 scalar 属性时，ACLNN L2 cache key 不含该属性，同 shape 不同属性值的调用复用旧 TilingData，出现\"单跑 PASS、批跑 FAIL\"的精度漂移。"
tags: ["task.debugging", "topic.precision", "topic.implementation"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# ACLNN L2 缓存键漏 scalar 致批跑误命中

## 现象

在调试 `softplus_v2_grad` 算子（arch35/DAV_3510，Ascend950PR）的 PyTorch ST 时，C++ ST 57/57 全过，但 PyTorch ST 仅 463/578 通过、115 失败。失败用例呈现一个明显模式：**同一用例单独跑通过、放进批量用例集里跑失败**，且失败数随用例顺序波动。设置环境变量 `DISABLE_L2_CACHE=1` 重跑，失败数从 115 降到 78，证明部分失败由 L2 缓存误命中导致。

检查 `op_api/aclnnSoftplusV2Grad.cpp` 第 123 行：

```cpp
L2_DFX_PHASE_1(aclnnSoftplusV2Grad, DFX_IN(gradOutput, self), DFX_OUT(gradInput));
```

`DFX_IN` 只列了 `gradOutput`、`self` 两个 tensor，**漏掉了 `beta`、`threshold` 两个 scalar 属性**。而算子的 `OP_ATTR(...)` 里 `beta`、`threshold` 作为 scalar 传入，并参与 TilingData 计算。

## 适用场景

- **工程形态**：aclnn 算子仓开发（ops-registry-invoke），op_api L2 接口实现层。
- **API 路径**：`L2_DFX_PHASE_1` / `DFX_IN(...)` / `DFX_OUT(...)` 宏，以及 `OP_ATTR(...)` scalar 注册。
- **验证平台与版本**：Ascend950PR（soc=ascend950，arch35/DAV_3510），CANN 9.0.0-beta.2。
- **适用粒度**：`operator_family`（所有通过 `OP_ATTR` 传 scalar 属性并影响 TilingData 的 aclnn L2 算子）。
- **路线优先级**：`recommended_fastpath`（补全 `DFX_IN` 保留缓存性能收益，优于直接关缓存）。
- **不适用或未验证场景**：无 scalar 属性的纯 tensor 算子（`DFX_IN` 只需列 tensor 时无此问题）；非 L2 aclnn 框架（如 kernel 直调）不经过此缓存。

## 根因

ACLNN L2 的 cache key = hash(**API 名 + op config + `DFX_IN(...)` 参数 + `DFX_OUT(...)` 参数**）。命中时直接返回已缓存的 `aclOpExecutor`（含已计算的 TilingData），**跳过 Tiling 函数**。**若 `DFX_IN` 遗漏了某个影响 TilingData 的 scalar（如 `beta`/`threshold`），该 scalar 不参与 cache key hash**：同 shape 不同属性值的调用命中同一缓存项、复用旧 TilingData，拿旧属性参与计算 → 结果错误。机制链：`OP_ATTR` 的 scalar 进入 TilingData → `DFX_IN` 漏 scalar → cache key 不含 scalar → 同 shape 异属性命中同缓存 → 复用旧 TilingData（旧 beta/threshold）→ 批跑时后序用例拿到前序用例的属性 → 精度漂移；单跑时缓存未污染故通过。

## 解决配方

**before**（`op_api/aclnnSoftplusV2Grad.cpp:123`，DFX_IN 漏 scalar）：

```cpp
L2_DFX_PHASE_1(aclnnSoftplusV2Grad, DFX_IN(gradOutput, self), DFX_OUT(gradInput));
```

**after**（DFX_IN 补全所有影响 TilingData 的输入：tensor + scalar）：

```cpp
L2_DFX_PHASE_1(aclnnSoftplusV2Grad, DFX_IN(gradOutput, self, beta, threshold), DFX_OUT(gradInput));
```

硬性约束：`OP_ATTR(...)` 中的每个 scalar 必须同时在 L2 的 `DFX_IN(...)` 中出现；`DFX_IN` 应覆盖输入 tensor + scalar + 普通 C++ 类型参数的全部输入。

## 验证信号

- 初始 PyTorch ST 463/578 通过、115 失败（来源平台：950；证据等级：tool_observed）。
- `DISABLE_L2_CACHE=1` 后失败数 115→78（来源平台：950；证据等级：tool_observed）。
- `DFX_IN` 补全 `beta, threshold` 后重建重测：499/578 通过（463→499，+36），残留 79 失败为另一独立 kernel bug（来源平台：950；证据等级：tool_observed）。

## 预防

- 同类排查：凡 `OP_ATTR` 传 scalar 的 L2 接口，批量审查 `DFX_IN` 完整性——`DFX_IN` 列表必须与 `OP_ATTR` 的 scalar 一一对应。
- 调试单跑 PASS/批跑 FAIL 的精度漂移时，先用 `DISABLE_L2_CACHE=1` 快速确认是否缓存相关，再查 `DFX_IN` 完整性（这是 quick-confirm 手段，不是最终修复；最终修复仍是补全 `DFX_IN`）。

## 坏实践

- 用 `DISABLE_L2_CACHE=1` 作为"修复"部署到生产——这放弃了 L2 缓存的性能收益，且本例 `DISABLE_L2_CACHE` 在该运行时未必完全生效（78 失败仍存在说明还有独立 kernel bug）。正确做法是补全 `DFX_IN`。

## 失效边界

- Ascend950PR/arch35 实测；其他平台（a2/a3）走相同 ACLNN L2 框架，机制一致但未验证，推断可迁移。
- `DFX_IN` 完整性规则对所有走 L2_DFX_PHASE 的 aclnn 算子通用；非 aclnn 框架（kernel 直调）不经过此缓存。