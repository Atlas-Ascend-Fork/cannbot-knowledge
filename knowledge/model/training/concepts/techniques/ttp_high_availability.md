---
type: Concept
title: TTP 高可用容错（故障检测 + 状态 Dump + 训练恢复）
description: TTP（Training Tolerance Platform，源自 MindIO TTP）是 MindSpeed 在 verl RL 训练栈上的高可用容错机制，降低大规模长训练因单卡硬件/通信故障导致整任务作废的算力损失。架构为 rank-0 Controller（服务端）+ 每卡 Processor（worker 端）的中心化协调：HeartbeatManager/HeartbeatChecker 按 interval/timeout/max-missed 检测心跳超时，ttp_exception_handler 装饰器捕获在途 UCE/HBM/HCCL/NCCL 异常并自报 ABNORMAL；_on_worker_fault 先 WAIT_RELEASE 暂停全员，经 choose_rank_inner_rl 选一组健康副本（REPLICA_NUM=2，DP-CP/DP-EP 拓扑）下发 DUMP_REQUEST；tft_save_callback 用 dump_group 替换默认通信域、apply_dump_patches 打 6 个 Megatron checkpoint 补丁绕过一致性校验，从单份副本写出含 model/optimizer/extra 的完整分布式 checkpoint（global_step=step//ppo_epochs）；成功后 Controller 发 EXIT、各 rank os._exit，由外部脚本从 dump 目录续训。开关 --ttp-enabled，经 MindSpeedFeature optimization_level=2 + verl repatch 两阶段生效。关键术语：Controller/Processor、heartbeat、WorkerStatus、replica group、dump_group、tft_save_callback、apply_dump_patches。
tags:
- task.optimization
- topic.reinforcement_learning
status: stable
sources:
- resource: https://gitcode.com/ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/README.md
  role: primary
- resource: https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/__init__.py
  role: supporting
created_at: '2026-06-29T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# TTP 高可用容错（故障检测 + 状态 Dump + 训练恢复）

## Summary

大规模长训练里，任一卡的硬件故障（UCE/HBM）、通信中断（HCCL/NCCL 超时、连接断开）都会让整个分布式任务挂掉；若只能回到上一次周期性 checkpoint，故障到 checkpoint 之间的算力全部作废。TTP（Training Tolerance Platform，源自 MindIO TTP 的训练容错机制）把损失压到最小：训练中**实时检测异常**，一旦某卡故障，立即**暂停全体**，从一份**仍然健康的副本（replica）**把当前 step 的权重 + 优化器状态 dump 成一致 checkpoint，再通知所有 rank 退出——续训只需从这份 dump 重新拉起，而不是退回更早的周期 checkpoint。

这套机制在本仓是 verl RL 训练栈上的实现：通过 `MindSpeedFeature` 把补丁打到 Megatron 的优化器与 `forward_backward` 调度上，借 verl 的 `Worker` / `MegatronCheckpointManager` 完成 dump。整体是「rank-0 Controller（服务端）+ 每卡 Processor（worker 端）」的中心化协调：

| 链路阶段 | 承担组件 | 关键动作 |
|---|---|---|
| 检测 | `HeartbeatManager` / `HeartbeatChecker` + `ttp_exception_handler` | 心跳缺失判 FAULT；异常装饰器捕获在途故障并自报 ABNORMAL |
| 协调 | `TTPController._on_worker_fault` | PAUSE 全员 → 选健康副本 → 下发 DUMP → 等待完成 → 通知 EXIT |
| Dump | `tft_save_callback` + `apply_dump_patches` | 用 dump_group 替换默认通信域，绕过校验，写 `model/optimizer/extra` |
| 退出/恢复 | `_handle_pause_and_dump` / `_on_exit` | 各 rank 完成 dump 后上报 STOPPED 并 `os._exit`，由外部拉起脚本从 dump 目录续训 |

## 启用与配置

开关是 `--ttp-enabled`（`action='store_true'`，默认关）。`TTPFeature` 以 `optimization_level=2` 注册，启用判据走基类的 `getattr(args, 'ttp_enabled', False)`，分两阶段生效：

- **Phase 1（import 期）**：verl CLI 上通常没有 `--ttp-enabled`，`is_need_apply` 为 False，不打补丁。
- **Phase 2（repatch）**：verl 的 `_init_device_mesh()` 带着 `override_transformer_config`（含 `ttp_enabled=True`）调 `repatch()`，重新注册补丁，optimizer 的 `__new__` 补丁在 worker 进程里真正生效。

