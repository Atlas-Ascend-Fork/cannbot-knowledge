---
{
  "type": "Runbook",
  "title": "DeepseekV41IndexerFoldedSpec 构建器 TypeError 启动崩溃修复：folded 孪生的跳过粒度从 kv-cache-group 降到 attention-group",
  "description": "vllm-ascend V27-dsv4.1 分支（HEAD 14a808abf 引入 DeepseekV41IndexerFoldedSpec）PD 分离 serve 启动即崩：dsa_v41.py build() 对 folded spec 抛 TypeError: Unsupported V4.1 cache spec。根因是原跳过判断在 kv-cache-group 粒度用 all(isinstance(...)) 判断整组，但 folded 孪生层与 token-indexed 兄弟层按 slot 打包共居 mixed full 组，all(...) 恒 False，跳过永不生效。修复把跳过降到 attention-group 粒度（循环内 isinstance 判断 continue），py_compile 通过、builder.build() 调用点全文件审计仅一处受影响；运行时验证（NPU pytest/serve smoke）因本机无 torch_npu 未在轨迹内完成。后续会话用户口头反馈崩溃消失（非客观信号，未计入验证）。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.speculative_decoding"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "agnostic"
  ]
}
---

# DeepseekV41IndexerFoldedSpec 构建器 TypeError 启动崩溃修复：folded 孪生的跳过粒度从 kv-cache-group 降到 attention-group

## 适用场景

- 框架/版本：vllm-ascend，分支 `V27-dsv4.1`，HEAD `14a808abf add new k cache`（该提交引入 `DeepseekV41IndexerFoldedSpec`）；文件 `vllm_ascend/worker/model_runner_v1.py`（`_build_attention_metadata`）。
- 部署形态：DeepSeek-V4.1 PD 分离（MooncakeHybridConnector）serve，两侧启动。
- 症状：启动即崩（任何前向之前），日志为 `TypeError: Unsupported V4.1 cache spec: DeepseekV41IndexerFoldedSpec`。
- 信息缺口声明：修复在本轨迹内闭合到"语法通过 + 调用点静态审计"；本机无 torch_npu/vllm 环境，运行时验证（pytest / serve smoke）未在轨迹内完成。

## 触发与观测

> 故障：V27-dsv4.1 分支（HEAD 14a808abf add new k cache 引入 DeepseekV41IndexerFoldedSpec）上 PD 分离 serve 启动即崩，报错日志为 dsa_v41.py:2023 raise TypeError: Unsupported V4.1 cache spec: DeepseekV41IndexerFoldedSpec（报错为用户提供日志；分支、spec 定义与产生点由仓库 grep 客观证实）。

用户提供的报错日志（来源记录 事件 112，原文节选）：

```
File "/opt/vllm-ascend-dsnext/vllm_ascend/worker/model_runner_v1.py", line 4157, in _build_attention_metadata
    _build_attn_group_metadata(
File "/opt/vllm-ascend-dsnext/vllm_ascend/worker/model_runner_v1.py", line 4062, in _build_attn_group_metadata
    attn_metadata_i = builder.build(
File "/opt/vllm-ascend-dsnext/vllm_ascend/attention/dsa_v41.py", line 2023, in build
    raise TypeError(f"Unsupported V4.1 cache spec: {type(spec).name}")
TypeError: Unsupported V4.1 cache spec: DeepseekV41IndexerFoldedSpec
```

（注：报错中的 `{type(spec).name}` 疑为源码笔误，应以仓库实际代码为准；本轨迹未逐字读取 dsa_v41.py:2023 该行。）

客观核实（事件 118，`git branch --show-current; git log --oneline -3; grep -rn "DeepseekV41IndexerFoldedSpec"` 输出逐字）：

```
V27-dsv4.1
14a808abf add new k cache
29a9dba84 !59 merge pr_54 into releases/v0.27.1rc
21ad48cd4 dspark cache add to private pool
===
vllm_ascend/core/deepseek_v41.py:58:class DeepseekV41IndexerFoldedSpec(AscendMLAAttentionSpec):
vllm_ascend/models/deepseek_v41/indexer.py:99:                    DeepseekV41IndexerFoldedSpec(
vllm_ascend/worker/model_runner_v1.py:143:    DeepseekV41IndexerFoldedSpec,
vllm_ascend/worker/model_runner_v1.py:4022:                isinstance(s, DeepseekV41IndexerFoldedSpec)
```

## 探针与操作

定位探针（事件 116/117/118/119/122/123）：分支与 HEAD 确认 → spec 定义/产生点 grep → `sed -n '1995,2035p' vllm_ascend/attention/dsa_v41.py`（build 分发逻辑）→ `sed -n '28,90p' / '150,175p' / '260,285p' vllm_ascend/core/deepseek_v41.py`（folded 孪生打包结构）。

修复前代码（事件 191 读取 model_runner_v1.py:4010-4037，其中原"组级跳过"判断即下方 diff 的 `-` 行）。

修复操作（事件 199，edit 工具调用，oldString→newString；事件 200 确认 Edit applied successfully）。

## 机制与判别

> 根因是跳过判断的粒度错误：原实现先按 kv-cache-group 粒度 all(isinstance(s, DeepseekV41IndexerFoldedSpec)) 判断整组跳过，但 folded 孪生与 token-indexed 兄弟层按 slot 打包共居 mixed full 组，all(...) 恒为 False，跳过永不生效，builder.build() 收到 folded spec 即抛 TypeError。

