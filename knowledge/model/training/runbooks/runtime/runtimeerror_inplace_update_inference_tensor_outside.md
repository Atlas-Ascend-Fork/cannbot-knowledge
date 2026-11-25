---
{
  "type": "Runbook",
  "title": "vLLM 推理线程 inference_mode 下分配的 ADXL 池槽位成为 inference tensor，writer 线程 copy_ 被拒",
  "description": "链路：vllm-ascend 在线训练 hidden-states 传输——训练仓 `speculators/hs_connectors/mooncake_store.py` 的 `_AdxlPool` 在 vLLM 主执行线程内 setup，Mooncake writer 线程（ThreadPoolExecutor）异步执行 `slot.copy_()` 写入。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-20T14:17:06Z",
  "platforms": []
}
---

# vLLM 推理线程 inference_mode 下分配的 ADXL 池槽位成为 inference tensor，writer 线程 copy_ 被拒

## 适用场景

- 链路：vllm-ascend 在线训练 hidden-states 传输——训练仓 `speculators/hs_connectors/mooncake_store.py` 的 `_AdxlPool` 在 vLLM 主执行线程内 setup，Mooncake writer 线程（ThreadPoolExecutor）异步执行 `slot.copy_()` 写入。
- 框架：PyTorch（inference_mode 语义）+ torch_npu ADXL/DMA 传输 + Mooncake；时间 2026-09，speculators 仓 commits `b0c78b1`/`f5050b0`。
- 通用场景：任何“张量池在 inference_mode 线程分配、跨线程在普通模式做原地写”的推理/训练混合工程。

## 触发与观测

- 触发：推理端 writer 线程写 Mooncake 样本失败（用户贴出的推理端日志，source 0 seq 343，user_reported）：

```text
(Worker_TP0_EP0 pid=225190) 2026-09-10 14:56:53,783 - ERROR - Mooncake write failed for cmpl-becf12649f315ff3-0-aeb08dc4: RuntimeError('Inplace update to inference tensor outside InferenceMode is not allowed.You can make a clone to get a normal tensor before doing inplace update.
```

- 机制：vLLM worker 主线程运行在 `torch.inference_mode()` 下，`_AdxlPool.setup()` 里的 `torch.empty` 分配的 pool slot 被永久标记为 inference tensor；writer 线程的线程局部模式不继承 inference_mode，`slot.copy_()` 属于 inference tensor 在 InferenceMode 之外的原地更新，被 PyTorch 拒绝（source 0 seq 364/384/473）。

## 探针与操作

- 修复（before → after）：
  - before：`_AdxlPool.setup()` 直接 `torch.empty(...)` 分配 slot（在 inference_mode 内）。
  - after：分配处用 `with torch.inference_mode(False)` 包裹 `torch.empty`（用户提出、agent 验证并落地 `mooncake_store.py:183`；后续 commit `f5050b0` 进一步改为整块连续 buffer 一次注册再切片成 slot，view 同样不是 inference tensor）。

```python
# speculators/hs_connectors/src/hs_connectors/mooncake_store.py :: _AdxlPool.setup()
with torch.inference_mode(False):
    pool = torch.empty(slot_bytes * num_slots, ...)   # 分配为普通 tensor
```

- 最小复现探针：外层 `torch.inference_mode()` 中调用 `_AdxlPool.setup()`，检查 `slot.is_inference()`；修复后为 `false`，普通线程语义下 `pool.put()` 的原地 `copy_()` 成功（source 0 seq 454/473）。

## 机制与判别

- inference tensor 标记发生在张量创建时（线程局部 InferenceModeOrNot），不可事后解除；只影响“跨线程原地写”这一类操作，读传输与 clone 不受影响。
- 判别：报错文本明确指向 `Inplace update to inference tensor outside InferenceMode`；与 ACL context 缺失（同 trace 前一问题：writer 线程未恢复 aclrtContext 导致 `batch_put_from` INVALID_PARAMS -600）是两类不同根因，前者 PyTorch 层拒绝、后者 ACL 层参数错误。
- 低风险残留（代码审查，source 0 seq 540）：`torch.empty` 失败时清理路径访问未赋值 `pool.data_ptr()` 会二次报 `UnboundLocalError`（不改行为只污染日志）；整块分配 1 GiB 比旧 2×512 MiB 更易受显存碎片影响。

## 验证信号

- 最小复现：修复后 slot `is_inference()==false`，跨线程 `copy_` 成功（agent 执行的最小复现，source 0 seq 454，agent_narrative）。
- 单元测试：Mooncake 单测 19 passed、`git diff --check` 通过（source 0 seq 473，agent 转述工具输出）。
- 失败侧原始报错为用户提供的推理端日志（source 0 seq 343，user_reported）；本会话内无端到端 NPU 训练回归，修复效果在真实训练任务上未复验。

## 适用与失效边界

- 适用：vLLM（inference_mode 执行模型）+ 异步 writer 线程共享张量池的 Ascend/Mooncake 传输；同构的 KV/hidden-state 转移组件。
- 失效/停止：若 writer 改为 clone 写（错误信息建议的方案）会多一次拷贝，非优选；`inference_mode(False)` 只应包裹分配点，不能关闭 vLLM 主线程的推理模式。显存碎片环境下注意整块连续分配的失败风险。
- 版本边界：PyTorch inference_mode 语义（RFC 17）；观测于 2026-09 speculators/mooncake_store.py。

## 附：断言存档

- vLLM inference_mode 主线程内 torch.empty 分配的 ADXL 池槽位被标记为 inference tensor，writer 线程在普通模式执行 slot.copy_() 报 Inplace update to inference tensor outside InferenceMode
- 用 torch.inference_mode(False) 仅包裹分配点后槽位为普通 tensor，跨线程原地写成功；最小复现验证 is_inference()==false 且 pool.put() copy_ 成功，Mooncake 单测 19 passed

```text
在 speculators/hs_connectors/src/hs_connectors/mooncake_store.py 的 _AdxlPool.setup() 中，用 with torch.inference_mode(False) 包裹 torch.empty 分配
```
