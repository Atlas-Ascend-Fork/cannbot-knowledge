---
{
  "type": "Runbook",
  "title": "cu_seqlens 隐式 D2H：按 copy_ 的维度、dtype 与调用链分组",
  "description": "区分 metadata DeviceCopy 与 allfallback 标量提取；原汇总表单位矛盾，暂不采用其绝对耗时和占比。",
  "tags": [
    "task.debugging",
    "topic.data_movement"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# cu_seqlens 隐式 D2H：按 copy_ 的维度、dtype 与调用链分组

## 适用场景

torchtitan-npu DSV4 varlen/sparse attention 的编译路径 profiling；需要原始事件参数、生成代码和调用栈。

## 触发与观测

观察到 dim=8 long int copy_ 与 select→_local_scalar_dense 链，不能把所有 scalar 提取都归到同一个 fallback 来源。

## 探针与操作

按 shape、dtype、forward/backward 和调用栈分组，再检查实际生成的 DeviceCopy 与 non_blocking 参数；对照关闭 allfallback 后哪些事件仍出现。

保留计数；单位不明的时长列暂缓采纳：

```text
event family                         count
copy_ dim=8 long int                   172
_local_scalar_dense double           7912
```

## 机制与判别

元数据张量回读与 allfallback Scalar 参数是需要分开的两类路径。只有确认实际 non_blocking 与 pinned 标记，才能判断某条额外同步逻辑是否被调用；不能仅凭补丁存在就认定它造成当前阻塞。

## 验证信号

原汇总记录 copy_ dim=8 long int 为 172 次，_local_scalar_dense double 为 7912 次。表头 wall(s)、正文微秒和秒换算互不一致，缺少可回读的单位闭环，因此本卡不采纳该表的绝对时长、占比或收益。

## 适用与失效边界

需要回到原始 profiler 字段确定时间单位；嵌套 copy 与 synchronize 的时间也不能简单相加为独占耗时。host 副本方案与 patch 收窄在该记录中未形成设备修复闭环。
