---
{
  "type": "Runbook",
  "title": "prefill 选批 KV 分配失败时 while+continue 无限自旋",
  "description": "cann-recipes-infer offline/online 推理在 KV 池耗尽或碎片化时 prefill 选批卡死（进程存活、无输出、无报错、无 \"phase stalled\" 日志）的排查场景。",
  "tags": [
    "task.debugging",
    "topic.kv_cache"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# prefill 选批 KV 分配失败时 while+continue 无限自旋

## 适用场景
cann-recipes-infer offline/online 推理在 KV 池耗尽或碎片化时 prefill 选批卡死（进程存活、无输出、无报错、无 "phase stalled" 日志）的排查场景。

## 触发与观测
offline 推理 prefill 选批在 KV 分配失败时进程不退出、不报错、原地空转；faulthandler 主线程栈确认卡在 scheduler.py:392 的 _schedule_prefill_batch。

## 探针与操作
1) faulthandler 抓主线程栈定位自旋帧。
2) 读 scheduler.py _schedule_prefill_batch 行 390-411 的 while 循环（见工件）。

## 机制与判别
机制：见结论原文与下方工件——_schedule_prefill_batch 的 while 循环内取队头不移除，allocate_slots 失败时 continue 回到循环头，队头与池状态都不变导致永久重复。

机制片段：
```
while self.waiting_queue:
24:     request = self.waiting_queue[0]        # 取队头，不移除
25:     ...
26:     if engine.kvcache_manager and not engine.kvcache_manager.allocate_slots(...):
27:         if enable_offline_cp:
28:             raise RuntimeError(...)
29:         continue                            # ← 回到循环头，队头还是它
30:     selected.append(self.waiting_queue.popleft())   # 成功才移除
```

## 验证信号
本轨迹为源码读取与 git show 核对（无运行时复现）；自旋点定位依据 faulthandler 主线程栈（卡在 scheduler.py:392）。

## 适用与失效边界
适用于 cann-recipes-infer scheduler 的 prefill 选批路径；不推荐"真跳过"（pop 暂存 + 放回队头）方案——与 request_offset/cache-owner 分片逻辑有漂移风险。修复与回归单测未在本轨迹内执行。

## 结论与证据边界
- 观测：自旋点在 executor/core/scheduler/scheduler.py 的 _schedule_prefill_batch（行 390-411）：while 循环内取队头不移除，allocate_slots 失败时 continue 回到循环头，队头与池状态都不变导致永久重复；faulthandler 主线程栈确认卡在 scheduler.py:392
