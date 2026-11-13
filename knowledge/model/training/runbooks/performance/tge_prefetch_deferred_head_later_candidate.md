---
{
  "type": "Runbook",
  "title": "训练图 prefetch balance——被 lease/预算推迟的恢复单元不得吞掉队头空隙（deferred + later_candidate 守卫）",
  "description": "TGE 训练图估计器为 Kimi 用例排布 FSDP 参数恢复（allgather）与计算通信掩盖，本修复解决被推迟恢复单元吞掉队头空隙的调度饿死问题。",
  "tags": [
    "task.implementation",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 训练图 prefetch balance——被 lease/预算推迟的恢复单元不得吞掉队头空隙（deferred + later_candidate 守卫）

TGE 训练图 balance 模式中，被 lease/预算推迟的大恢复单元会吞掉队头空隙、饿死后续小单元。本卡记录聚焦复现、deferred + later_candidate 守卫修复与估计器时间线验证。

## 适用场景

TensorCentricTrainingGraphEstimator（TGE）balance 模式做 FSDP 参数恢复（allgather）与计算通信掩盖的时间线排布：目标是 layer n 的预取 FSDP allgather 在 layer n-1 执行、并尽可能往 layer n-1 前面放。适用于任何「按 gap 从前往后扫描放置通信/恢复单元、且存在 lease/字节预算准入推迟」的调度器，当大恢复单元被推迟后反而吞掉早期空隙、饿死后续小单元时。

## 触发与观测

触发：用户要求把 balance 模式修改为 layer n 的 FSDP allgather 在 layer n-1 层开始时即可执行。

失败观测（时间线扫描日历 + 用户质疑）：

- 客观信号：逐单元扫描输出（8347.939200 moved=True 等大量单元被移动/推迟的日历）；用户指出「扫描应该从前往后、前面占位算子应被移动」。

## 探针与操作

- 诊断脚本：wrapped apply_timeline_prefetch 打印 layer.2 恢复组的 baseline/release/bytes/gated/depends_on/layer previous 约束，定位「准入/lease 条件统一推迟」。
- 聚焦复现：chain(3) + g1b 构造双恢复单 gap 用例，输出 `START g0 20.0 moved True base 80.0 / START g1 200.0 moved False / START g1b 150 moved True base 220.0`。
- 单测：新增 test_delayed_head_does_not_consume_earlier_gap；全套 `python -m unittest tests.test_prefetch_layer_windows tests.test_prefetch_restore_units tests.test_prefetch_config tests.test_prefetch -v`；`py_compile` + `git diff --check`。

## 机制与判别

机制：timeline_prefetch.py `move_into_gaps` 的最终 diff：

```diff
diff --git a/tge/passes/prefetch/timeline_prefetch.py b/tge/passes/prefetch/timeline_prefetch.py
index ac9e699..b7c4b67 100644
--- a/tge/passes/prefetch/timeline_prefetch.py
+++ b/tge/passes/prefetch/timeline_prefetch.py
@@ -111,6 +111,12 @@ def move_into_gaps(graph, baseline, headroom, *, admission=None, mode="balance",
                 starts[layer_windows[i].previous_compute] if i in layer_windows else records[i].start_us
                 for i in pending)
             pending = [pending[j] for j in order]
+            pending = deque(pending)
+            pending_ready = {
+                i: (starts[layer_windows[i].previous_compute] if i in layer_windows
+                    else records[i].start_us)
+                for i in pending
+            }
         position, cursor, resident, allocation_cursor = 0, 0.0, 0, 0.0
         leases, output = deque(), []
         lease_scope = None
@@ -150,13 +156,25 @@ def move_into_gaps(graph, baseline, headroom, *, admission=None, mode="balance",
         for current in intervals:
             if current[2] in moved:
                 continue
-            while position < len(pending) and records[pending[position]].start_us < cursor:
-                blockers[pending[position]].add("comm_window")
-                position += 1
+            if balanced:
+                while pending and records[pending[0]].start_us < cursor:
+                    blockers[pending.popleft()].add("comm_window")
+            else:
+                while position < len(pending) and records[pending[position]].start_us < cursor:
+                    blockers[pending[position]].add("comm_window")
+                    position += 1
             gap_end = current[0]
-            while position < len(pending) and cursor < gap_end:
+            deferred = []
+            while ((position < len(pending)) if not balanced
+                   else (pending and cursor < gap_end and pending_ready[pending[0]] <= gap_end)):
                 examined += 1
-                i = pending[position]
+                if balanced:
+                    i = pending.popleft()
+                    if records[i].start_us < cursor:
+                        blockers[i].add("comm_window")
+                        continue
+                else:
+                    i = pending[position]
                 duration = records[i].cost.duration_us
                 # 可利用自己的原始通信时段向前平移，但不能跨入其它通信。
                 fit_end = current[1] if balanced and current[2] == i else gap_end
@@ -181,10 +199,17 @@ def move_into_gaps(graph, baseline, headroom, *, admission=None, mode="balance",
                 if size > budget:
                     skipped["buffer_budget"] += 1
                     blockers[i].add("buffer_budget")
-                    position += 1
+                    if not balanced:
+                        position += 1
                     continue
                 window = max((records[ids[n]].end_us for n in windows.get(i, ())), default=0.0)
-                ready_floor = max(window, allocation_cursor)
+                # A balance AllGather is eligible from the previous layer's
+                # compute entry. Keep this explicit in the scan lower bound,
+                # rather than relying only on the eventual ScheduleResult
+                # start gate, so the first feasible Comm gap is selected.
+                layer_entry = (starts[layer_windows[i].previous_compute]
+                               if i in layer_windows else 0.0)
+                ready_floor = max(window, allocation_cursor, layer_entry)
                 if i in layer_windows:
                     members = set(unit.preparations) | {i}
                     hard_ready = max((starts[p] + records[p].cost.duration_us
@@ -227,19 +252,43 @@ def move_into_gaps(graph, baseline, headroom, *, admission=None, mode="balance",
                         placements = {}
                 if fallback:
                     size = unit.copy_nbytes
-                begin = max([cursor, window, allocation_cursor]
+                begin = max([cursor, window, allocation_cursor, layer_entry]
                             + [placements.get(p, starts[p]) + records[p].cost.duration_us
                                for p in hard_parents[i]]
                             + [placements.get(p, starts[p]) + offset for p, offset in gates.get(i, ())])
-                if begin + duration > fit_end or begin >= records[i].start_us:
+                too_late = begin >= records[i].start_us
+                if begin + duration > fit_end or too_late:
                     blockers[i].add("comm_window")
+                    if balanced:
+                        if not too_late:
+                            deferred.append(i)
+                        continue
                     break
                 lease_start = min(placements.values(), default=begin)
                 if not placements:
+                    earliest_begin = begin
                     begin = admission_time(begin, size, scope, rolling)
+                    if balanced:
+                        later_candidate = any(pending_ready[j] <= gap_end for j in pending)
+                    else:
+                        later_candidate = False
+                    if (balanced and later_candidate
+                            and begin > earliest_begin + 1e-6
+                            and begin > cursor + 1e-6):
+                        # A lease or byte-budget delay must not consume the
+                        # earlier part of this gap. Keep the unit pending and
+                        # let later restores use the gap before its delayed
+                        # admission time.
+                        deferred.append(i)
+                        continue
                     lease_start = begin
-                if begin + duration > fit_end or begin >= records[i].start_us:
+                too_late = begin >= records[i].start_us
+                if begin + duration > fit_end or too_late:
                     blockers[i].add("comm_window")
+                    if balanced:
+                        if not too_late:
+                            deferred.append(i)
+                        continue
                     break
                 release(lease_start)
                 for node, start in placements.items():
@@ -267,7 +316,12 @@ def move_into_gaps(graph, baseline, headroom, *, admission=None, mode="balance",
                 lease_scope = scope
                 lease_entry = layer_windows[i].compute if i in layer_windows else None
                 cursor = begin + duration
-                position += 1
+                if not balanced:
+                    position += 1
+            if balanced:
+                # Preserve the original layer-window order across gaps while
+                # allowing a fitting later restore to bypass an oversized head.
+                pending.extendleft(reversed(deferred))
             if current[2] not in moved:
                 output.append(current)
                 cursor = current[1]
```

判别要点：

- 修复为 timeline_prefetch.py move_into_gaps：pending 改 deque 并维护 pending_ready（前一层入口时间）；恢复单元被 lease/预算推迟且存在 pending_ready[j] <= gap_end 的后续候选时（later_candidate 守卫）进 deferred 队列，让后面的恢复使用更早空隙，gap 结束后 pending.extendleft(reversed(deferred)) 保持层窗口原序。
- ready_floor 显式纳入 layer_entry（前一层的 compute 入口）：balance AllGather 从上一层的计算入口即可参与，扫描下界不再只依赖 ScheduleResult start gate，保证选中第一个可行 Comm gap。
- 行为判别（#349 聚焦复现）：g1b（更小的恢复）先放进 gap，g1（被推迟的队头）后放。

## 验证信号

- 事件锚点：（修复说明）、（timeline.json 18952950 字节落盘）。
- 验证层级：cpu_reference（单测）+ TGE 估计器对 Kimi 用例完整跑通生成 timeline（估计器口径的端到端，非 NPU 实测）。Train: 37929 nodes, 21432.243119 ms；Memory fits=True。

## 适用与失效边界

- 仅适用 balance 模式（balanced 分支）；非 balance 路径保留原 position 扫描行为。
- deferred 重排保持「层窗口原序 + 允许放得下的更小恢复越过超大队头」：若业务要求严格 FIFO 不可越过，此行为变化需要另行评估。
- later_candidate 判定基于 pending_ready（前一层入口时间），仅对「被 lease/预算推迟」的队头生效；`too_late`（begin >= 原始 start）的单元仍按 comm_window 拒绝。
- 验证为估计器时间线（模拟口径）；NPU 实测的掩盖收益不在本候选范围。
