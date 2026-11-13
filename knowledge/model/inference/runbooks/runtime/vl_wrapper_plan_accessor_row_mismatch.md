---
{
  "type": "Runbook",
  "title": "修复配方 · DSV4.1 尾窗 drafter 行数错配：plan 通道改 runner 侧 + drafter 行数硬校验",
  "description": "尾窗特性下沉重构后 NPU 复跑报 drafter 行数错配 [452,5120] vs [128,5120]。修复形态：plan 通道改在 runner _build_attention_metadata 内 clear→嵌套 build+stash（only-if-None，plan-less 层不清槽）；drafter 只读 runner 通道并加行数硬校验（num_context != hidden_rows 即 raise 带诊断信息），此后同类 handoff 洞会立刻响亮失败而非晦涩的 tensor-copy 错误。",
  "tags": [
    "task.debugging",
    "topic.speculative_decoding"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 修复配方 · DSV4.1 尾窗 drafter 行数错配：plan 通道改 runner 侧 + drafter 行数硬校验

## 适用场景

vllm-ascend-dsnext 的 DSV4.1 prefill 尾部窗口化（VLLM_ASCEND_ENABLE_TAIL_WINDOW_PREFILL）与 dspark 投机解码共存场景下的 plan 通道 handoff 修复。


## 触发与观测
触发：尾窗下沉重构（model_runner_v1.py 还原为公共模块零改动、plan 经 `runner.get_model().get_step_private_circle_plan()` 拉取）后 NPU 复跑，仍报 `RuntimeError: The expanded size of the tensor (452) must match the existing size (128) ... Target sizes: [452, 5120]. Tensor sizes: [128, 5120]`（dspark_proposer.py:350 set_inputs_first_pass），且三条尾窗日志中前两条（plan builder `452 -> 128`、boundary `452 -> 128`）在场。

## 探针与操作
静态审阅探针：对修复 diff 逐块核对（runner 通道 stash、plan-less 层不清槽、drafter 行数硬校验）。

## 机制与判别
修复形态（静态审阅通过）：plan 通道改由 runner `_build_attention_metadata` 内 clear→嵌套 build+stash（only-if-None，plan-less 层不清槽），drafter 只读 runner 通道并加行数硬校验（`num_context != hidden_rows` 即 raise 带诊断）——把这类洞从「晦涩 tensor-copy 错误」升级为「响亮失败」。

### 补充机制片段
```
+        shared = attn.shared_state
+        if shared is not None and metadata.swa.private_circle_plan is not None:
+            # The model reads the step plan at the head/tail boundary, after
+            # the head layers have run. Plan-less layers (e.g. the draft SWA
+            # group, which is excluded from the pool plan by design) must not
+            # clear it.
+            shared.step_private_circle_plan = metadata.swa.private_circle_plan
+        tail_idx = shared.tail_row_idx if shared is not None else None
+        if tail_idx is not None:
+            if tail_idx.numel() != hidden_states.shape[0]:
+                raise RuntimeError(
+                    "V4.1 tail-window row count does not match the hidden "
+                    f"states: tail={tail_idx.numel()}, hidden={hidden_states.shape[0]}"
+                )
+            # Tail-window layers address the batch through the gathered tail
+            # rows. Positions keep their original absolute values; cos/sin
+            # are batch-row-aligned tables and follow the same gather.
+            positions = metadata.positions.index_select(0, tail_idx)
```

## 验证信号
客观信号：vl_model.py 的未提交 diff（用户自行修复 wrapper 委托）、465 行/6 文件重放 diff 的全量审阅通过（runner 通道 +15 行、条件 stash、reset() 双字段清空、spec-verify 混批守卫、aux 冲突门控 dspark 豁免均核对）。NPU 复跑（预期日志链 `plan: 452 -> 128` → `boundary: 452 -> 128` → `DSpark first pass follows tail-window layout: 452 -> 128 context rows`、接受率不变）在轨迹内为「待复测」状态。

### 结论与证据边界

  修复形态（静态审阅通过、NPU 复测待做）：plan 通道改在 runner _build_attention_metadata 内 clear→嵌套 build+stash（only-if-None，plan-less 层不清槽）；drafter 只读 runner 通道并加行数硬校验（num_context != hidden_rows 即 raise 带诊断信息），此后同类 handoff 洞会立刻响亮失败而非晦涩的 tensor-copy 错误。

## 适用与失效边界
适用：vllm-ascend DSV4.1 尾窗 drafter plan 通道的 handoff 修复。失效/边界：(a) 行数硬校验是事后告警不是预防；(b) 尾窗无损性论证（纯 SWA draft + -1 sentinel + 逐行投影 ⟹ 与全量路径逐位等价）是静态论证，接受率不降才是运行时证据。
