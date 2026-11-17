---
{
  "type": "Runbook",
  "title": "model-only checkpoint 成功不等于 optimizer 状态可恢复",
  "description": "先检查 checkpoint 的键集合与保存分支，再评估 virtual optimizer 的完整恢复；静态裸 dcp.save 不能证明所有含 optimizer 的保存必然崩溃。",
  "tags": [
    "task.debugging",
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
# model-only checkpoint 成功不等于 optimizer 状态可恢复

## 适用场景

torchtitan-npu virtual optimizer 与 checkpoint_virtual 的保存/恢复验收；实际行为受保存模式与版本影响。

## 触发与观测

仅权重保存成功与包含 swap optimizer 状态的失败报告看似矛盾，需要先核对两次实际保存内容。

## 探针与操作

读取 DCP metadata 的 key 集合，区分模型权重、optimizer 与调度器状态；再分别做 model-only 和完整状态的 save/load，以及恢复后的状态/绑定检查。

源码函数单元（依赖所属模块上下文）：

```python
@torch.no_grad()
def dcp_save(
    self,
    state_dict: dict[str, Any],
    checkpoint_id: str,
    async_mode: AsyncMode,
    enable_garbage_collection: bool = False,
    to_hf: bool = False,
) -> Future | AsyncSaveResponse | None:
    if async_mode != AsyncMode.DISABLED or to_hf:
        return super().dcp_save(
            state_dict=state_dict,
            checkpoint_id=checkpoint_id,
            async_mode=async_mode,
            enable_garbage_collection=enable_garbage_collection,
            to_hf=to_hf,
        )

    dcp.save(
        state_dict,
        storage_writer=dcp.FileSystemWriter(
            checkpoint_id,
            per_thread_copy_ahead=0,
        ),
    )
    if enable_garbage_collection:
        GarbageCollection.collect("GC collection invoked by checkpointer.")
    return None
```

## 机制与判别

所读同步保存分支直接调用 dcp.save，per_thread_copy_ahead=0；它是否收到 optimizer 状态取决于上层 state_dict。model-only 成功不能验收完整断点续训，而源码中没有 staging 也不能单独证明所有完整状态保存都必崩。

## 验证信号

原始工具读取能证明该同步 dcp_save 实现。键计数、完整 swap round trip 与其他修复分支没有作为本卡的新验收闭环，不再宣称 optimizer 保存/恢复的普遍成功或必然崩溃。

## 适用与失效边界

需要固定代码版本、保存模式和实际状态类型分别复现；异步和 HF 分支会转调父类，不由所示同步分支覆盖。恢复后还需验证 optimizer 状态及 swap 绑定，而不只看文件大小。