因为 worker 多为 Ray actor 进程，配置走双通道：bash 启动器先 `export TTP_*` 环境变量，worker 经 `os.environ` 继承；`get_ttp_config()` 在优化器构造时据此装出完整 `TTPConfig`，`set_ttp_config()` 反向把配置同步回 `os.environ` 供其它 actor 读取。

`register_patches` 在 `ttp_enabled=True` 时注册四处永久补丁：

- `DistributedOptimizer.__new__` → `patched_optimizer_new`：存在 REPLICA 子组时改返回 `TTPReplicaOptimizer`，并触发幂等的副本子组构建。
- `ChainedOptimizer.__init__` → `patched_chained_optimizer_init`：在每个 TTP 子优化器上挂 `_ttp_parent_chained`，让 dump 回调能拿到完整 `ChainedOptimizer` 产出完整 `sharded_state_dict`。
- `ChainedOptimizer.step` → `patched_chained_optimizer_step_wrapper`：在整个 optimizer step（含梯度裁剪）层面套 `ttp_exception_handler`，使裁剪阶段触发的 FORCE STOP 也能被接住。
- `forward_backward_no_pipelining` → `patched_forward_backward_wrapper`：在前向/反向调度里逐步检查 PAUSE，避免异步注入的暂停异常被 C 调用拖延。

配置项与默认值（`register_args` 与 `constants.py` 一致）：

| 参数 / 环境变量 | 默认 | 含义 |
|---|---|---|
| `--ttp-server-ip` / `TTP_SERVER_IP` | `0.0.0.0` | Controller 监听 IP |
| `--ttp-server-port` / `TTP_SERVER_PORT` | `29500` | Controller 监听端口 |
| `--ttp-dump-dir` / `TTP_DUMP_DIR` | `ttp_dump` | dump checkpoint 目录 |
| `--ttp-max-dump-ckpt-to-keep` | `1` | 保留的 dump checkpoint 数 |
| `--ttp-save-optimizer` / `--ttp-save-rng` | `True` | dump 是否含优化器 / RNG 状态 |
| `--ttp-dump-timeout-seconds` | `60` | dump 超时 |
| `--ttp-wait-dump-file-timeout` | `60` | 等待 dump 文件落盘超时 |
| `--ttp-heartbeat-interval-ms` | `1000` | 心跳发送间隔 |
| `--ttp-heartbeat-timeout-ms` | `3000` | 心跳超时阈值 |
| `--ttp-max-missed-count` | `3` | 判故障前允许的连续缺失次数 |

`TTPConfig.validate()` 在启用时校验心跳三项为正、`server_port ∈ [1, 65535]`；关闭时直接放行。配置以 `_global_ttp_config` 单例缓存，未 `set` 时由 `get_ttp_config()` 从环境变量重建（Ray worker 路径）。

## 检测：心跳与异常上报

`WorkerStatus` 状态机贯穿全链路：`INIT(0) → NORMAL(1)`，故障分两类——`ABNORMAL(2)` 是 worker 自报，`FAULT(3)` 是 Controller 因心跳超时判定；暂停态 `PAUSE(4)`、终态 `STOPPED(5)`。

检测有两条独立入口，最终都汇入 `TTPController._on_worker_fault`：

- **心跳超时（被动）**：worker 的 `HeartbeatManager` 每 `interval_ms` 发一次心跳，携带 `status` 与 `iteration`；Controller 的 `HeartbeatChecker._check_timeouts` 对超过 `timeout_ms` 未更新的 rank 累加 `missed_count`，达到 `max_missed_count` 即置 `FAULT` 并回调 `_on_worker_timeout`。启动有 `INIT_TIMEOUT_SECONDS = 120` 的宽限：未集齐 `world_size` 个 worker 且首注册不足 120s 时跳过超时判定，避免冷启动误杀。已处于 `ABNORMAL/PAUSE` 的 rank 不再判超时。连接断开（`_on_disconnect`）直接置 `FAULT`。
- **在途异常（主动）**：`ttp_exception_handler` 装饰器包住优化器方法与 `forward_backward`，在方法入口先 `check_and_raise_if_paused()`，执行体异常时按错误串归类。被识别为 TTP 故障的关键字（对 `str(e)` 做子串匹配）包括 `UCE`、`HBM`、`HCCL`、`NCCL`、`timeout`、`broken`、`connection`、`RuntimeError`、`TTP_INJECTED_FAULT`；命中后调 `processor.on_worker_exception(e)` 把故障上报 Controller（置 `ABNORMAL` 并发心跳），再进入 `_handle_pause_and_dump` 等待协调，而非立刻 `os._exit`——立即退出会让同 DP 组的伙伴卡在在途集合通信上死锁。

