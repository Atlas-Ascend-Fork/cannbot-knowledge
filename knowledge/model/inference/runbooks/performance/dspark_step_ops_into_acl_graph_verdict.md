---
{
  "type": "Runbook",
  "title": "DSpark 图外 eager 操作的旁路流重叠候选：仅完成静态检查",
  "description": "Kimi K3 DSpark 中尝试把 build_model_inputs_first_pass 放到独立 stream，在 draft 图前 wait_stream。来源只完成 diff 和 py_compile；图捕获、同步先后、缓冲生命周期、精度与性能均未运行验证。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# DSpark 图外 eager 操作的旁路流重叠候选：仅完成静态检查

## 适用场景
- vllm-ascend 上以 DSpark 投机解码 + ACL graph（FULL_DECODE_ONLY）部署 Kimi K3，profiling 显示每个 decode step 都出现一批图外算子（linear/rotary/scatter/copy 等 host 启动）。
- 用户/外部分析建议"把 precompute_and_store_context_kv() 搬进图"以消除每步 host 启动，需要低风险的替代或补充方案。

## 触发与观测
- profiling 每 step 都有单独算子（请求确认能否通过搬图解决）。

- 关键结论：


> 方案 B（只完成静态检查，是否采用需运行验证）：不搬图，改成旁路流 overlap——保持现在 hoisted 在 `_propose` 的 eager 调用（设计上保留调用内容，运行正确性仍待验证），把 `build_model_inputs_first_pass` 放到独立 stream 上执行，进入 draft 图前才用设备侧 `wait_stream` 显式排序，旨在为 draft attention 读取 KV 建立先后关系，实际流依赖、图捕获与缓冲生命周期仍须验证。预期不减少算子数量，而尝试与 host metadata 构建重叠；收益尚未测量，改动小、可回退；新增开销是一个 stream + 两次 `wait_stream`。已按方案 B 完成最小改动（未提交，+19/−7），`py_compile` 通过。

## 探针与操作
1. 正确判断 ACL graph replay：不要用"日志每步出现 Replaying aclgraph"——它是 logger.info_once（acl_graph.py:261），每进程只打一次；Capturing 是 debug 级默认不可见。正确判据：profiler 的 ACL graph execute/replay 节点、VLLM_LOGGING_LEVEL=DEBUG、或在 _propose 打印 aclgraph_runtime_mode（分析结论，源码行号来自助手分析）。
2. 需要消除每步 host 启动时的候选替代：见机制与判别的方案 B。

## 机制与判别
- 方案 B 机制：图外 eager 保持不变，把 build_model_inputs_first_pass 放到惰性创建的 side stream 上，与 host 侧 metadata 构建重叠；进 draft 图前才 wait_stream 排序（晚等保 overlap）。

### 补充机制片段


```text
+        if self.method == "dspark":
+            # Launch the draft context-KV projection on a side stream so it
+            # overlaps the host-side draft metadata build below. It is ordered
+            # after the input kernel that filled the context slot buffers, and
+            # the default stream waits for it before the draft graph replay.
+            if self._context_kv_stream is None:
+                self._context_kv_stream = torch.npu.Stream()
+            self._context_kv_stream.wait_stream(torch.npu.current_stream())
+            with torch.npu.stream(self._context_kv_stream):
+                self.build_model_inputs_first_pass(num_input_tokens, self._context_slot_mapping_buffers)
```


```text
+        if self.method == "dspark":
+            # The draft attention reads the context KV written on the side
+            # stream; wait as late as possible to keep the overlap.
+            torch.npu.current_stream().wait_stream(self._context_kv_stream)
```

## 验证信号
- 方案 B 最小改动已实现：仅 vllm_ascend/spec_decode/llm_base_proposer.py +19/−7，git diff 与 py_compile 通过（未提交）。
- 客观核对：方案 B diff（2132）已读取原文比对。
- 局限：无任何运行时验证；启动日志（仍进图）、连续两次 curl、profiling 前后对比（aclrtSynchronizeStreamWithTimeout 缩短）、首请求/连续/同前缀正确性均列为待验证项。

- 验证范围（validation_scope）：static_check

## 适用与失效边界
- 方案 B 只隐藏延迟不减少算子；若 profiling 占比不高，保持 hoisted 版本更稳。
