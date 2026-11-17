---
{
  "type": "Runbook",
  "title": "多卡 MoE 超时排查：按设备与核身份聚合 current PC",
  "description": "从超时记录提取 current PC 辅助定位等待点；先区分记录条数与唯一设备/核，匹配同版本二进制，不能仅凭频数裁定死锁机制。",
  "tags": [
    "task.debugging",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# 多卡 MoE 超时排查：按设备与核身份聚合 current PC

## 适用场景

多卡 NPU kernel 的 EZ9999/aicore timeout 日志；设备、rank、core 标识及构建产物可取得。

## 触发与观测

记录出现 only 1/8 ranks reported 与 aicore timeout。错误转储包含重复记录和多个 PC 字段。

## 探针与操作

先定位 current 字段，保留设备/rank/core 组合后再聚合，避免把 trap PC 和 current PC 混用；用匹配的目标文件或反汇编定位候选等待点。

原聚合先 sort -u 再计数；不是日志频次或唯一设备核数：

```text
current PC             distinct (core_id, PC) pairs after device identity was lost
0x1200408728e8          62
0x12004084af64          31
```

## 机制与判别

PC 集中只能缩小等待位置，不能单独证明依赖闭环或某个 FIFO 根因。相同 core_id 在不同设备上不是同一核；丢失设备身份后，只能按实际聚合方法报告本例的去重 (core_id,PC) 对数，不能推导唯一设备核数。

## 验证信号

原命令先提取 (core_id,current PC)、sort -u 后再计数：0x1200408728e8 为 62 对，0x12004084af64 为 31 对。设备身份在该聚合中已经丢失，因此既不是原始日志频次，也不是唯一设备核数；不将其作为独立因果闭环。

## 适用与失效边界

源码文本偏移不等于指令地址；需匹配同版本二进制与地址基准。静态依赖图未发现环不等于排除时序问题，真正根因还需完整受控实验。