两类特殊控制异常不算新故障：`STEP FINISH`（Controller 通过 `PyThreadState_SetAsyncExc` 注入、或 `_pause_type == 'RAISE'`）表示主线程被 PAUSE；`FORCE STOP` 是本机 `stop_device` 强杀在途 NPU 算子所致，只需静默进入 PAUSE。为兜住逃逸出装饰器的 FORCE STOP，`set_main_thread_id` 还在主线程装了 `sys.excepthook`，把 `FORCE STOP/UCE/HBM/HCCL/NCCL/TTP_INJECTED_FAULT` 路由到 `_handle_pause_and_dump`，防止 worker 直接崩。

仓内自带故障注入用于验证：`TTP_FAULT_INJECTION_ENABLED=true` 时，在 `TTP_FAULT_INJECTION_ITERATION`（默认 3）、`TTP_FAULT_INJECTION_RANK`（默认 1）抛 `TTP_INJECTED_FAULT`，且有一次性 guard。注入点放在 optimizer step 完成之后（`_iteration = _ttp_shared_step // 8`），以对齐 verl「step N 结束后存 `global_step_N`、含 post-step-N 权重」的命名约定。

## 协调：暂停 → Dump → 退出

`_on_worker_fault(fault_rank)` 在 `_dump_lock` 下串行化整条故障流程（已 `FAULT/STOPPED`、已完成 dump、或 dump 进行中的重复故障都直接返回，并入 `_fault_ranks`）：

1. **PAUSE 全员**：给除 `fault_rank` 外的所有 rank 发 `WAIT_RELEASE`（`action='PAUSE'`），最多等 10s 直到几乎全部进入 `PAUSE`。worker 端 `_on_wait_release` 收到后立即上报 `PAUSE`、`clear` dump 事件、置 `_limit_step = 当前 iteration + 1` 与 `_pause_type = 'RAISE'`，并 `inject_exception_to_main_thread()` 用 `PyThreadState_SetAsyncExc` 给主线程注入 `STEP FINISH`；若主线程卡在 NCCL，靠 dump 时的 `stop_device` 打断。
2. **选健康副本**：`begin_exception_ckpt(fault_ranks)` 取故障 rank 上报的 `iteration` 作为 `repair_step`，按 DP-CP / DP-EP 副本拓扑用 `choose_rank_inner_rl` 选出一组**完整且全部正常**的 rank 作为 dump 组。RL 拓扑下世界被切成两半（如 actor/critic），约束所有 dump rank 必须同属一半，否则返回错误以保证优化器状态一致；选不到健康组就给全员发 EXIT。
3. **下发 DUMP 并等待**：向 dump 组发 `DUMP_REQUEST`（携带分组与 `world_ranks`），主流程 `_dump_complete_event.wait(timeout=600.0)`。各 dump rank 回 `DUMP_RESPONSE`，`_on_dump_response` 集齐全部回包后判 `all_dump_success` 并校验 `global_step_{N}` 目录存在。
4. **退出**：dump 成功则给所有连接 rank 发 `EXIT`，并 `_wait_for_stopped_confirmation`（10s，期间最多重发 2 次）等各 rank 上报 `STOPPED`；dump 失败或 600s 超时则 `controller.stop()` + `sys.exit(1)` 让整个程序退出。

worker 端的等待逻辑集中在 `_handle_pause_and_dump`：`wait_next_action(timeout=300)` 串行化主线程进入等待态——返回 `"EXIT"` 则上报 STOPPED 后 `os._exit`；返回 `"DUMP"` 则 `wait_for_dump_complete(timeout=1800)` 等后台 save 线程；dump 失败抛 `RuntimeError`。`DUMP_REQUEST` 到达时（`_on_dump_request`）会 `set` dump 事件让等待中的主线程转入 `"DUMP"`，并起一个 daemon `_save_data_thread` 调 `save_handler.execute_save()` 真正落盘——`stop_device` 在落盘内部执行，正常路径下主线程已暂停、相当于空操作。

控制消息类型（`MsgType`）：`HEARTBEAT/HEARTBEAT_ACK`、`REGISTER(_ACK)`、`REGISTER_REPLICA_GROUP(_ACK)`、`DUMP_REQUEST/DUMP_RESPONSE`、`EXCEPTION`、`TRIGGER_DUMP(_ACK)`、`WAIT_RELEASE`（兼作 PAUSE 与放行）、`EXIT`。

