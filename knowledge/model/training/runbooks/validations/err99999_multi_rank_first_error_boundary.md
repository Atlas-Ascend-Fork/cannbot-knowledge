---
{
  "type": "Runbook",
  "title": "torch_npu ERR99999 多 rank 失败时的 execute_log 与 plog 计数分流",
  "description": "来源 execute_log 仅一个 worker 有一条 ERROR，所查 8 个 worker 的 plog 均为零 ERROR。计数可定位后续应读的日志，不能单凭零计数认定环境故障或排除 CANN。",
  "tags": [
    "task.debugging",
    "topic.parallelism"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# torch_npu ERR99999 多 rank 失败时的 execute_log 与 plog 计数分流

## 适用场景

分布式训练汇总 ChildFailedError/ERR99999，需要先找到最早具体异常，避免把框架包装码当根因。

## 触发与观测

来源训练多个 local rank 退出 1；计数探针看到 execute_log 的 train_log_worker_4 有 1 条 ERROR，其余 7 个为 0；所查 plog 8 个 worker 均为 0 条 ERROR。

## 探针与操作

在PowerShell中将环境变量`CASE_ROOT`设置为故障采集根，下面应包含execute_log与ascend_log；示例统计8个worker，其他规模需调整范围。

```
$lp = $env:CASE_ROOT; "=== ERROR counts in execute_log ==="; Get-ChildItem -LiteralPath "$lp\execute_log" -File | ForEach-Object { $c = (Select-String -LiteralPath $_.FullName -SimpleMatch "[ERROR]" -AllMatches | Measure-Object).Count; "$($_.Name): $c" }; "=== ERROR counts in plog per worker ==="; 0..7 | ForEach-Object { $c = (Get-ChildItem -LiteralPath "$lp\ascend_log\plog_worker_$_\log" -File | Select-String -SimpleMatch "[ERROR]" | Measure-Object).Count; "plog_worker_$_`: $c" }
```

计数后需打开那一条错误及其前后完整上下文，核对时间、rank 与调用栈。零计数只涵盖所检索文件、级别和匹配模式。

## 机制与判别

ERR99999 是汇总现象，ERROR 数量不是原因分类器。应用 traceback、文件缺失或 CANN 内部异常应由具体首错内容决定，不能由 plog 零 ERROR 推导。

## 验证信号

本卡采用的客观信号是上述日志计数；数据集路径或环境修复结论未进入该卡证据，不据此声称已定界或修复。

## 适用与失效边界

这是日志导航规则。日志缺失、截断、错误采用其他级别或根本未落盘时，零 ERROR 不代表设备无错误。没有修复后的训练验证。
