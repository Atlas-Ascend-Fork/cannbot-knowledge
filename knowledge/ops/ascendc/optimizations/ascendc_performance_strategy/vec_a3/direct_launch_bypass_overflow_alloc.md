---
type: Optimization
title: 自研直调 launch 路径：消除 auto_gen 框架的 per-launch overflow 设备内存分配/释放
description: 改走自研直调 launch，绕过 auto_gen 每次 8B overflow 分配与释放。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-direct-launch-bypass-overflow-alloc.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：自研直调 launch 路径：消除 auto_gen 框架的 per-launch overflow 设备内存分配/释放

> 单一优化点：AscendC tikcpp 直调工程中，auto_gen 生成的 `aclrtlaunch_*` 包装每次调用都 `AllocAscendMemDevice(8B)` + `FreeAscendMemDevice(8B)`（overflow 缓冲的两次驱动级调用，release 构建实际从不写它）。自己注册一次 kernel 二进制并持有**进程级静态 overflow 缓冲**，launch 直接调框架的 `LaunchAscendKernel`，跳过 per-call 分配/释放与 prof 检查。

## 1. 原理

- auto_gen `aclrtlaunch_*` 的固定序列：栈上 args struct → `AllocAscendMemDevice(&overflow, 8)` → `LaunchAscendKernel` → `FreeAscendMemDevice(overflow)`。overflow 写回仅在 `ASCENDC_DUMP && ASCENDC_DEBUG` 下发生——release 构建里这两次驱动级分配/释放是纯浪费。
- 对高频微小 kernel（host 主导），每次 launch 多付 ~8-10us（实测 35.0 → 24.5us/kernel_mean，单次调用 -8.5us）。
- 框架符号（`RegisterAscendBinary` / `LaunchAscendKernel` / `AllocAscendMemDevice` / `FreeAscendMemDevice`）都从 `libkernels.a` 导出，pybind 扩展链接同一静态库即可自行调用；嵌入的 kernel 二进制 blob 符号（`__ascend_kernel_<soc>_kernels`）同理可 extern 引用。

## 2. 性能问题模式

- 触发代码形态：直调工程（`kernel<<<blockDim, nullptr, stream>>>` 语法），host 每次调用走 auto_gen `aclrtlaunch_*`。
- profiling 特征：chrome trace 里 `Free` 项 avg 数十 us（含 overflow 释放），远超业务张量释放的合理值；kernel 设备时间 ≪ wall。
- 不适用：ACLNN 官方算子框架（非直调）；需要 ASCENDC_DUMP 调试的构建；launch 频率低的大 kernel（8us 占比可忽略）。

## 3. 正确性红线

- args struct 布局/对齐必须与 auto_gen 生成的**完全一致**（逐成员 alignas 镜像，框架按签名解析）；签名一变就要同步镜像改。
- overflow 静态缓冲进程级复用：release 不写；若开启 ASCENDC_DUMP/DEBUG 必须恢复 per-call 分配。
- `RegisterAscendBinary` 与 host_stub constructor 的注册并存（同 binary 双 handle）需实测验证无冲突。
- 注册失败要有 fallback（回退旧 `*_do` 路径），不能静默不 launch。
- **不要**借本卡顺带短路 launch 本身：空输出算子不 launch 有被评测判反作弊 0 分的风险（历史教训），kernel 启动必须保留。

## 4. 泛化条件

- **适用**：任何 AscendC tikcpp 直调 + 高频小 kernel + host 主导的算子（微小 shape、shape/元数据推导型）。
- **不适用**：kernel 本身耗时大的算子（launch 框架开销占比 <5%）；依赖 profiling hook（StartAscendProf/ReportAscendProf）的采集构建。

## 5. 实施步骤

1. pybind 扩展里 `extern "C"` 声明四个框架符号 + extern 镜像声明二进制 blob（struct：5×uint32_t 头 + `uint8_t aiv_buf[]`，只用字段偏移）。
2. 进程级懒初始化（`static` local lambda）：`RegisterAscendBinary(aiv_buf, aiv_file_len, 1, &handle)` 一次 + `AllocAscendMemDevice(&overflow, 8)` 一次永不释放。
3. 每次调用：栈上构造镜像 args struct（含 overflow 指针指向静态缓冲）→ `LaunchAscendKernel(handle, 0, blockDim, &args, sizeof(args), stream)`。
4. 1-case 原型验证正确性（输出 bit-exact）+ 计时，再全量 bench + 精度。

## 6. LLM 前置问题

- 目标构建是否 release（无 ASCENDC_DUMP/DEBUG）？
- args struct 是否与当前签名逐成员镜像（含对齐）？
- 是否保留了 kernel launch（未滑向"不 launch"的反作弊红线）？
- CANN 大版本升级后框架符号/布局是否需要回归验证？

## 7. 验收标准

- build + 精度全过；验收数据（910B3, 50 iters, 空闲卡）：每调用 wall 35.0 → 24.5us（-30%）；geo 8.903 → 12.457x；精度 20/20。原型单 case：none 39.9→31.1us，mean 32.5→24.2us（overflow Alloc/Free 对 = 8.5us/次）。

## 检索卡（短卡）

动作：改走自研直调 launch，绕过 auto_gen 每次 8B overflow 分配与释放。
适用：适用于 AscendC tikcpp 直调、高频小 kernel、host 主导算子。
限制：args struct 的成员布局与对齐必须和 auto_gen 完全一致。
范围：AscendC tikcpp 直调工程的 host launch 路径。
检索词：aclrtlaunch、overflow、AllocAscendMemDevice、LaunchAscendKernel、Free。
机会：每次调用经过 aclrtlaunch 包装，trace 中出现固定 Free 项。
代价：kernel 本身耗时大时不适用。