## Dump：从健康副本写一致 checkpoint

副本拓扑由 `replica_group.py` 维护，`REPLICA_NUM = 2`：`ttp_initialize_replica_dp_group()` 用 Megatron `RankGenerator` 按 `tp-cp-ep-dp-pp` 序枚举每个 DP-CP 组，`build_dp_cp_replica_group` 把每组按 `REPLICA_NUM` 二分成副本子列、各建 NCCL + GLOO 通信域；MoE 场景再建 DP-EP 副本组。每个 worker 只看到自己本地的 DP 组，副本切分与「选哪一份副本来 dump」由 Controller 的 `choose_rank_inner_rl` 合并完成。

`tft_save_callback(step, save_info, worker)` 是 dump 主入口，难点是**让一组只覆盖单份副本的 rank 写出一份完整的分布式 checkpoint**，为此临时改写通信拓扑并绕过若干一致性校验：

- 从 `save_info` 的 `world_ranks` 用 `dist.new_group` 建 `dump_group`；`_cache_parallel_state` 先缓存 TP/PP/DP 的 rank/world_size（防止默认通信域被替换后 `parallel_state` 取值出错），再 `_replace_default_group_with_dump` 把 `dist.GroupMember.WORLD` 换成 `dump_group`。
- `_reset_replica_groups_for_dump` / `_align_optimizer_dp_groups` 把副本子组与每个子优化器的 `data_parallel_group` 重置成与 dump rank 对齐的新组。
- `_save_dump_checkpoint`：必要时把 offload 到 CPU 的模型搬回 device；`gc.collect()` + 睡 3s 后 `torch_npu.npu.stop_device` / `restart_device` 清在途算子；调 `apply_dump_patches()` 打 6 个 Megatron checkpoint 临时补丁；在 `MegatronCheckpointManager` 上强制 `async_save=False`、`checkpoint_save_contents = ["model","optimizer","extra"]`，由 dump 组首 rank 把 `rank` 改写为 0，调 `save_checkpoint(...)` 落盘；之后恢复副本组、`parallel_state` 缓存与各项补丁。
- `global_step` 取 `step // ppo_epochs`，dump 路径为 `{dump_dir}/global_step_{N}/actor`。落盘后在 `dist_ckpt/` 下校验 `.metadata`、`common.pt` 与至少一个 `.distcp` 文件存在，三者齐备才算成功；最后在 `dump_group` 上 `barrier`。

`apply_dump_patches()`（`dump_patches.py`，由 `dump_save.py` 在落盘前显式调用、进程退出不需回滚）替换的 6 个 Megatron 目标都为绕过「只有部分 rank 参与」时会失败的校验（下列五个 wrapper，其中 `save_preprocess` 在 `state_dict_utils` 与 `serialization` 两处模块路径各注册一次、共占两个目标）：`save_preprocess`（强制 `validate_access_integrity=False`）、`FullyParallelSaveStrategyWrapper.apply_saving_parallelization`（`ignore_groups=True` 纳入所有 `ShardedTensor`、把 `ShardedObject` 的 `replica_id` 置 0 否则模型权重会被静默丢弃）、`sharded_tensor_to_torch_sharded_tensor`（临时 no-op 掉远端 device 校验）、`MCoreSavePlanner.create_global_plan`（no-op 掉 `_validate_global_plan`）、`FullyParallelSaveStrategyWrapper.__init__`（强制用 `dump_group` 作 `parallelization_group`，避免等故障 rank 应答而 hang）。

## 恢复

本模块内的「恢复」链路止于「**产出一份一致 dump + 通知所有 rank 干净退出**」：dump 成功后 Controller 给全员发 `EXIT`，worker 的 `_on_exit` 上报 `STOPPED` 心跳后 `os._exit`。真正的续训不在 TTP 代码内自动完成，而是由外部拉起脚本从 `{dump_dir}/global_step_{N}` 重新启动训练任务——相比退回上一周期 checkpoint，这份 dump 保住了故障当下的训练进度，把重算损失压到一个 step 量级。dump 默认只保留最近一份（`max_dump_ckpt_to_keep=1`）。

## Evidence

