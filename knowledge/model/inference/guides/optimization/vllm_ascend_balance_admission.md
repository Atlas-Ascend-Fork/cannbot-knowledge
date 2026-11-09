---
type: Guide
title: vLLM Ascend Balance Scheduling：DP 全局准入冻结
description: 解释任一 DP rank 达运行请求上限后的全组新请求冻结，核对配置优先级、EngineCore gather 时机和版本漂移。 补清中英签名差异、local
  active/global running两容量字段、当前pin与Phase2B接缝的适配边界。 说明 CPU tensor 的 item 与 NPU 同步成本的证据边界。
  明确 Balance Scheduling 配对 Native pin 544f182d9f0c9bfe8bd7645525951d5e3692a542 的版本适配入口；独立5df参考不构成该配对兼容性验证。
tags:
- task.optimization
- topic.model_serving
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/balance_schedule_refactor.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_balance_schedule.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_engine_core.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-release-tag.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/balance_schedule_refactor.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-10-29T11:00:26Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
      parallelism:
        all_of:
        - dp
updated_at: '2026-11-02T07:05:01Z'
aliases:
- Balance
- Balance Scheduling
- Balance Scheduling main-verified 544f182d9f0c9bfe8bd7645525951d5e3692a542
---

# vLLM Ascend Balance Scheduling：DP 全局准入冻结


## 目的、范围与前置缺口

目标场景是 PD MIXED 的多 DP 调度，常与 MoE 使用；本策略限制新请求准入，不迁移正在运行的请求，也不强制各 rank 的 running 数相等。设计未给出整项功能的硬件矩阵，保持 draft、空平台。

固定 ceac1a2b 的 release pin 为 v0.32.0。设计中的 v0.24.0/e5588 示例是历史说明；当前 copied schedule 与实际 pin 存在静态差异，启用前必须处理[版本漂移检查](../../runbooks/runtime/vllm_ascend_balance_scheduler_version_drift.md)。文档意图不构成兼容性通过证明。

## 策略和配置

EngineCore 在每个 active step 末 all_gather 各 rank 的 len(running)，下一步 WAITING 准入消费该快照。实现的门是 max(snapshot)==max_num_running_reqs：任一 rank 达上限，全组不再接纳新 WAITING 请求。它不临时降低容量让较少请求的 rank 追平，也不是按 token 数做均衡。

推荐 additional_config.scheduler_config.enable_balance_scheduling。实际解析先取已初始化 AscendConfig.scheduler_config，初始化窗口回退 nested additional_config，再回退 legacy top-level，最后 False；没有环境变量开关兜底。配置校验及 CPP/Dyntra 组合限制须先核对。

## 每步参与不能依赖本地请求

BalanceDPEngineCoreProc 在 super()._has_global_unfinished_reqs 返回后注入 dp_group 并调用 balance_gather；本地请求耗尽、执行 dummy batch 的 rank 仍参与 active iteration。全体 idle 时一致跳过。上游该函数不是每次都发实际 all-reduce，内部有32步节奏，不能把调用点简化成每步必有一次 all-reduce。

gather 若移到 schedule，drained rank 不进入 schedule 而缺席；若移到更早的 _process_engine_step，wave 边界可能有 rank 阻塞 input/future、另一个进入 gather。均可形成 collective 失配，诊断见[波次超时](../../runbooks/runtime/vllm_ascend_balance_wave_collective_timeout.md)。实际 gather 使用 CPU int tensor，不能仅因 .item() 推导一次 NPU→CPU 同步。

## 关闭路径和验收

balance 关闭时 schedule 直接 super().schedule(throttle_prefills)，但 SRF waiting queue 可独立安装。recompute、dynamic-batch、profiling scheduler 显式设置 scheduler_cls 时绕过默认模块名替换，不能据文件已 import 就认定 balance 生效。

当前 EngineCore 入口在 patch_engine_core.py：初始化 AscendConfig，按需装 CPP，优先 Dyntra、再 balance 后调用原入口。代码没有设计样例中的关闭分支恢复语句；同进程复用多配置时需检查实际类，不把文档的 restore 描述当现有保证。

兼容缺口解决后，用不均匀完成、连续请求波次、drained rank、全部 idle、开/关 balance 的同负载测试，记录每步各 rank running 快照、新准入与队列等待、TTFT/TPOT 和吞吐。设置失效、停顿或尾延迟退化时关闭目标策略并以新进程恢复已验证路径。本次未运行上游单测、DP 服务或性能测试。


## 完整中英文对照：设计阶段与当前控制路径

新增核对 balance_schedule_refactor.md 全文562行和 balance_schedule_refactor.po 的69条业务译文。69条msgid均可在英文定位，但中文第58、60条仍描述v0.23双版本签名并集、_SUPER_SCHEDULE_HAS_THROTTLE内省和旧CI通道；对应英文已改成共享签名与直接转发。这两处语义差异不能被字符串匹配掩盖，也不应恢复成新版适配的兼容分支。

固定快照的release pin为v0.32.0、main-verified为544f182d9f0c9bfe8bd7645525951d5e3692a542；本任务Native参考为另一提交5df63a7203cdb9328d824a27b682e77c7b9928be。设计中的v0.24.0/e5588说明、Phase表Done、CPU意图锁和NPU测试计划都不能证明这三个对象已兼容。本批只复读明确源码范围，未重做整个copied schedule的AST/行为等价验证；沿既有版本漂移Runbook继续核验。

### 配置、等待队列与两个容量字段

`_balance_scheduling_enabled` 先读已初始化的AscendConfig.scheduler_config，再读additional_config内的scheduler_config，之后兼容legacy顶层键，最后False；这是已读函数的次序。bool回退不是任意字符串或非法配置的通用校验。新配方使用nested配置，并以完整AscendConfig校验后的值为准。

已读WAITING片段在未抢占且UNPAUSED时进入，先取kv_holding_waiting或waiting；空队列用if not request_queue退出。随后先检查本地len(running)==max_num_active_reqs，再检查全局快照max(balance_queue)==max_num_running_reqs。不要把local active cap与global running cap两个字段简单等同，也不把gate改成临时降低cap来追赶另一个rank。此处只描述所读准入片段，未据此证明整段跳过、回填和回滚逻辑。

### EngineCore钩子与未来接缝

当前入口在patch_engine_core.py，初始化AscendConfig、按需安装profiling patch，优先Dyntra、再balance选择DP类，然后调用原入口；代码没有设计伪代码所说的关闭分支restore。其post_step补丁与完整PP/MTP执行协议也不是同一项证据。单进程切换配置时检查实际类；回退仍以新进程恢复已记录配置为起点。

平台校验允许无kv_transfer_config或kv_role=kv_both，拒绝其他非空KV角色；这解释PD-mixed表述，不能据补丁已导入推断PD分离也被支持。gather依赖每个活跃rank都进入hook，包括dummy路径；hook调用次数和底层实际all-reduce每32步的节奏分开。CPU int tensor上的item不等于已测得NPU拷贝或主机同步成本。设计中的60s RPC报错是来源观察，不是所有部署的固定超时。

Phase2B的_should_stop_admitting_waiting是设计中的后续接缝方案，当前补丁仍保留copied schedule；适配新版框架时先检查实际Native接口，不能按该草图假定接缝存在或整段副本已删除。保持draft和空平台：本批没有获得整项功能的硬件矩阵，也未执行上游单测、DP服务、通信或性能试验。
