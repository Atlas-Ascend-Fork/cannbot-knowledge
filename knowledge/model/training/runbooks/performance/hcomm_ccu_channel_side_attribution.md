---
{
  "type": "Runbook",
  "title": "CCU 性能回退的静态排查：区分直接改动与共享资源候选",
  "description": "记录 channel 路径 diff 与共享映射声明，保留对照/采样方法；内存分配次数、锁争用和具体性能根因没有实测闭环。",
  "tags": [
    "task.debugging",
    "topic.parallelism"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# CCU 性能回退的静态排查：区分直接改动与共享资源候选

## 适用场景

服务于训练通信后端的 hcomm/CCU channel 分支排查。使用前应确认模型或框架实际走到这些通道，而非泛化到所有训练通信。

## 触发与观测

用户报告分支的 CCU 用例劣化，并要求收窄到 channel；这一性能现象是用户输入，不是本记录的完整基准结果。

## 探针与操作

固定两个构建版本，比较 channel 调用链和共享映射；对实际 CCU/AICPU 混合路径记录资源创建、同步拷贝、launch 和锁等待。

源码中新增共享映射的完整声明：

```text
std::unordered_map<DeviceChannelKey, ChannelHandle, DeviceChannelKeyHash> ChannelProcess::g_ChannelDestroyHandleMap;
```

## 机制与判别

所读差异新增了共享 channel 映射等实现内容。直接 CCU 路径没有文本 diff，不代表运行行为一定不变；共享锁、间接调用和混合通道只能列为待测候选，不能靠静态成本估计裁定根因。

## 验证信号

本卡证据层级为源码读取和 diff。没有闭合的 channel 实测对照，因此不采纳“至少 6 次分配/6 次 H2D”或“高几个量级”等成本承诺。

## 适用与失效边界

必须核验真实调用路径和独立基准。不能把用户已排除的某一测试范围当作其他路径都已测完，也不能把静态候选排序写成定位成功。
