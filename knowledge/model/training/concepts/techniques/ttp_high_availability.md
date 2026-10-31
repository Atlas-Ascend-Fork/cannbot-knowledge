---
type: Concept
title: TTP 高可用容错（故障检测 + 状态 Dump + 训练恢复）
description: MindSpeed TTP 在 verl 栈尝试从健康副本保存故障 checkpoint，含 Controller/Processor、心跳、优化器异常包装和 dump 通信域。固定版本被动超时/断连入口会因先置 FAULT 而跳过 dump；故障上报、退出确认及超时配置也有实现限制。仅有特定 post-step 注入路径，文件存在性检查不足以证明任意故障时刻可恢复或损失仅一个 step；须独立验证一致性与外部重启。
tags:
- task.optimization
- topic.reinforcement_learning
status: stable
sources:
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/README.md
  role: primary
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/__init__.py
  role: supporting
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/comm/controller.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/comm/processor.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/comm/socket_server.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/adaptor.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/recovery/exception_handler.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/recovery/dump_save.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/replica/replica_group.py
  role: implementation
- resource: cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/replica/replica_optimizer.py
  role: implementation
created_at: '2026-06-29T00:00:00Z'
updated_at: '2026-10-29T15:31:31Z'
platforms:
- agnostic
---

# TTP 高可用容错（故障检测 + 状态 Dump + 训练恢复）

## Summary

大规模长训练里，任一卡的硬件故障（UCE/HBM）、通信中断（HCCL/NCCL 超时、连接断开）都会让整个分布式任务挂掉；若只能回到上一次周期性 checkpoint，故障到 checkpoint 之间的算力全部作废。TTP（Training Tolerance Platform，源自 MindIO TTP 的训练容错机制）设计目标是检测故障、暂停任务、从健康副本保存权重与优化器状态，再由外部重启以减少重算损失。固定版本存在下文的入口和退出缺口；dump 绕过一致性校验、成功仅检查文件存在，不能据此保证任意故障时刻状态一致可恢复。

这套机制在本仓是 verl RL 训练栈上的实现：通过 `MindSpeedFeature` 把补丁打到 Megatron 的优化器与 `forward_backward` 调度上，借 verl 的 `Worker` / `MegatronCheckpointManager` 完成 dump。整体是「rank-0 Controller（服务端）+ 每卡 Processor（worker 端）」的中心化协调：

| 链路阶段 | 承担组件 | 关键动作 |
|---|---|---|
| 检测 | `HeartbeatManager` / `HeartbeatChecker` + `ttp_exception_handler` | 心跳缺失判 FAULT；异常装饰器捕获在途故障并自报 ABNORMAL |
| 协调 | `TTPController._on_worker_fault` | PAUSE 全员 → 选健康副本 → 下发 DUMP → 等待完成 → 通知 EXIT |
| Dump | `tft_save_callback` + `apply_dump_patches` | 用 dump_group 替换默认通信域，绕过校验，写 `model/optimizer/extra` |
| 退出/恢复 | `_handle_pause_and_dump` / `_on_exit` | 请求各 rank 退出；_on_exit 的 STOPPED 心跳存在发送缺口，由外部拉起脚本从 dump 目录续训 |

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
| `--ttp-dump-timeout-seconds` | `60` | 配置字段未被当前执行路径消费，不能控制实际 dump 等待 |
| `--ttp-wait-dump-file-timeout` | `60` | 配置字段未生效；落盘后直接检查文件存在性 |
| `--ttp-heartbeat-interval-ms` | `1000` | 心跳发送间隔 |
| `--ttp-heartbeat-timeout-ms` | `3000` | 心跳超时阈值 |
| `--ttp-max-missed-count` | `3` | 判故障前允许的连续缺失次数 |

`TTPConfig.validate()` 在启用时校验心跳三项为正、`server_port ∈ [1, 65535]`；关闭时直接放行。配置以 `_global_ttp_config` 单例缓存，未 `set` 时由 `get_ttp_config()` 从环境变量重建（Ray worker 路径）。

## 检测：心跳与异常上报

`WorkerStatus` 状态机贯穿全链路：`INIT(0) → NORMAL(1)`，故障分两类——`ABNORMAL(2)` 是 worker 自报，`FAULT(3)` 是 Controller 因心跳超时判定；暂停态 `PAUSE(4)`、终态 `STOPPED(5)`。