- [mindspeed](https://gitcode.com/ascend/MindSpeed) — 钉定版 @1432cb0
- [`mindspeed/core/ttp/__init__.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/__init__.py) — 模块定位 "MindSpeed TTP (Training Tolerance Platform)"、对外符号清单
- [`mindspeed/features_manager/ttp/ttp_feature.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/features_manager/ttp/ttp_feature.py) — `TTPFeature`（`optimization_level=2`、`register_args` 全部 `--ttp-*` 开关与默认、`register_patches` 四处永久补丁、Phase1/Phase2 repatch 说明）、`_try_set_ttp_config`（args↔env 桥接）
- [`mindspeed/core/ttp/config.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/config.py) — `TTPConfig` / `HeartbeatConfig`、`validate()`、`get_ttp_config` / `set_ttp_config`（单例 + `os.environ` 同步）
- [`mindspeed/core/ttp/constants.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/constants.py) — `WorkerStatus` / `MsgType` 枚举、心跳与 dump 默认常量（`MAX_DUMP_CKPT_TO_KEEP=1` 等）
- [`mindspeed/core/ttp/comm/heartbeat.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/comm/heartbeat.py) — `HeartbeatManager._send_heartbeat`（携 status/iteration）、`HeartbeatChecker._check_timeouts`（`max_missed_count`、`INIT_TIMEOUT_SECONDS=120`、跳过 ABNORMAL/PAUSE）
- [`mindspeed/core/ttp/comm/processor.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/comm/processor.py) — `TTPProcessor`（`_on_wait_release` 注入 STEP FINISH、`_on_dump_request` 起 `_save_data_thread`、`wait_next_action` / `wait_for_dump_complete`、`on_worker_exception`、`set_main_thread_id` 装 excepthook）、`SaveHandler.execute_save`
- [`mindspeed/core/ttp/comm/controller.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/comm/controller.py) — `TTPController._on_worker_fault`（PAUSE 10s → `begin_exception_ckpt` → 等 600s → EXIT）、`choose_rank_inner_rl`（同半副本选择）、`_on_dump_response`（集齐回包判成败 + 校验 `global_step_N`）、`_wait_for_stopped_confirmation`
- [`mindspeed/core/ttp/recovery/exception_handler.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/recovery/exception_handler.py) — `ttp_exception_handler`（TTP 错误关键字分类、FORCE STOP/STEP FINISH 处理）、`_handle_pause_and_dump`、`_send_stopped_heartbeat_and_exit`
- [`mindspeed/core/ttp/recovery/dump_save.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/recovery/dump_save.py) — `tft_save_callback`（dump_group 建组/替换默认 PG/落盘/校验 `.metadata`·`common.pt`·`.distcp`、`global_step=step//ppo_epochs`）、`_save_dump_checkpoint`（`stop_device`/`restart_device`、`save_contents=["model","optimizer","extra"]`）、`_cache_parallel_state`、`tft_init_controller_processor`（rank0 起 Controller 线程）
- [`mindspeed/features_manager/ttp/dump_patches.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/features_manager/ttp/dump_patches.py) — `apply_dump_patches`：6 个 Megatron checkpoint 临时补丁目标
- [`mindspeed/core/ttp/adaptor.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/adaptor.py) — `patched_optimizer_new` / `patched_chained_optimizer_init` / `patched_chained_optimizer_step_wrapper` / `patched_forward_backward_wrapper`、`_ttp_inject_fault_if_enabled`、6 个 dump 补丁实现（`ignore_groups=True`、`replica_id=0`、no-op 校验）
- [`mindspeed/core/ttp/replica/replica_group.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/replica/replica_group.py) — `REPLICA_NUM=2`、`ttp_initialize_replica_dp_group`（`RankGenerator` 按 `tp-cp-ep-dp-pp` 枚举 DP-CP/DP-EP）、`build_dp_cp_replica_group`（NCCL+GLOO 副本子组）、`ReplicaGroupManager`
- [`mindspeed/core/ttp/_registry.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/core/ttp/_registry.py) — `get_processor` / `set_processor`（打破 processor↔exception_handler 循环依赖的共享单例）

## Links

- [auto-settings](auto_settings.md)（同为长训练前置：先用 auto-settings 搜出放得下、跑得快的并行/重计算/内存配置，TTP 再保住长训练过程不因单卡故障作废）
- [training-debug-observability](training_debug_observability.md)（同属训练可观测/可靠性：Flight Recorder 记录通信轨迹辅助定位 HCCL 超时，TTP 在检测到 HCCL/NCCL 故障后接管暂停与 dump）
- [mindspeed](../frameworks/mindspeed.md)（TTP 经 `MindSpeedFeature` / `register_patches` 机制接入的框架底座）
