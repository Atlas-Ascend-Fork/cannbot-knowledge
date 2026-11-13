---
{
  "type": "Runbook",
  "title": "A1 device 元数据提前入队的分阶段打桩对照与归因限制",
  "description": "TP=2打桩先测base/opt，后补P3+B2b。两组worker均值的bam/execute_model差为+8.93%/+9.12%，但并非三侧同轮交错，宿主负载和轮间漂移未隔离，不能认定为已测得的A1因果增量。",
  "tags": [
    "task.debugging",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# A1 device 元数据提前入队的分阶段打桩对照与归因限制

## 适用场景

vllm-ascend的DeepSeek-V4.1 host-bound优化：尝试在metadata构建时将device元数据任务提前提交至旁路流，与后续host build重叠。来源为TP=2打桩环境，并非真实八卡性能验收。

## 触发与观测

来源先采集base与含A1的opt各3轮、每轮2个worker。发现opt的build开销偏高后，才创建无A1的P3+B2b对照worktree并另补2轮、共4个worker样本。

| worker均值口径 | opt（含A1，先采） | P3+B2b（后补） | 两组均值相对差 |
| --- | ---: | ---: | ---: |
| _build_attention_metadata | 3904us | 3584us | +8.93% |
| execute_model | 5264us | 4824us | +9.12% |

端到端step wall三组记录的中位数为214.7/202.1/218.3ms。来源还记录宿主负载高、轮间与worker间波动；这些数值不能单独证明A1负收益或三方案等效。

## 探针与操作

1. 回看每组的提交、采样时间、轮次、worker和调用数。此例P3+B2b是观察base/opt结果后的后补对照，**不是三侧同轮交错**。
2. 若要隔离A1增量，应在其余实现与工作负载一致的条件下重新做A/B或三侧交错/随机顺序、重复轮次；同时保存host负载及每worker原始结果。
3. 将打桩host开销与真实设备/端到端指标分开。区间重叠不是显著性检验，也不证明等效。

## 机制与判别

A1的实现意图是任务创建时直接enqueue到旁路executor；以下为来源改动节选：

```diff
@@ -2829,10 +2830,15 @@ class DeepseekV41MetadataBuilder(AttentionMetadataBuilder[DeepseekV41Metadata]):
             return existing
         shared[key] = buffer
         if self._device_metadata_enabled:
-            self._device_metadata_tasks = (
-                *self._device_metadata_tasks,
-                DeviceMetadataTask(stage, run, id(buffer), priority=priority),
-            )
+            if self._device_metadata_executor is not None:
+                # 提前提交：任务一创建即在旁路流执行，device 元数据内核
+                # 与后续 host build 重叠（异步掩盖）。
+                self._device_metadata_executor.enqueue(stage, run, id(buffer))
+            else:
+                self._device_metadata_tasks = (
+                    *self._device_metadata_tasks,
+                    DeviceMetadataTask(stage, run, id(buffer), priority=priority),
+                )
         else:
             run()
         return buffer
```

3904/3584和5264/4824是分阶段worker均值之差，计算本身可保留；时间漂移、宿主负载及worker差异未被隔离。它们不能改称“已单独测得的A1增量”。后补对照能提供进一步实验线索，但不足以闭合因果。

## 验证信号

已采用base/opt三轮与后来P3+B2b两轮的工具采样返回，并核对worktree建立在第一阶段测量之后。没有三侧同轮交错的原始记录，也没有真机A/B。建议重采的实验未在本次知识复核中执行。

## 适用与失效边界

适用于理解此TP=2打桩样本的测量限制。可保留“本次记录的opt均值较后补P3+B2b高”，不能外推为A1普遍回归、端到端收益定论或真实多卡优化优先级。
