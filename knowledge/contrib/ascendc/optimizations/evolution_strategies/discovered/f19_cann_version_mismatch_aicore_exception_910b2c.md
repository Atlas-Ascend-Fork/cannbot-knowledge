---
type: Optimization
title: "F19: 编译期 CANN 与运行时 CANN 版本不匹配 → 假的内核 bug"
description: "编译期 CANN（$ASCEND_HOME_PATH 指向的默认安装）与设备侧运行时 CANN 版本不一致时，device .so 能加载、能 launch，但在第一个 ReduceMax（softmax）处必然 aicore exception；未改动的基线内核同样复现。基线也失败时应先隔离环境与共享路径，而不是直接改内核。"
tags:
  - task.debugging
  - topic.attention
  - topic.compute.reduction
  - topic.compute.normalization
  - topic.compute.composite
  - topic.data_movement.layout_transform
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/appendix/Release_Notes/CANN_9_1_0.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/appendix/interface_change_description.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f19_cann_version_mismatch_aicore_exception_910b2c.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---
> 证据：基线/变体与逐 case 数据见 [证据包 cases/f19_cann_version_mismatch_aicore_exception_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f19_cann_version_mismatch_aicore_exception_910b2c.json)。

> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F19: 编译期 CANN 与运行时 CANN 版本不匹配 → 假的内核 bug

## 现象
`ASCEND_HOME_PATH` 默认指向系统安装的 CANN 8.5.1，而设备侧运行环境是 CANN 9.1。
用 8.5.1 的头/库 + bisheng 编出的 device .so：

- 能加载、能 launch；
- 在**第一个 `ReduceMax`（softmax）处必然** `aicore exception code 0x40`、
 `mte error 0x380300007d`、`loopend executed before loop, lcnt=0`；
- **未改动的 pristine 基线内核同样复现**（这条是关键线索，但不是唯一可能原因：
 基线与改版也可能共享同一个内核缺陷或构建缓存）。

另有一个伴生现象：`SetFlag/WaitFlag(EVENT_ID3)` 手工事件写法被怀疑有问题 —— 实际是误判，
改用 TQue 只是绕过了那一次编译，换成 9.1 后原写法正常。

## Resolution
1. **基线同样失败时优先排查环境或共享路径**，而不是直接判定为内核缺陷。隔离步骤：
 固定基线源码、设备与输入，只切换编译/运行所用的 CANN 配套，重新编译并重跑，
 同时确认进程实际加载的库（`ldd`/启动日志）与预期一致；只有切换配套后恢复，才把归因定为环境。
2. 锁定正确的 CANN：`export ASCEND_HOME_PATH=<目标 CANN 安装根>`（不要把本机绝对路径写死到内核或脚本），
 并把其 `bin` 与 `tools/profiler/bin` **前置到 PATH**（否则命中的旧版 `msprof` 会 dlopen 失败），
 同时 `LD_LIBRARY_PATH` 加其 `lib64` 与 `runtime/lib64`。
3. Python 侧用与 CANN 配套的 venv（例如 CANN 9.1 配 `torch 2.12 + torch_npu 2.12`）；
 系统 python3 的旧版 torch 与新版 CANN 不配套时会出现符号/ABI 问题。
4. `evaluate_ascendc.sh` 会自己 source 环境；但 `msprof_profile_run.sh` **不会** ——
 跑性能前不设 `LD_LIBRARY_PATH` 会表现为「全部 case -> ERR / Could not load this library」。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f19_cann_version_mismatch_aicore_exception_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