检测有两类入口，但 （当前来源） 的被动入口不能按设计启动 dump：

- **心跳超时（被动）**：worker 的 `HeartbeatManager` 每 `interval_ms` 发一次心跳，携带 `status` 与 `iteration`；Controller 的 `HeartbeatChecker._check_timeouts` 对超过 `timeout_ms` 未更新的 rank 累加 `missed_count`，达到 `max_missed_count` 即置 `FAULT` 并回调 `_on_worker_timeout`。启动有 `INIT_TIMEOUT_SECONDS = 120` 的宽限：未集齐 `world_size` 个 worker 且首注册不足 120s 时跳过超时判定，避免冷启动误杀。已处于 `ABNORMAL/PAUSE` 的 rank 不再判超时。连接断开（`_on_disconnect`）也先置 FAULT。两者随后调用 _on_worker_fault，但该函数入口对已 FAULT 直接返回，因此被动故障链路实际跳过暂停与 dump。
- **在途异常（主动）**：`ttp_exception_handler` 装饰器包住优化器方法；forward_backward 用单独的 patched_forward_backward_wrapper，只处理暂停和 TTP_INJECTED_FAULT，其余 RuntimeError 重新抛出，不获得同样的异常覆盖。装饰器，在方法入口先 `check_and_raise_if_paused()`，执行体异常时按错误串归类。被识别为 TTP 故障的关键字（对 `str(e)` 做子串匹配）包括 `UCE`、`HBM`、`HCCL`、`NCCL`、`timeout`、`broken`、`connection`、`RuntimeError`、`TTP_INJECTED_FAULT`；命中后调 `processor.on_worker_exception(e)` 把故障上报 Controller（置 `ABNORMAL` 并发心跳），该调用本身循环等待，收到退出信号 os._exit(0)，600秒超时或异常 os._exit(1)，不会正常返回到装饰器后续 _handle_pause_and_dump。后者是暂停等其他控制路径的等待逻辑。

两类特殊控制异常不算新故障：`STEP FINISH`（Controller 通过 `PyThreadState_SetAsyncExc` 注入、或 `_pause_type == 'RAISE'`）表示主线程被 PAUSE；`FORCE STOP` 是本机 `stop_device` 强杀在途 NPU 算子所致，只需静默进入 PAUSE。为兜住逃逸出装饰器的 FORCE STOP，`set_main_thread_id` 还在主线程装了 `sys.excepthook`，把 `FORCE STOP/UCE/HBM/HCCL/NCCL/TTP_INJECTED_FAULT` 路由到 `_handle_pause_and_dump`，防止 worker 直接崩。

仓内自带故障注入用于验证：`TTP_FAULT_INJECTION_ENABLED=true` 时，在 `TTP_FAULT_INJECTION_ITERATION`（默认 3）、`TTP_FAULT_INJECTION_RANK`（默认 1）抛 `TTP_INJECTED_FAULT`，且有一次性 guard。注入点放在 optimizer step 完成之后（`_iteration = _ttp_shared_step // 8`），该除数8来自“每训练步调用8次子优化器”的经验配置，计数按子优化器调用增加；更换微批或优化器组合后必须重新核对迭代与训练步关系，不能无条件视为 global_step。

## 协调：暂停 → Dump → 退出

`_on_worker_fault(fault_rank)` 在 `_dump_lock` 下串行化整条故障流程（已 `FAULT/STOPPED`、已完成 dump、或 dump 进行中的重复故障都直接返回，并入 `_fault_ranks`）：

