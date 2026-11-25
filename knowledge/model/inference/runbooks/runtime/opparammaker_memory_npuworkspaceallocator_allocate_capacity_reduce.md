---
{
  "type": "Runbook",
  "title": "daVinci-MagiHuman SR OOM 启动对照：直接 torchrun 完成，mm_launch 包装失败原因未定",
  "description": "区分直接 torchrun 的完整 SR 运行与包装启动首步 OOM；失败后 HBM 读数不能反证失败瞬间容量不足，后续队列缺省值调整仅有3/5进度记录。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:58:23Z",
  "platforms": []
}
---

# daVinci-MagiHuman SR OOM 启动对照：直接 torchrun 完成，mm_launch 包装失败原因未定

## 适用场景

- 模型/任务：daVinci-MagiHuman 15B Single-Stream DiT 的 `sr_1080p` 超分推理，448×256基础分辨率、1920×1088超分、5步SR，CPU offload开启（gpu_resident_weight_ratio=0.35、HEURISTIC）。
- 平台：单卡NPU；错误报告总容量61.28 GiB，但容量不用于判型，本来源未确认具体Atlas产品和完整软件版本。
- 包装启动：`infer_sr_1080p.sh` 经 mm_launch/mm_function.sh 调度；本次失败的启动头明确为 `launcher: torchrun`，不是 accelerate launch（source 0 seq 121）。
- 直接启动：torchrun 直调 `inference/pipeline/entry.py` 的对照运行。两条路径虽都使用torchrun，入口、参数传递与环境设置仍须分别核对。

本卡是启动对照的诊断入口。[后续队列缺省值调整记录](opparammaker_memory_npuworkspaceallocator_allocate_capacity_reduce_2.md)保留10:30失败及之后仅到3/5的返回。两卡属于同一问题链，各自source 0是不同会话；引用同名日志不增加运行次数，也不能把相同错误签名当作独立根因证据。

## 触发与观测

较早会话的包装启动失败记录：

- source 0 seq 121，09:40左右的失败：

```text
[2026-06-22 09:39:39,324 - INFO] [Rank 0] Before super resolution evaluation GPU 0 memory allocated: 2.19 GB, max_allocated: 32.16 GB, reserved: 32.61 GB, max_reserved: 32.61 GB
[rank0]:[E622 09:40:08.251874251 OpParamMaker.cpp:454] NPU out of memory. NPUWorkspaceAllocator tried to allocate 2.72 GiB(NPU 0; 61.28 GiB total capacity; 2.21 GiB free). If you want to reduce memory usage, take a try to set the environment variable TASK_QUEUE_ENABLE=1.
```

- 撤销SR2_1080后，seq205/206在09:55:05再报OOM，09:55:24报告进程失败退出；seq228/229加回该设置后仍失败。这里只说明本会话的几次切换未消除失败，不推广为该变量在所有负载下都无影响。
- seq211/212随后才读取npu-smi，显示约5733/65536 MB，先前失败PID已不在进程表。该采样发生在失败之后，不能用它断言失败瞬间物理显存充足或已证实分配器保留/碎片化根因。

按OOM日志的当时口径，2.72 GiB申请已超过2.21 GiB空闲。SR前的2.19 GB allocated与32.16 GB历史峰值既不是失败瞬间的空闲，也不是完整HBM占用账。

## 探针与操作

1. 对照本来源的三次包装启动失败，保留各自时刻和日志；不因数值相同就合并成同一次运行，也不把跨卡重复读取同一日志当新的复现。
2. source 0 seq182/183仅保留6/18历史日志的SR 5/5及后处理片段，未核对当时启动方式；助手所写的工具description不能代替启动头或调用证据。也不能由本会话有限次失败外推包装启动必然OOM。
3. 读取直接torchrun对照：TI2V运行见seq217/218；T2V的 `log_sr_1080p_torchrun_20260622_100622.log` 见seq239/240，输出文件列表见seq246。
4. 逐项核对实际入口、输入类型、完整参数和有效环境值。T2V与TI2V不能当相同负载的重复性能试验；相同的几项SR前内存快照也不能证明两进程处于相同内存状态。
5. 若继续试验队列模式，按[后续记录](opparammaker_memory_npuworkspaceallocator_allocate_capacity_reduce_2.md)检查缺省值、外部继承值和YAML覆盖，另行采集失败瞬间的容量及进程时间线。

## 机制与判别

- 包装启动在工作区申请时失败；当时的2.21 GiB空闲不足以满足2.72 GiB申请。其他时点的npu-smi与SR前PyTorch快照不能排除容量不足，也不能区分碎片化、生命周期或并发调度的具体作用。
- 两条启动路径都含torchrun；该对照提供继续检查入口、环境与配置的线索，不是“torchrun对accelerate”或严格单变量因果实验。
- SR2_1080切换后的几次运行仍失败，不据此推导其他变量或永久根因已经排除。
- 后续队列缺省值调整只留下3/5的中断返回，不得借本卡直接启动的完整运行替它补上5/5或出片验证。

## 验证信号

- 本来源seq121/206/229保留包装启动的失败记录。
- seq217/218保留直接torchrun TI2V的5/5进度；seq239/240保留直接T2V运行日志，seq246列出相应T2V/TI2V输出文件。两种输入分别记录，不作重复性能统计或质量等价声明。
- 后续卡source 0 seq89/90读取的同名 `log_sr_1080p_torchrun_20260622_100622.log` 与本卡seq239/240对应同一直接T2V运行，不能再计一次成功复现。
- 本卡09:40与后续10:30的OOM保留了相同分配数值，但时刻/PID不同；09:55另有失败栈及退出记录，不补写该片段未保留的分配数值。不因数字相同声称是同一次失败或独立硬件佐证。

## 适用与失效边界

- 适用于该模型SR阶段OOM的启动路径、有效环境和容量时间线核对；最终根因未定。
- 直接启动在所记录案例完成，不保证其他输入、版本和显存占用下可绕开OOM。若它也失败，仍需检查容量及模型/环境，不能反向证明启动路径无关。
- 本卡没有测试TASK_QUEUE_ENABLE；队列缺省值变更和3/5边界仅采用后续卡自己的来源，不跨会话升级验证层次。

## 附：断言存档

- 失败当刻申请2.72 GiB、报告空闲2.21 GiB；SR前快照和失败后npu-smi不证明失败当时有足够可分配空间。
- 本卡直接torchrun的完成记录与后续队列调整的3/5中断分别成立；同名成功日志的复引只计同一次运行。
