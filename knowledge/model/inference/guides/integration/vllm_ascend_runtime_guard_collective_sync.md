---
type: Guide
title: vLLM Ascend Runtime Guard 配置同步：单槽总线、波次对齐与生效边界
description: 沿 sync_due_bits_from_src、DueBitsBusWorker 和 apply_config_sync_payload 接入多rank框架，区分writer、TP0来源、提交与应用，诊断wave错位、尾部等待和同mtime更新风险。 解释merged bus的source-owned控制位，以及配置cascade后deferred任务保留与清理顺序。
tags:
- task.implementation
- task.debugging
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/dist.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/bus_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_bus.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_dump.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/rank_gate.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/runtime_guard.md
  role: supporting
created_at: '2026-10-29T19:31:47Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T19:41:59Z'
aliases:
- Runtime Guard merged bus source-owned 控制位
- 配置 cascade 与 deferred 清理
---

# vLLM Ascend Runtime Guard 配置同步：单槽总线、波次对齐与生效边界


## 适用任务与固定版本

新Runner已接入Runtime Guard，但部分rank配置未生效、idle波卡住、end-of-wave等待，或错误地用全world同步热配置。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的dist、RuntimeConfig与processor_bus；仅源级接线知识，整项硬件集合未知，保持draft/空平台。没有运行分布式服务或测量通信重叠收益。

## writer、总线来源与检测rank分别定位

JSON writer在inner_dp_world存在且world_size>1时以其首rank优先，多DP无该组时退到TP0且PP0，再退world首rank/RANK=0或单进程。它负责启动持久化，不等于last-PP TP0的总线来源，也不等于所有参与者；API/EngineCore的后台文件轮询不负责persist。

_runtime_config_sync_group_or_none只在last PP且TP world_size>1时返回TP组，从不返回跨DP/跨PP组。processor仅在hot_reload启用时走merged bus；否则采用本地配置与单lane dump claim路径。transport对非last PP返回None，只允许本地poll而不跨PP通信；但processor.sync_for_step对已识别的非last PP又会直接返回，不能据transport注释断言这些worker都在自动轮询。TP<=1的实际进入者和非worker后台reloader各按自身入口poll，没有一轮broadcast自动覆盖所有DP副本的保证。共享路径也需各副本看见同一内容，不能用跨DP full-world collective补齐。

进程是否为worker还看RANK、LOCAL_RANK、VLLM_DP_RANK与已建world；若非worker reloader先启动，循环发现worker身份后退出。每路径的后台线程登记不是跨进程锁；_bg_reloader_started也不表示每个后续RuntimeConfig对象都被同一线程更新。

## due位是来源拥有的，不是任意rank投票

merged路径的sync_due_bits_from_src构造float32向量 `[wave_idx, config_due, dump_due]`，仅TP0填入并broadcast；followers本地due位不做OR。src用实际ProcessGroup成员列表的首global rank，而非假定global rank0。_group_rank优先rank_in_group，再只允许is_first_rank明确来源回退，无法判定时抛错，不伪造非来源rank。

优先用cpu_group；缺少时退device_group，后者构造NPU tensor。没有gate或单rank时只是本地返回，不证明进程间已同步。独立sync_due_bits/sync_task_bus的单lane路径使用all_reduce(MAX)再按due广播对象，不能把这两种协议混写。

_WAVE_IDX_MOD为2**24，wave槽存本地_bus_wave_seq的模值，接收方不相等则抛merged-bus wave misalignment。它防止一部分跨波消费，既不是永久请求epoch，也不能区别相差整倍模周期的波次。这个seq每次merged提交增长，和WaveTracker只在真实wave增长的计数用途不同。

每个参与rank必须按相同顺序进入due-vector及各due lane；即使本rank无dump job也不能擅自跳过。来源对象构造/collective错误不被通用soft-fail吞掉，否则其他rank可能仍在等待。不要在每次_dummy_run内重复sync；一个execute_model可能已sync再调用dummy，idle DP的相应worker入口也要维持同一协议。

## 单槽后台通信与推理线程应用

DueBitsBusWorker持有queue depth=1和一个inflight slot，与处理文件/检测任务的ActionQueue分开。wave-head准备本地bits并handoff上一波auto jobs，提交后立即返回False；False不是配置没变化的最终判定。worker依次做due广播、可选config对象广播、可选dump对象广播，forward可与之重叠。due lane通过broadcast_when_due：due=False直接返回None，due=True才由来源调用build_payload或取payload，再调用group.broadcast_object；该函数不吞collective失败，不能在非来源自行跳过。

end-of-wave的_drain_merged_bus等待结果，再在推理线程apply配置和stash deferred dump；配置变更不会因为submit返回就立刻用于同波已开始的检测。正常drain没有超时界限，not-finished warning按30秒节流；warning是forward未完全隐藏通信的线索，不单独证明网络故障或死锁。

未drain的上一slot会阻止下一submit；processor也在提交前防御性drain。submit/drain/worker result.error会退款相应未执行dump arms并继续抛异常。stop最多join默认2秒，清本地标记不证明正在进行的collective已经停止或其他rank已退场；适配时须保留原框架的协同退出与失败处置。

## 本地digest与follower版本不是同一个判据

本地reload比较文件digest，能发现同mtime但内容变化；mtime更旧可直接跳过。build_config_sync_payload在reload变化或首次同步时发送data，但version仍取mtime浮点数。apply_config_sync_payload的follower只有version!=自身_version才_apply_loaded，未再次比较data内容。

据这条静态路径推导：文件系统时间粒度较粗、两次有效内容修改保持同mtime时，来源可接受新data而已持同version的follower不应用；首次同步恰持同version也需核对各rank实际_data。这里没有复现故障，不声称所有运行都会分歧，也不把mtime数字或来源updated日志当成组内一致性证明。验证应记录来源/接收payload、各rank有效配置和版本，保留实际内容差异。

_last_reload_ts在完成config lane时即推进，data=None也可更新；_initial_broadcast_done会先置True。follower验证失败保留last-known-good，但后续无变化payload未必重发整份data，不能只靠等待一个poll周期宣称已自动追平。

## 配置cascade与状态清理

有效变更依次同步quota、logger、detector与ReportWriter的控制字段。needs_sample_hooks从True变False时purge检测侧Store/stamp、退款并丢未claim auto arms，清IO缓存；已移到deferred的job仍保留本波D2H机会。purge不等于物理KV已释放，也不构成完整runner reset。

本地reload/配置apply失败与collective失败分开处理；前者可保留旧配置，后者不能随意忽略。跨rank一部分成功、一部分回到旧值时，要先保留证据并核对协议，不在单rank重发/重启观测线程来假定修复。

按[配置控制](../../runbooks/runtime/vllm_ascend_runtime_guard_controls.md)确认启动和schema，按[请求生命周期](vllm_ascend_runtime_guard_request_lifecycle.md)对齐采样stamp，按[dump完整性](../../runbooks/validations/vllm_ascend_runtime_guard_dump_incomplete.md)检查实际分片。默认关闭、仅热加载、detector开启和dump开启的开销需分别在目标硬件测量，本文没有NPU或性能A/B结果。
