---
{
  "type": "Runbook",
  "title": "DSV4.1 尾窗与 dspark 交接丢失：被包装模型访问器静默返回 None 导致 452/128 布局不匹配崩溃",
  "description": "vllm-ascend（vllm-ascend-dsnext，DSV4.1）prefill 尾窗特性（VLLM_ASCEND_ENABLE_TAIL_WINDOW_PREFILL，尾部 19 层只算每请求最后 128 token）与 spec decode drafter（dspark）联调。 通用模式：模型内状态经访问器（accessor）传递给 spec decode proposer / runner 的架构，且运行模型可能被外层类（wrapper/ForCausalLM 壳）包装。 知识形态：diagnostic_rule（trigger / probe / observation / discrimination）。",
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
# DSV4.1 尾窗与 dspark 交接丢失：被包装模型访问器静默返回 None 导致 452/128 布局不匹配崩溃

## 适用场景

- vllm-ascend（vllm-ascend-dsnext，DSV4.1）prefill 尾窗特性（VLLM_ASCEND_ENABLE_TAIL_WINDOW_PREFILL，尾部 19 层只算每请求最后 128 token）与 spec decode drafter（dspark）联调。
- 通用模式：模型内状态经访问器（accessor）传递给 spec decode proposer / runner 的架构，且运行模型可能被外层类（wrapper/ForCausalLM 壳）包装。

## 触发与观测

- 观测链——来源结论：判别依据：plan 与 boundary 日志均正常（452→128、model 已 gather）而 proposer 的 tail_plan 为 None，说明交接在读侧丢失；self.runner.get_model() 返回的对象被外层类包装，get_step_private_circle_plan 访问器只存在于 AscendDeepseekV41ForCausalLM 上、运行模型暴露的是 language_model.model...，getattr 取不到访问器时静默返回 None，使 drafter 回退全量 context 布局——这是「包装层吞掉模型访问器」的通用故障模式。

## 探针与操作

- 探针 1：对照三条日志链（"V4.1 tail-window prefill plan: 452 -> 128" / "boundary after layer 20: 452 -> 128" / "DSpark first pass follows tail-window layout: 452 -> 128 context rows"）定位丢失发生在哪一环。
- 探针 2：读 runner 的 self.model 装配点（load_lora_model / BreakableACLGraphWrapper / ACLGraphWrapper 包装链）与 drafter 的模型获取路径，确认 get_model() 返回的包装对象上 getattr 访问器为 None。
- 探针 3（一次性 handoff probe，区分三种失效）：打印 source（runner/model）、accessor 是否存在、plan_is_none、has_tail_row_idx、state_id、hidden_rows、num_context、plan keys——区分「accessor 缺失 / 槽位为空 / plan 无尾字段」。

## 机制与判别

- 修复机制 1（runner 保留本步 plan，逐字）：

```text
                # Tail-window handoff: retain this step's V4.1 private-circle
                # plan on the runner. The DSpark drafter reads it from here
                # instead of walking into the model's module tree, which can be
                # wrapped by an outer class that does not expose the accessor
                # (`get_step_private_circle_plan`); that silent None used to
                # drop the drafter back to the full-batch context layout while
                # the target had already gathered the tail rows.
                step_plan = common_v41_metadata.get("private_circle_plan")
                if step_plan is not None and getattr(
                    self, "_step_private_circle_plan", None
                ) is None:
                    self._step_private_circle_plan = step_plan
```

- 修复机制 2（proposer 优先读 runner，逐字）：

```text
        # Prefer the runner's step plan: the object returned by
        # ``get_model()`` can be wrapped by an outer class that does not carry
        # the accessor (observed: the accessor exists only on
        # ``AscendDeepseekV41ForCausalLM`` while the running model exposes
        # ``language_model.model...``), which previously made the handoff
        # vanish silently.
        plan_source = "runner"
        get_step_plan = getattr(self.runner, "get_step_private_circle_plan", None)
        if get_step_plan is None:
            plan_source = "model"
            get_step_plan = getattr(
                self.runner.get_model(), "get_step_private_circle_plan", None
            )
        step_plan = get_step_plan() if get_step_plan is not None else None
```

- 修复前的 drafter 读法与尾行 gather：

```text
304	        # Tail-window prefill step: the context rows are the model's gathered
305	        # tail rows. The draft is pure-SWA on the private ring and its first
306	        # pass stores context KV only inside each request's tail window (the
307	        # full-path clamp discards the head rows), so the gathered rows carry
308	        # every feature this pass consumes; only the row layout changes. The
309	        # target model has already gathered the aux captures to this layout.
310	        tail_plan = None
311	        get_step_plan = getattr(
312	            self.runner.get_model(), "get_step_private_circle_plan", None
313	        )
314	        if get_step_plan is not None:
315	            step_plan = get_step_plan()
316	            if step_plan is not None and "tail_row_idx" in step_plan:
317	                tail_plan = step_plan
318	        if tail_plan is not None:
319	            tail_idx = tail_plan["tail_row_idx"]
320	            num_context = int(tail_idx.numel())
321	            target_positions = target_positions.index_select(0, tail_idx)
```

- 无损性论证——来源结论：尾窗对 drafter 无损的机制依据：dspark draft 是纯 SWA、join PC ring，无长 KV/index 平面；full 路径下 clamp 本就把每请求窗口外 context 槽位 mask 成 -1，_store_standard_swa_kv 对 -1 跳过（头部行的 KV 投影算完即丢弃）；KV 投影按行独立（行 i 只依赖特征行 i + position i），故喂尾行特征与全量路径逐位等价、存储槽位坐标不变、PC commit 机制零改动。
- 修复与验证判据——来源结论：修复：_build_attention_metadata 把本步 V4.1 private-circle plan 保留在 runner（_step_private_circle_plan + get_step_private_circle_plan 访问器），dspark proposer 优先从 runner 读取、模型访问器仅作回退，并加一次性 handoff probe 日志区分 accessor 缺失/槽位为空/plan 无尾字段三种情况；配合三条一致日志链（"plan: 452 -> 128" → "boundary after layer 20: 452 -> 128" → "DSpark first pass follows tail-window layout: 452 -> 128 context rows"）与「接受率应与不开尾窗相同（无损）」作为验证判据。该判据为设计与检视结论，修复后的完整 NPU 复跑结果未在本簇轨迹中捕获。
- 相关检视结论（同一问题的源码检视）：plan/boundary/proposer 由同一个 plan 的 tail_row_idx 门控（model 读 plan.get、proposer 判 "tail_row_idx" in plan），同一步内不可能两边布局不一致；decode step 每个 SWA 层 forward 把 step_private_circle_plan 刷成 None（自愈）；恒等 step 不建 tail 字段；verify+PC prefill 混批时 runner verify 分支按全量行坐标寻址、尾窗 step 的 aux 已 gather 到 W 行会静默选错行，需 plan builder 守卫（检测非 prefill 行 q>1 则不建 tail 字段），该守卫在 PD 部署下恒不触发（P 侧 num_decodes=0、D 侧不建 plan）。

## 验证信号

  - c5933b73 （tool_result）：修复后的 runner 保留代码与 proposer 优先 runner 源代码（含 "observed: the accessor exists only on AscendDeepseekV41ForCausalLM while the running model exposes language_model.model..." 的观察注释）。
  - cf317344 实跑观察（plan/boundary 日志 452→128 正常、proposer tail_plan None、num_context=452）。
  - fb5f2db7 检视结论（激活单一信号源、prefill-only 语义、proposer 链路、kernel 交互、aux 时序、dummy_run/ACL graph capture 不经过 set_inputs_first_pass 无 stale plan 风险；发现并修 verify 混批守卫）。
- 修复后的完整 NPU 复跑（三条日志数值一致 + 接受率与不开尾窗相同）未在本簇任一轨迹中捕获到终态结果——按验证判据执行后才能宣称闭环。

## 适用与失效边界

- 适用：任何"模型内状态经访问器传给 drafter/runner"的 spec decode 架构；包装模型（ForCausalLM 壳、ACLGraphWrapper、LoRA 包装）场景下访问器失效的判别与修复模式（把状态保留点从模型树移到 runner，读方优先 runner）。
- 失效边界：该修复只解决"交接丢失"（452/128 不匹配）；尾窗特性本身的 prefill-only 语义依赖 plan builder 门控与 decode 自愈；非 PD 单机 dspark+PC+尾窗的 verify 混批场景必须保留 plan builder 守卫；恒等退化步（全请求 ≤128）不建 tail 字段、两条路径天然一致。修复效果在本簇内未完成硬件级终验，采用前需补跑。
