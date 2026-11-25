---
{
  "type": "Runbook",
  "title": "daVinci-MagiHuman SR OOM 后续：队列缺省值改为1，仅保留至3/5的中断返回",
  "description": "记录脚本增加TASK_QUEUE_ENABLE缺省值1后的不完整运行；未核验最终生效值，返回至3/5并中断，不证明完成出片、正常退出或碎片化根因。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# daVinci-MagiHuman SR OOM 后续：队列缺省值改为1，仅保留至3/5的中断返回

## 适用场景

- 模型：daVinci-MagiHuman sr_1080p，448×256→1920×1088、5步SR，单卡NPU、CPU offload（resident ratio 0.35、HEURISTIC），来源记录CANN 8.5.1。
- 未确认具体Atlas产品，不以61.28 GiB容量判型。
- 这是[启动对照诊断入口](opparammaker_memory_npuworkspaceallocator_allocate_capacity_reduce.md)的后续会话。前卡保留直接torchrun的完整运行，本卡只记录包装路径的队列缺省值试验。

## 触发与观测

本会话10:30的首步swiglu7失败（source 0 seq154）：

```text
[2026-06-22 10:29:30,825 - INFO] [Rank 0] Before super resolution evaluation GPU 0 memory allocated: 2.19 GB, max_allocated: 32.16 GB, reserved: 32.61 GB, max_reserved: 32.61 GB
0%|          | 0/5 [00:00<?, ?it/s][rank0]:[E622 10:30:09.326994291 OpParamMaker.cpp:454] NPU out of memory. NPUWorkspaceAllocator tried to allocate 2.72 GiB(NPU 0; 61.28 GiB total capacity; 2.21 GiB free). If you want to reduce memory usage, take a try to set the environment variable TASK_QUEUE_ENABLE=1.
[ERROR] ... ERR00006 PTA memory error
Exception raised from malloc at ../torch_npu/csrc/core/npu/NPUWorkspaceAllocator.cpp:444
```

2.72 GiB申请高于失败时报告的2.21 GiB空闲。SR前2.19 GB allocated和32.16 GB峰值不能证明失败时空闲充足，也不能直接锁定碎片化。

## 探针与操作

- source 0 seq89/90读取此前直接torchrun的T2V日志；它与前卡seq239/240是同名 `log_sr_1080p_torchrun_20260622_100622.log` 的复引，不是本会话新完成的一次运行。
- source 0 seq42的完整 `sample_video.py` 先调用 `initialize_infra()` 再进入 `entry.main`，不能宣称与直接entry调用完全等价。更换入口后仍有seq154的OOM，尚未完成对所有初始化副作用的控制。
- seq24的完整mm_function.sh中 `mm_setup_env()` 将队列缺省值设为2，随后YAML env_vars还能覆盖环境；这是脚本设置顺序，不等于读取到了每次失败进程的最终有效值。
- seq164的编辑在 `infer_sr_1080p.sh` 中增加：

```bash
export TASK_QUEUE_ENABLE="${TASK_QUEUE_ENABLE:-1}"
```

该写法只在变量未设置或为空时采用1，保留已有非空值；还须检查后续YAML/启动器覆盖。修改保持mm_launch包装调用路径，但来源未打印本次最终生效的队列值。

## 机制与判别

- 错误文本建议尝试TASK_QUEUE_ENABLE=1，这是排查线索，不是碎片化或队列机制已经证实的根因。
- 添加缺省值后的后一次调用保留至3/5进度，说明该返回文本中未在原首步位置再次记录OOM；没有完成全程运行，也没有控制所有环境变量及采集分配器时间线。
- 不能只凭编辑文本和部分进度证明有效值一定为1，或证明队列模式以某种机制消除了OOM。

## 验证信号

- source 0 seq169的调用配置上限为300000ms；这只是调用参数，不是已测得运行300秒或中断原因的证据。
- seq170保留的执行返回含3/5进度（52.16/37.53/32.30 s/it）及 `User aborted the command`。退出码为空，归一化为unknown并带 `ambiguous_exit_status`；不把completed生命周期标记当退出成功。
- 仅采用这段不完整运行记录；没有正常退出、5/5和最终视频验收，也没有完成设备功能或端到端正确性验证。
- 前卡与本卡重复读取的直接T2V成功不能填补这里的验证缺口。两张卡相同的OOM数字属于同一问题链；不同时间的运行及重复日志引用分别记账，不当独立根因佐证。

## 适用与失效边界

- 适用于该包装脚本的队列缺省值、外部继承值和YAML覆盖排查；其余版本须重新核对设置顺序。
- 后续验证应记录有效队列值、完整退出状态、5步及输出验收，并采集同一时点的容量数据。若继续OOM，应按容量和驻留占用排查，不直接归为碎片化。
- 缺省值写法允许显式传2作后续对照，但来源没有完成该单变量验证，也未测吞吐或质量影响。

## 附：断言存档

- 10:30的首步OOM报告2.72 GiB申请、2.21 GiB空闲；前置快照不代表失败时容量。
- 添加缺省值1后仅保留至3/5且标明用户中断的unknown返回，不声称有效值已确认、正常完成、出片或根因证实。

```text
"newString": "export CPU_OFFLOAD=\"${CPU_OFFLOAD:-true}\"\nexport SR2_1080=\"${SR2_1080:-true}\"\nexport MAGI_COMPILE_COMPILE_MODE=\"NONE\"\nexport TORCH_COMPILE_DISABLE=\"1\"\nexport TASK_QUEUE_ENABLE=\"${TASK_QUEUE_ENABLE:-1}\"\nexport MAGI_COMPILE_OFFLOAD_CONFIG='{\"model_cpu_offload\":true,\"gpu_resident_weight_ratio\":0.35,\"offload_policy\":\"HEURISTIC\"}'"
```
