---
{
  "type": "Runbook",
  "title": "TorchNPU 虚拟优化器 AclrtHostRegister 失败：每 moment tensor 单独注册不可连续，改每进程单 arena 一次注册",
  "description": "环境/任务：Ascend 950 单机多卡，torchtitan-npu DeepSeek-V4 Flash（24.6B 主干），通用 Virtual Optimizer（Adam 二阶状态 Host 交换，`empty_with_swapped_memory()` 路径），容器 `memlock` 名义 unlimited、Host 内存 700+ GiB 可用。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# TorchNPU 虚拟优化器 AclrtHostRegister 失败：每 moment tensor 单独注册不可连续，改每进程单 arena 一次注册

## 适用场景

- 平台范围依据：source 0 seq 90的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

- 环境/任务：Ascend 950 单机多卡，torchtitan-npu DeepSeek-V4 Flash（24.6B 主干），通用 Virtual Optimizer（Adam 二阶状态 Host 交换，`empty_with_swapped_memory()` 路径），容器 `memlock` 名义 unlimited、Host 内存 700+ GiB 可用。

## 触发与观测

- Flash 基线完成模型构建、前向和反向后，第一次 optimizer step 失败：通用 Virtual Optimizer 为 Adam 二阶状态申请 swap memory 时，四个 rank 都收到 `AclrtHostRegister failed`（source 0 seq 215）——计算链路已走通到反向结束，失败在优化器状态落 Host。

## 探针与操作

1. 容量排除（source 0 seq 429、455）：单进程至少可注册 27 GiB、单 rank 40 GiB 成功——排除很低的固定配额；Flash 每 rank AdamW 两份状态约 50.9 GiB，故障更像 4 rank 并发注册接近驱动的全局 Host 映射上限，而非单进程限制。
2. 关键探针（source 0 seq 1286 逐字）：同一进程第一次 `empty_with_swapped_memory()` 成功、第二次即失败——哪怕每次只有 4 KiB、Host 还有 700+ GiB、`memlock=unlimited`。因此不是容量问题，而是当前 TorchNPU 实现「每个 moment tensor 单独注册」与运行时注册约束不兼容。
3. 修复（source 0 seq 1286）：每个 rank 只注册一个大块 swap arena，所有 `exp_avg`/`exp_avg_sq` 分配互不重叠的 view；先小模型验证 view 能被 fused AdamW 正确更新。

## 机制与判别

- 机制：TorchNPU 的 swapped memory 实现按 tensor 粒度调用 Host 注册；同进程第二次注册即失败（与注册大小无关）→ 逐 tensor 注册方案在该 TorchNPU/驱动组合上不可用（source 0 seq 1286）。
- 判别：容量探针（27/40 GiB 单进程成功）排除 ulimit/memlock 与单进程配额；4 KiB 二次失败排除容量与并发上限两种解释，锁定「注册次数」约束（source 0 seq 429、455、1286）。
- 旁证：未修改的上游同样复现 `AclrtHostRegister failed`，确认不由 Engram 接入引入（摘要级，同会话另一分片）。

## 验证信号

- tool_observed：4 rank 在首次 optimizer step 的 `AclrtHostRegister failed`（source 0 seq 215）。
- tool_observed：单进程 27 GiB / 单 rank 40 GiB 注册成功（source 0 seq 429、455）。
- tool_observed：第二次 `empty_with_swapped_memory()` 4 KiB 即失败（source 0 seq 1286）。
- tool_observed：单 arena 方案通过 8 rank、两种 dtype、fused AdamW 连续两步验证；8 个进程各只做一次 Host 注册，参数和 step 均正常更新（source 0 seq 1383）。

## 适用与失效边界

- 适用：TorchNPU 虚拟优化器/Host swap 在多卡训练中 `AclrtHostRegister failed` 的分诊与绕过（单 arena + view 分配）；判别顺序：单进程容量探针 → 同进程二次注册探针 → 注册次数归因。
- 失效/限制：arena 首次清零存在长尾（EP4 大 arena 约 9 分钟，摘要级）；完整 256-expert 规模（2843 亿主干）单机 8 卡不可行，验证为 8 卡缩放规模（source 0 seq 1383）；TorchNPU 修复逐 tensor 注册后本卡绕过方案失效但判别方法仍适用。

## 附：断言存档

- TorchNPU 虚拟优化器 AclrtHostRegister failed：同进程第二次 empty_with_swapped_memory() 即使 4 KiB 也失败（memlock unlimited、Host 700+GiB），根因是每 moment tensor 单独注册；改为每 rank 单个大块 swap arena 一次注册+exp_avg/exp_avg_sq 互不重叠 view，8 rank×2 dtype×fused AdamW 两步验证通过

```text
可行修复是每个 rank 只注册一个大块 swap arena，再给所有 `exp_avg/exp_avg_sq` 分配互不重叠的 view
```
