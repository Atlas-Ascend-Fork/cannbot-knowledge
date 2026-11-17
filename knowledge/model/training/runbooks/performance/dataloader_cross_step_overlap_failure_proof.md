---
{
  "type": "Runbook",
  "title": "DataLoader 消费等待：按结束时间与 duration 重建 fetch/compute 区间",
  "description": "修正 fetch_all 与 compute_phase 时间线，保留实际阻塞观测；队列、feeder、FD 或 worker 瓶颈仍需分支探针，不能由 out=8 直接定论。",
  "tags": [
    "task.debugging",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# DataLoader 消费等待：按结束时间与 duration 重建 fetch/compute 区间

## 适用场景

torchtitan/StatefulDataLoader 多进程预取与训练步的时间线分析。日志在阶段结束时记录 duration。

## 触发与观测

启用预取后，消费端仍出现 _get_data 等待；outstanding 数不能直接等同于已经可消费的 batch 数。

## 探针与操作

把每条日志的时间当结束点，用对应 duration 反推开始点。分别记录任务派发、worker 完成、数据入队/可读和主进程接收，才能区分计算不足与传输背压。

同一次运行的原始日志字段摘录（已去除进程/日期前缀）：

```text
13:15 run:
13:15:49,260 [ZCODE_TRACE] train_step fetch_all: 1.3799s
13:15:52,377 [ZCODE_TRACE] train_step compute_phase: 3.1164s
[ZCODE_DL] _get_data blocked for 0.8848s at rcvd=0 send=8 out=8 info_len=1
```

## 机制与判别

13:15:49.260 的 fetch_all:1.3799s 对应约 13:15:47.880→49.260；13:15:52.377 的 compute_phase:3.1164s 对应约 49.261→52.377。不能把这两个结束时间之间的计算区间标成 fetch。out=8 只描述未完成/未接收任务窗口，不证明 feeder/pipe/FD 是根因。

## 验证信号

同一次 13:15 运行的日志包含上述两条结束时间/duration，以及首次 rcvd=0 时 _get_data blocked for 0.8848s、send=8、out=8、info_len=1。它证明消费端等待，不能直接证明 worker 在整个 compute 期间只产出一批；较早 13:09 的 0.2775s 不并入这次运行。

## 适用与失效边界

本记录没有完成队列容量、FD 传输或 worker 算力的受控定位，不能称为 PyTorch 的普遍框架限制。不同步骤和不同来源的日志不能拼成一个已闭合时间线。
