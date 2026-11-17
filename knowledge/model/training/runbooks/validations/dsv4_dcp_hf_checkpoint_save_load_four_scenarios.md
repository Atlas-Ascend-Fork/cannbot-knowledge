---
{
  "type": "Runbook",
  "title": "Checkpointing active 却不保存：检查独立的 load_only 短路开关",
  "description": "enable 与 load_only 是两个独立条件；示例默认 load_only 时，仅开启 enable 仍不会保存。保留此源码判据，不把其他未采纳场景的结果放入本卡。",
  "tags": [
    "task.implementation",
    "topic.checkpointing"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": [
    "agnostic"
  ]
}
---
# Checkpointing active 却不保存：检查独立的 load_only 短路开关

## 适用场景

记录中的 torchtitan-npu CheckpointConfig 与启动脚本；示例参数包含 --checkpoint.no-enable 和 --checkpoint.load-only。

## 触发与观测

日志显示 Checkpointing active，但用户预期的保存未发生。

## 探针与操作

检查最终参数和 _should_save 的完整判断顺序。保存场景显式确认 enable=True 且 load_only=False，随后从日志与实际产物核对保存行为。

所读版本的完整保存条件函数（已去除工具行号）：

```python
def _should_save(self, curr_step: int, last_step: bool = False) -> bool:
       """Determine whether a checkpoint should be saved based on
       the current step, interval, and training status."""
       if not self.enable or self.load_only:
           return False
       if curr_step == 1 and self.enable_first_step_checkpoint:
           return True
       if last_step:
           return True
       if curr_step % self.interval == 0:
           return True
       return False
```

## 机制与判别

所读实现第一项判断是 if not self.enable or self.load_only: return False，因此 enable=True 不能覆盖 load_only=True 的短路。该版本示例的保存入口需要同时调整两项，而非只追加 --checkpoint.enable。

## 验证信号

原始工具输出提供 _should_save 实现的完整分支。此卡只采纳该配置判据；不再把 DCP/HF 四场景、loss 变化或存储大小写成这个判据的额外验收。

## 适用与失效边界

默认值与 flag 命名依赖所用版本/脚本，其他入口未必默认 load_only。保存、恢复、优化器状态和权重一致性必须分别验收。