> 修复把跳过降到 attention-group 粒度：循环内对 self.attn_groups[kv_cache_gid][attn_gid].kv_cache_spec 做 isinstance 判断后 continue；py_compile 语法通过、全文件 builder.build() 调用点审计仅一处受影响、zeroer 迭代器只消费 backend/layer_names 不受影响；运行时验证（NPU pytest/serve smoke）因本机无 torch_npu 环境未在轨迹内完成。

修复前后完整 diff（事件 226，`git diff` 输出逐字；净 +6/-6 行）：

```python
-            # The folded indexer twin is written by indexer_prologue_k or the
-            # D-side import mirror; nothing in the forward pass consumes its
-            # attention metadata, so skip its builder pass entirely.
-            if group_specs and all(
-                isinstance(s, DeepseekV41IndexerFoldedSpec)
-                for s in group_specs.values()
-            ):
-                continue
             for attn_gid in range(len(self.attn_groups[kv_cache_gid])):
+                # The folded indexer twin is written by indexer_prologue_k or
+                # the D-side import mirror; nothing in the forward pass
+                # consumes its attention metadata. Folded twins share the
+                # mixed "full" group with their token-indexed siblings (their
+                # planes are packed into the same slot), so the skip must
+                # happen at the attention-group granularity, not per
+                # kv-cache-group.
+                if isinstance(
+                    self.attn_groups[kv_cache_gid][attn_gid].kv_cache_spec,
+                    DeepseekV41IndexerFoldedSpec,
+                ):
+                    continue
                 _build_attn_group_metadata(
```

机制要点：folded 孪生缓存（`indexer_prologue_k` 或 D 侧导入镜像写入，前向无消费者）与其 token-indexed 兄弟层**打包进同一 mixed "full" cache group**（`DeepseekV41FullSpec.is_uniform_with_collection` 允许 folded 与 compress_ratio 1/2 的兄弟共存），因此"整组皆 folded"的前提在真实布局下不可能成立，组级 `all(...)` 判断是死条件。

判别：
- 与 `is_v41_draft_swa_spec` 的"纯 draft 组"跳过（事件 191 中另一处 `continue`）不同——纯 draft 组确实整组同质，组级判断成立；folded 组是混合组，必须细到 attn-group。
- 该崩溃是启动即崩（确定性），与长稳压测中的接受率衰减/精度问题无关；后续同会话出现的 Mqsmla AICore 崩溃、GPQA 精度掉点为独立问题（见 [DeepSeek-V4.1 Mqsmla AI Core 崩溃根因：预计算 cmp_topk_length 位置上界与 -1 填充索引的 gap 导致非法寻址](deepseek_v41_mqsmla_core_cmp_topk_length.md) 与 notes）。

## 验证信号

| 结论 | 信号（事件） | 证据等级 |
|---|---|---|
| 分支/HEAD/spec 定义与产生点 | 来源记录:118（git branch/log + grep 输出） | 工具结果（客观） |
| 修复前组级死条件代码 | 来源记录:191（model_runner_v1.py:4010-4037 读取） | 工具结果（客观） |
| edit 应用成功 | 来源记录:200（"Edit applied successfully"） | 工具结果（客观） |
| 语法通过 | 来源记录:204（`python3 -m py_compile` 输出 "syntax OK"） | 工具结果（客观，仅语法级） |
| 最终 diff 与调用点审计 | 来源记录:226（git diff + grep 确认 143/4028 两处引用） | 工具结果（客观） |
| 环境缺 torch_npu | 来源记录:222（ModuleNotFoundError: No module named 'torch_npu' / 'vllm'） | 工具结果（客观） |

验证等级声明：**修后验证为静态级**（py_compile 语法通过 + `builder.build()` 调用点全文件审计：3855/3932 在被跳过函数内、3984 只做 isinstance、5334/6245 的 zeroer 迭代器只用 backend/layer_names）。运行时验证命令已在轨迹内给出但未执行（本机无 NPU 环境）：

```bash
pytest -sv tests/ut/worker/test_model_runner_v1.py tests/ut/attention/test_dsa_v41_private_circle.py
```

后续会话用户口头反馈"现在不崩溃了，但是精度严重掉点"（事件 844）——用户叙述，按纪律不作为客观验证信号，仅作线索记录。ruff 检查未能执行（`ruff: command not found`，事件 209）。

## 适用与失效边界

- 适用：vllm-ascend V27-dsv4.1 一带、任何引入 `DeepseekV41IndexerFoldedSpec` 且其孪生层与 token-indexed 兄弟共居混合 cache group 的版本；症状为 `_build_attention_metadata → builder.build()` 抛 "Unsupported V4.1 cache spec"。
- 修复语义边界：跳过的前提是 folded 孪生前向无消费者（由 `indexer_prologue_k`/D 侧导入镜像写入）；若未来某前向路径开始消费 folded 元数据，该跳过需重新评估。
- 部署注意：报错环境 `/opt/vllm-ascend-dsnext` 部署版与仓库有约 130 行偏移，修复后需重新构建部署镜像（轨迹内提示）。
- 失效/回退：若运行时验证发现 attn-group 粒度跳过导致某消费路径缺元数据，回退方案是 dsa_v41 build() 内对 folded spec 返回惰性（inert）元数据兜底（同会话后续确实补充了该防御纵深与测试，事件 348/351/355，属后续扩展）。
- 本修复不解决 dspark 接受率衰减、Mqsmla AICore 崩溃或 GPQA 精度掉点（同会话独立问题）。