1. **PAUSE 全员**：给除 `fault_rank` 外的所有 rank 发 `WAIT_RELEASE`（`action='PAUSE'`），最多等 10s 直到几乎全部进入 `PAUSE`。worker 端 `_on_wait_release` 收到后立即上报 `PAUSE`、`clear` dump 事件、置 `_limit_step = 当前 iteration + 1` 与 `_pause_type = 'RAISE'`，并 `inject_exception_to_main_thread()` 用 `PyThreadState_SetAsyncExc` 给主线程注入 `STEP FINISH`；若主线程卡在 NCCL，靠 dump 时的 `stop_device` 打断。
2. **选健康副本**：`begin_exception_ckpt(fault_ranks)` 取故障 rank 上报的 `iteration` 作为 `repair_step`，按 DP-CP / DP-EP 副本拓扑用 `choose_rank_inner_rl` 选出一组**完整且全部正常**的 rank 作为 dump 组。RL 拓扑下世界被切成两半（如 actor/critic），约束所有 dump rank 必须同属一半，否则返回错误以保证优化器状态一致；选不到健康组就给全员发 EXIT。
3. **下发 DUMP 并等待**：向 dump 组发 `DUMP_REQUEST`（携带分组与 `world_ranks`），主流程 `_dump_complete_event.wait(timeout=600.0)`。各 dump rank 回 `DUMP_RESPONSE`，`_on_dump_response` 集齐全部回包后判 `all_dump_success` 并校验 `global_step_{N}` 目录存在。
4. **退出**：dump 成功则给所有连接 rank 发 `EXIT`，并 `_wait_for_stopped_confirmation`（10s，期间最多重发 2 次）等各 rank 上报 `STOPPED`；dump 失败或 600s 超时则 `controller.stop()` + `sys.exit(1)` 只结束调用它的线程；socket 接收回调可在后台线程运行，该分支也未保证全员收到 EXIT，因此可能需要外部终止整个任务。

worker 端的等待逻辑集中在 `_handle_pause_and_dump`：`wait_next_action(timeout=300)` 串行化主线程进入等待态——返回 `"EXIT"` 则上报 STOPPED 后 `os._exit`；返回 `"DUMP"` 则 `wait_for_dump_complete(timeout=1800)` 等后台 save 线程；dump 失败抛 `RuntimeError`。`DUMP_REQUEST` 到达时（`_on_dump_request`）会 `set` dump 事件让等待中的主线程转入 `"DUMP"`，并起一个 daemon `_save_data_thread` 调 `save_handler.execute_save()` 真正落盘——`stop_device` 在落盘内部执行，正常路径下主线程已暂停、相当于空操作。

控制消息类型（`MsgType`）：`HEARTBEAT/HEARTBEAT_ACK`、`REGISTER(_ACK)`、`REGISTER_REPLICA_GROUP(_ACK)`、`DUMP_REQUEST/DUMP_RESPONSE`、`EXCEPTION`、`TRIGGER_DUMP(_ACK)`、`WAIT_RELEASE`（兼作 PAUSE 与放行）、`EXIT`。

## Dump：从健康副本写一致 checkpoint

副本拓扑由 `replica_group.py` 维护，`REPLICA_NUM = 2`：`ttp_initialize_replica_dp_group()` 用 Megatron `RankGenerator` 按 `tp-cp-ep-dp-pp` 序枚举每个 DP-CP 组，`build_dp_cp_replica_group` 把每组按 `REPLICA_NUM` 二分成副本子列、各建默认分布式后端组与显式 GLOO 组（NPU 环境默认后端取决于实际初始化配置）；MoE 场景再建 DP-EP 副本组。建组要求对应 DP-CP / DP-EP rank 列表长度能被 REPLICA_NUM=2 整除；TTPReplicaOptimizer 还拒绝原始 DP group 大小为1或奇数。每个 worker 只看到自己本地的 DP 组，副本切分与「选哪一份副本来 dump」由 Controller 的 `choose_rank_inner_rl` 合并完成。

`tft_save_callback(step, save_info, worker)` 是 dump 主入口，难点是**让一组只覆盖单份副本的 rank 写出一份完整的分布式 checkpoint**，为此临时改写通信拓扑并绕过若干一致性校验：

