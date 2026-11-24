---
type: Optimization
title: 标量 kernel 参数直传：消除 tiling 的 GM 中转与同步 H2D 拷贝
description: 将 host 打包并经 GM 传入 tiling，改为在 kernel 签名中直接传递标量参数。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-scalar-kernel-arg-direct-pass-eliminate-tiling-h2d.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：标量 kernel 参数直传：消除 tiling 的 GM 中转与同步 H2D 拷贝

> 单一优化点：直调（AscendC tikcpp `<<<>>>`）算子若 tiling 内容全部是 host 已知标量（shape/属性推导量），把「host 打包 tiling struct → torch::empty 两个临时张量 → `copy_(non_blocking=false)` 同步 H2D → kernel 逐字节读 GM」整条链，改为**标量 kernel 参数直传**（kernel 签名追加标量参数，launch args struct 自动携带）。

## 1. 原理

- tiling 走 GM 的通用框架路径每次调用付出：2 次 `torch::empty`（完整 dispatcher 分配）+ 1 次**同步 H2D 拷贝**（隐式等 stream 排空）+ kernel 内逐字节 GM 读取循环 + 2 次 tensor 释放（NPU allocator 慢路径）。
- host 主导场景（kernel 设备时长 ≪ 每调用 wall），这些是数量级最大的单项：实测 tiling 链占每调用 ~90us（copy_ 55.5us + empty×2 25us + 对应 Free），而 kernel 仅 2.71us。
- tikcpp 的 kernel 签名支持标量参数：auto_gen 会把标量直接打进 `aclrtlaunch_*` 的 args struct（`void* y; uint64_t a; uint32_t b; void* overflow;`），host 零额外成本传值，kernel 零 GM 读。

## 2. 性能问题模式

- 触发代码形态：pybind/op host 侧存在「为传 tiling 而 `torch::empty` CPU+NPU 两个小张量 + `memcpy` + `copy_(non_blocking=false)`」；kernel Init 存在逐字节 GM→本地 struct 拷贝循环。
- 同族形态：host 把 tiling 参数/标量系数先上传 GM（**控制 blob / DeviceControlCache / workspace 头**）再由 kernel 从 GM 逐字读回；带 `non_blocking=false` 或显式 sync 的「每次调用必发」小块 H2D。
- 同族形态：launch 后紧跟 `aclrtSynchronizeStream(stream)` 非必要强制同步——e2e 地板可达 kernel 时间的 5-10×（host 占比 70-87%）。
- profiling 特征：chrome trace / key_averages 显示每次调用 `aten::copy_` ~50us 级 + `aten::empty`×N；所有 case 延迟 flat（与 shape 无关的固定 host 开销）；kernel 设备时间 ≪ wall（wall/t_hw > 5x）；Task Duration 与核最长耗时之差（头开销）占比 >5% 且 case 越小占比越大。
- 不适用：tiling 含 device 侧才能确定的量（如输入数据统计值）；tiling 表很大（超过几个标量的 struct 布局）——此时应改异步拷贝或 workspace 复用，而非标量直传。

## 3. 正确性红线

- kernel 标量参数类型必须与 launch 声明**严格一致**（`uint64_t`/`uint32_t` 原生类型，不要用 GM_ADDR 指针 cast 变体传标量——那是另一条回退路径）。
- 标量参数进入 args struct 的布局由 auto_gen 按签名生成，改动签名后必须重新生成/编译（全量 rebuild），不可手改生成物。
- **struct 按值传参在 `<<<>>>` 直调路径未验证，勿用**——直接展开标量参数列表（实测 18 个标量稳定）。
- 空输出/零长度分支（如 outputLength==0）必须在 kernel 内提前 return，不得写 GM。
- 参数校验（reduction 枚举、shape 匹配）保留在 host，不因快而省。

## 4. 泛化条件

- **适用**：直调工程中 tiling 只含 host 已知量的任何算子（shape 推导型、元数据型、配置型）；host 主导的高频小 kernel。标量个数无硬上限（实测 18 个稳定）；≤3~4 个 int32 时最简，>8 个或含数组时仍应走 GM tiling 区。
- **不适用**：tiling 依赖输入数据内容；tiling 结构巨大；ACLNN 官方框架算子（有 tiling 协议约束）；host 必须读输出再决策的算子（同步是语义必需，不可删）。
- 与 `host-reduce-sync-gate` 互补：本卡消「tiling 传输通道」，该卡消「host 侧同步/分配逻辑」。

## 5. 实施步骤

1. kernel 签名：`fn(GM_ADDR y, GM_ADDR tiling)` → `fn(GM_ADDR y, uint64_t scalarA, uint32_t scalarB)`。
2. kernel 类：删除 GM tiling 逐字节拷贝（`BnViewCopyTiling` 类循环），标量直接成员初始化。
3. host：删除 tilingCpu/tilingNpu 两个 empty + memcpy + copy_，`do` 函数签名带标量直传。
4. **平台核数查询静态缓存**：`QueryAivCoreNum`/`GetCoreNumAiv` 改 `static const` 一次性初始化。
5. **删除 launch 后非必要强制同步**：确认输出消费路径全部 stream-ordered、评测脚本外层已有 synchronize 兜底后，删除 `aclrtSynchronizeStream`。
6. 全量 rebuild（auto_gen 重新生成 launch 签名），验证生成的 `aclrtlaunch_*` 参数含标量。
7. 先跑 1-case 原型计时（收益需超噪声），再全量 bench + 精度。

## 6. LLM 前置问题

- tiling struct 里是否**每一项**都能在 host 由 shape/属性算出？有没有 device 侧才知道的量？
- 删除 tiling 后 kernel 是否还有任何 GM 读取依赖（除业务输入输出）？
- 空输出路径 kernel 是否保持「不启动写操作」而 launch 本身保留（反作弊安全）？

## 7. 验收标准

- build + 精度全过；验收数据（910B3, 50 iters, 空闲卡）：每调用 wall 127.0 → 35.0us（-72%）；geo 2.457 → 8.903x；精度 20/20（bit-exact int64）。顺带消除 tiling tensor 释放的 allocator 慢路径（trace Free 项 142.6 → 52.5us/次）。

## 检索卡（短卡）

动作：将 host 打包并经 GM 传入 tiling，改为在 kernel 签名中直接传递标量参数。
适用：直调工程中，tiling 仅含 host 已知的 shape、元数据或配置标量。
限制：参数数量、类型须符合编译器与 launch ABI；kernel 标量类型须与 launch 声明严格一致。
范围：tiling 仅含 host 已知标量的直调算子。
检索词：AscendC tikcpp 直调、标量 kernel 参数、tiling、同步 H2D、launch ABI
机会：host 为 tiling 创建 CPU/NPU 小张量，并执行 memcpy 与同步 copy_。
