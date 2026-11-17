---
{
  "type": "Runbook",
  "title": "HashMoE checkpoint 缺 gate.bias：在 init_states 后复查 buffer 生命周期",
  "description": "构造时移除的 expert_bias_E 可能在上游 init_states 重新出现；修正覆盖初始化钩子，并以 state_dict、to_hf 和前向检查限定验证范围。",
  "tags": [
    "task.debugging",
    "topic.checkpointing"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# HashMoE checkpoint 缺 gate.bias：在 init_states 后复查 buffer 生命周期

## 适用场景

torchtitan-npu DSV4 hash 路由层使用 HF/DCP checkpoint；训练初始化包含 to_empty 和 init_states。

## 触发与观测

加载报 hash 层 layers.0.ffn.gate.bias 缺失。只检查刚 build 的模型，会漏掉后续初始化重新建立的 buffer。

## 探针与操作

依次检查 build、init_states 后的 state_dict，再看 to_hf 请求的键。以下覆盖方法应放在匹配版本的 HashMoE 类中，保留上游初始化行为。

源码函数单元（依赖所属模块上下文）：

```python
# torchtitan_npu/patches/torchtitan/models/common/moe.py (HashMoE)
def _init_self_buffers(self, *, buffer_device=None):
    super()._init_self_buffers(buffer_device=buffer_device)
    # Hash layers route by ``tid2eid`` and never apply ``expert_bias_E``;
    # the upstream re-materialization must not resurrect the buffer, or
    # the trainer's ``init_states()`` (after ``to_empty()``) would put it
    # back into ``state_dict()`` and break HF checkpoint loading.
    if getattr(self.router, "hash", False):
        self.expert_bias_E = None
```

## 机制与判别

覆盖 _init_self_buffers 后先调用 super，再在 hash 路由条件下将 expert_bias_E 置 None，使该属性在重初始化后继续不进入 hash 层的 checkpoint 请求。不能仅靠构造时清理维持这个不变量。

## 验证信号

原始检查输出显示 hash 层 0/1 不含该 buffer、非 hash 层 2/3 保留；to_hf 只请求非 hash 层 gate.bias。记录还有 6 passed 与 hash 层前向冒烟；不据此宣称完整官方大模型训练恢复通过。

## 适用与失效边界

需同时核对上游钩子签名及 from_hf 的 hash 层映射策略。两份来源有大量相同历史，按一个修复链记录，不计两次独立复现。