- 从 `save_info` 的 `world_ranks` 用 `dist.new_group` 建 `dump_group`；`_cache_parallel_state` 先缓存 TP/PP/DP 的 rank/world_size（防止默认通信域被替换后 `parallel_state` 取值出错），再 `_replace_default_group_with_dump` 把 `dist.GroupMember.WORLD` 换成 `dump_group`。
- `_reset_replica_groups_for_dump` / `_align_optimizer_dp_groups` 把副本子组与每个子优化器的 `data_parallel_group` 重置成与 dump rank 对齐的新组。
- `_save_dump_checkpoint`：必要时把 offload 到 CPU 的模型搬回 device；`gc.collect()` + 睡 3s 后 `torch_npu.npu.stop_device` / `restart_device` 清在途算子；调 `apply_dump_patches()` 打 6 个 Megatron checkpoint 临时补丁；在 `MegatronCheckpointManager` 上强制 `async_save=False`、`checkpoint_save_contents = ["model","optimizer","extra"]`，由 dump 组首 rank 把 `rank` 改写为 0，调 `save_checkpoint(...)` 落盘；之后恢复默认通信域、部分副本组和 parallel_state 缓存；apply_dump_patches 没有撤销入口，dump 补丁保留到进程退出。
- 仅当传入上下文具有 worker.config.actor 时 `global_step` 取 `step // ppo_epochs`，其他分支直接取 step；replica_optimizer 默认登记的上下文是优化器实例，dump 路径为 `{dump_dir}/global_step_{N}/actor`。落盘后在 `dist_ckpt/` 下校验 `.metadata`、`common.pt` 与至少一个 `.distcp` 文件存在，三者齐备才算成功；最后在 `dump_group` 上 `barrier`。

`apply_dump_patches()`（`dump_patches.py`，由 `dump_save.py` 在落盘前显式调用、进程退出不需回滚）替换的 6 个 Megatron 目标都为绕过「只有部分 rank 参与」时会失败的校验（下列五个 wrapper，其中 `save_preprocess` 在 `state_dict_utils` 与 `serialization` 两处模块路径各注册一次、共占两个目标）：`save_preprocess`（强制 `validate_access_integrity=False`）、`FullyParallelSaveStrategyWrapper.apply_saving_parallelization`（`ignore_groups=True` 纳入所有 `ShardedTensor`、把 `ShardedObject` 的 `replica_id` 置 0 否则模型权重会被静默丢弃）、`sharded_tensor_to_torch_sharded_tensor`（临时 no-op 掉远端 device 校验）、`MCoreSavePlanner.create_global_plan`（no-op 掉 `_validate_global_plan`）、`FullyParallelSaveStrategyWrapper.__init__`（强制用 `dump_group` 作 `parallelization_group`，避免等故障 rank 应答而 hang）。

## 恢复

本模块只尝试保存 dump 并请求退出，真正续训由外部脚本从 dump 目录启动。成功退出路径的 `_on_exit` 先设置 _stop_event，随后调用发送 STOPPED 心跳；底层 _send_heartbeat_safe 因事件已设置而直接返回 False，因此不能把 Controller 的确认等待当成可靠退出握手。失败/超时分支还可能只结束 Controller 接收线程，任务级清理需外部监督。

将重算损失压到一个 step 是设计目标，固定来源只展示特定 post-optimizer 注入路径，未证明其他故障时刻各 rank、权重和优化器处于同一步。dump 成功的文件存在性检查也不是恢复一致性验收，使用前须在目标配置验证故障注入、保存、退出和重新加载后的状态。dump 默认只保留最近一份。

## Evidence

- [README.md](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/README.md)（primary）
- [__init__.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/__init__.py)（supporting）
- [controller.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/comm/controller.py)（implementation）
- [processor.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/comm/processor.py)（implementation）
- [socket_server.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/comm/socket_server.py)（implementation）
- [adaptor.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/adaptor.py)（implementation）
- [exception_handler.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/recovery/exception_handler.py)（implementation）
- [dump_save.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/recovery/dump_save.py)（implementation）
- [replica_group.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/replica/replica_group.py)（implementation）
- [replica_optimizer.py](../../../../../cann-recipes-raw/mindspeed/c5a72765f99fd8470362c7afdc2cdffe0ab5aea6/mindspeed/core/ttp/replica/replica_optimizer.py)（implementation）

## Links

- [auto-settings](auto_settings.md)（同为长训练前置：先用 auto-settings 搜出放得下、跑得快的并行/重计算/内存配置，TTP 再保住长训练过程不因单卡故障作废）
- [training-debug-observability](training_debug_observability.md)（同属训练可观测/可靠性：Flight Recorder 记录通信轨迹辅助定位 HCCL 超时，TTP 在检测到 HCCL/NCCL 故障后接管暂停与 dump）
- [mindspeed](../frameworks/mindspeed.md)（TTP 经 `MindSpeedFeature` / `register_patches` 机制接入的框架底座）
