---
{
  "type": "Runbook",
  "title": "多卡并行视频生成的卡分配：i % num_workers 会双占卡致 OOM，须 worker pool 每卡单任务 + 空闲卡补跑",
  "description": "Ascend NPU 多卡（本例 61.27 GiB×8）上做视频生成基线/评测批量生成（autotune-evaluator 的 L1 baseline：5 个 prompt 并行生成，每进程以 `ASCEND_RT_VISIBLE_DEVICES=<id>` 绑定单卡跑 HunyuanVideo/Wan2.1 级别的大模型）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# 多卡并行视频生成的卡分配：i % num_workers 会双占卡致 OOM，须 worker pool 每卡单任务 + 空闲卡补跑

## 适用场景

Ascend NPU 多卡（本例 61.27 GiB×8）上做视频生成基线/评测批量生成（autotune-evaluator 的 L1 baseline：5 个 prompt 并行生成，每进程以 `ASCEND_RT_VISIBLE_DEVICES=<id>` 绑定单卡跑 HunyuanVideo/Wan2.1 级别的大模型）。

## 触发与观测

- 触发（source 0 seq 60，用户报告）：`发现你 0 卡跑了两个 task`。
- 观测一（source 0 seq 34，逐字）：`i % num_workers` 分配使 5 任务 4 卡出现
```
[launched] idx0_seed61724 → ASCEND_RT_VISIBLE_DEVICES=0
...
[launched] idx25_seed15082 → ASCEND_RT_VISIBLE_DEVICES=0
```
- 观测二（source 0 seq 354，逐字）：卡 0 上两任务 17-20s 内先后 OOM，其余卡成功：
```
RuntimeError: NPU out of memory. Tried to allocate 56.00 MiB (NPU 0; 61.27 GiB total capacity; 19.05 GiB already allocated; 19.05 GiB current active; 13.55 MiB free; 19.60 GiB reserved in total by PyTorch)
[FAILED]   idx0_seed61724 (17.0s) exit=1
[FAILED]   idx25_seed15082 (20.2s) exit=1
[done]     idx2_seed52079 (244.2s)
[done]     idx1_seed75524 (249.5s)
[done]     idx24_seed17833 (250.8s)
```
  本例卡 0 还有 ~19GB 残留进程占用（npu-smi 显示 45GB），双占放大了失败，但单任务峰值 35.6GB 下双占本身就超 61GB。

## 探针与操作

- 分配机制修复（source 0 seq 65-67）：把 `i % num_workers` 的"启动即分卡"改为 **worker pool**：每张卡一个工作线程，从队列取任务，卡空出来才派下一个——任意时刻每卡至多一个任务。
- 故障恢复：失败的 2 个任务用空闲卡补跑（`ASCEND_RT_VISIBLE_DEVICES=4/5 ...` 前缀指定，source 0 seq 359），5 个 L1 视频最终齐全（source 0 seq 366）。
- 诊断探针：`npu-smi info` 看每卡 HBM 占用与残留进程；`ps aux | grep generate.py` 确认父/子进程；注意后台父进程 exit 0 ≠ 子进程全部结束（stdout=PIPE + `&` 会吞掉输出且通知提前，source 0 seq 41）。

## 机制与判别

- 机制：`ASCEND_RT_VISIBLE_DEVICES` 只做可见性裁剪，同一物理卡被两个进程同时绑定时各自独立分配 HBM；HunyuanVideo 单任务峰值 ~35.6GB（source 0 seq 435），双占必然 OOM。`i % num_workers` 在任务数 > 卡数时把溢出任务立即压到卡 0，而不是排队。
- 判别：失败任务全部落在被双占的卡 0、成功任务全在独占卡 1-3 —— 卡维度完美区分；补跑到空闲卡后同命令成功。

## 验证信号

- 设备级（等级：设备功能观测，单次批量）：launched 日志 + OOM/成功分卡统计（source 0 seq 34/354）；补跑后 5 视频齐全（source 0 seq 366）。
- worker pool 版本随后用于 HunyuanVideo L1 生成（"卡 1-4，worker pool 模式，不会有同卡双任务"，source 0 seq 346），该批次失败仅因卡 0 残留进程（非双占），机制成立。
- 局限：未做受控 A/B（同批任务新旧调度各跑一次）；OOM 阈值依赖单任务峰值显存。

## 适用与失效边界

- 适用：单卡放不下两个实例的大模型批量推理/生成（视频 DiT、LLM 离线批生成）；调度原则=每卡一队列位 + `ASCEND_RT_VISIBLE_DEVICES` 显式绑定 + 失败任务按空闲卡补跑。
- 失效/不覆盖：小模型单卡多实例可显式超卖（不在本判别内）；残留进程清理（根因是环境未回收，本轨迹用换卡绕过）；GPU/多机场景未覆盖。

## 附：断言存档

- 多卡并行大模型批量生成的卡分配不能用 i % num_workers（任务数>卡数时溢出任务立即双占卡 0）：ASCEND_RT_VISIBLE_DEVICES 只裁剪可见性，两进程绑同卡各自独立分配 HBM，HunyuanVideo 单任务峰值 ~35.6GB 下双占 61.27GB 卡必 OOM（本例卡 0 双任务 17-20s 内先后 OOM，独占卡 1-3 的 3 任务全部成功，~245-251s 完成）；正确调度是 worker pool：每卡一工作线程从队列取任务，任意时刻每卡至多一个任务。

```text
RuntimeError: NPU out of memory. Tried to allocate 56.00 MiB (NPU 0; 61.27 GiB total capacity; 19.05 GiB already allocated; 19.05 GiB current active; 13.55 MiB free; 19.60 GiB reserved in total by PyTorch) If reserved memory is >> allocated memory try setting max_split_size_mb to avoid fragmentation.
[FAILED]   idx0_seed61724 (17.0s) exit=1
```
