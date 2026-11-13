---
{
  "type": "Runbook",
  "title": "训练多 rank SIGKILL 时核对宿主与 cgroup 的 OOM 记录",
  "description": "来源多 rank 收到 SIGKILL、没有 traceback，宿主 oom_kill 与容器 OOM 计数为零。这只说明所检查计数未记录 OOM，不能排除应用先失败后整组清理、调度器终止或外部信号。",
  "tags": [
    "task.debugging",
    "topic.parallelism"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 训练多 rank SIGKILL 时核对宿主与 cgroup 的 OOM 记录

## 适用场景

分布式训练多个 rank 同时 exitcode=-9，框架汇总 SIGKILL 但缺少 Python traceback。

## 触发与观测

来源 16 个 local rank 的训练作业中，多个 rank 收到 Signal 9。排查时宿主 `/proc/vmstat` 的 oom_kill=0，所查容器 cgroup memory.events 没有 OOM 计数，memory.failcnt=0。

## 探针与操作

```
echo "=== host vmstat oom ==="; grep -E "^oom_kill" /proc/vmstat; echo "=== container cgroup ==="; docker inspect -f '{{.State.Pid}}' jzw_dsv4; PID=$(docker inspect -f '{{.State.Pid}}' jzw_dsv4); cat /proc/$PID/cgroup; echo "=== memory.events ==="; CG=$(cat /proc/$PID/cgroup | sed 's/^0:://'); echo "$CG"; cat "/sys/fs/cgroup${CG}/memory.events" 2>/dev/null; cat "/sys/fs/cgroup${CG}/memory.max" 2>/dev/null; cat "/sys/fs/cgroup${CG}/memory.current" 2>/dev/null
```

同时核对采集时间、实际 cgroup 路径、父进程/调度器日志及最早失败 rank。计数器属于特定环境与时间窗口，不能用一次读数代替完整事件历史。

## 机制与判别

这些记录降低了“所查内核/cgroup OOM killer 触发”的可能性，但 SIGKILL 不提供发信者身份。应用异常触发上层清理、作业管理器策略、用户/外部进程发信号等方向仍未排除。没有 traceback 也不证明代码未发生更早的错误。

## 验证信号

采用信号只有 SIGKILL 现象及 OOM 计数检查。其他用户 pkill 误伤或复跑恢复的结论未进入本卡采用证据。

## 适用与失效边界

本卡是取证分流，不是 OOM、代码错误或外部误杀的最终定案。补齐时间对齐、信号来源与父进程/调度器记录后才能归因；没有修复后的训练验证。
