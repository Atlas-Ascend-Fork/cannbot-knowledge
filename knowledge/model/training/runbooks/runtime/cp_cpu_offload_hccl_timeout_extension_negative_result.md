---
type: Runbook
title: CP 与 CPU offload 排障：延长 HCCL 超时仍失败
description: 训练日志在 300s 与 600s 超时设置下都出现同序号单元素 ALLREDUCE 失败，不能把延长超时或首步成功当作多步训练修复。
tags:
- task.debugging
- topic.parallelism
- topic.memory
status: draft
sources: []
created_at: '2026-10-29T07:47:19Z'
updated_at: "2026-10-29T08:06:03Z"
platforms:
- '950'
---

# CP 与 CPU offload 排障：延长 HCCL 超时仍失败

## 适用场景

torchtitan-npu 的 CPU offload 与上下文并行 CP 联用排障，来源任务要求四卡、CP=2，并持续训练多个 step。用户指定的机器称为 A5，对应本仓 `950` 平台；本卡未独立查询设备型号，具体依赖版本与各次运行完整参数尚未冻结，因此保持 draft。

本卡记录“延长超时仍失败”的边界，不给出已修复配方；不据两次运行推断完整工作负载相同。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_4}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

来源工具读取训练日志，先观测到单元素 ALLREDUCE 超时：

```text
WorkHCCL(SeqNum=1631, OpType=ALLREDUCE, NumelIn=1, NumelOut=1, Timeout(ms)=300000) ran for 300277 milliseconds before timing out.
```

后续日志中，ProcessGroup 超时已被设置为 `0:10:00`，日志仍返回相同 SeqNum/OpType/Numel 字段的失败记录：

```text
WorkHCCL(SeqNum=1631, OpType=ALLREDUCE, NumelIn=1, NumelOut=1, Timeout(ms)=600000) ran for 600733 milliseconds before timing out.
```

## 探针与操作

原轨迹中执行的日志提取命令如下，只读取日志，不触发训练。使用时定位本次任务的实际日志文件；来源文件名不是通用复现路径。

```bash
grep -n "Watchdog\|timeout\|ALLREDUCE\|ALLGATHER\|aclnn\|Pinned\|Error\|terminate" ${LOCAL_PATH_1} 2>/dev/null | tail -8
```

以下是来源轨迹中的两组完整配置块和启动命令，保留原文；前提是已进入对应 torchtitan-npu checkout 并加载来源任务的环境。私有环境加载路径、远程账号和进程清理操作未写入本卡。这些是历史失败尝试，不能直接当作修复命令。

第一组指定四卡、CP=2、DP_SHARD=2、EP=4，目标 2 步，初始化超时参数为 300 秒：

```bash
export ASCEND_RT_VISIBLE_DEVICES=4,5,6,7
export NGPU=4
export CP=2
export DP_SHARD=2
export CONFIG=deepseek_v4_1_flash_40layers_8experts_text
# Avoid port 16666 which is stuck from previous crashed runs
export HCCL_NPU_SOCKET_PORT_RANGE=18000-19000
```

```bash
bash examples/deepseek_v4_1/debug/deepseek_v4_1_flash_8p_cpt_4k_a5.sh \
    --parallelism.expert-parallel-degree 4 \
    --training.enable-cpu-offload \
    --training.steps 2 \
    --extension.quantization.no-enable-quantized-training \
    --comm.init-timeout-seconds 300 \
    --dump-folder ${LOCAL_PATH_2} \
    2>&1 | tee ${LOCAL_PATH_3}
```

第二组仍为四卡、CP=2、DP_SHARD=2、EP=4，但目标改为 5 步，初始化超时参数为 600 秒；此次部署还替换了 grad_accum.py 与 grad_clip.py，不能视为只改 timeout 的受控对照：

```bash
export ASCEND_RT_VISIBLE_DEVICES=4,5,6,7
export NGPU=4
export CP=2
export DP_SHARD=2
export CONFIG=deepseek_v4_1_flash_40layers_8experts_text
export HCCL_NPU_SOCKET_PORT_RANGE=18000-19000
```

```bash
bash examples/deepseek_v4_1/debug/deepseek_v4_1_flash_8p_cpt_4k_a5.sh \
    --parallelism.expert-parallel-degree 4 \
    --training.enable-cpu-offload \
    --training.steps 5 \
    --extension.quantization.no-enable-quantized-training \
    --comm.init-timeout-seconds 600 \
    --dump-folder ${LOCAL_PATH_4} \
    2>&1 | tee ${LOCAL_PATH_1}
```

工具返回了启动和重试标记，随后日志读取给出前述 watchdog 失败。启动确认不等于训练完成；同名日志可能被重试覆盖，来源中未做 PID/seed 与完整版本绑定。

把训练 step、ProcessGroup 的 timeout 设置和 watchdog 的 SeqNum/OpType/Numel 关联阅读。还需检查所有参与 rank 的日志与最终完成状态；只读取 rank0 或最后一行不足以复原所有通信依赖。这是后续排查要求，本次没有重跑训练。

## 机制与判别

两份失败日志具有相同 SeqNum/OpType/Numel 字段；各自的 300000ms 与 600000ms 超时均未给出多步训练完成证据。

两次超时数字只是失败观测，不能作为“把超时调大即可修复”的依据。日志中的 `step: 1` 和模型初始化成功也不等于后续多个 step 已完成。多个补丁和运行条件在轨迹中发生变化，因此不能把差异单点归因于某个 stream、event、优化器或 CP mesh。

## 验证信号

- 工具读取的第一份日志返回 `Timeout(ms)=300000` 的 ALLREDUCE watchdog 失败。（来源平台：用户指定 A5/950，未独立复核型号；证据等级：tool_observed；单条开发轨迹内的既有日志）
- 后续工具读取同时返回 `0:10:00` 超时设置、`Timeout(ms)=600000` 的同字段 watchdog 失败记录以及最后的 step 1 记录；没有完成训练的证据。（来源平台：用户指定 A5/950，未独立复核型号；证据等级：tool_observed；单条开发轨迹内的既有日志）

## 适用与失效边界

跨运行相同的 SeqNum、OpType 和 Numel 不能证明通信组、参与 rank 或调用位置是同一个 collective。`--comm.init-timeout-seconds` 的启动值与后续 ProcessGroup timeout 记录也分别保留，不把两者视为未经核实的唯一设置链。

只记录该训练开发过程的失败边界。`SeqNum=1631` 是来源运行的定位标识，不是其他版本固定会失败的 collective 序号。不能据此认定所有 CPU offload+CP 配置均不可用，也不能确认设备级循环依赖或具体通信域是根因。

停止继续把超时放宽当作验收；恢复任务目标要求的多 step 结果、各 rank 完成状态与精度/损失检查后，才能报告修复。后续需要冻结模型规模、专家与并行配置、代码版本及流事件时序，采用一次只改变一个条件的复测。此前本卡保持失败路线记录，不提供尚未验证的修法。
