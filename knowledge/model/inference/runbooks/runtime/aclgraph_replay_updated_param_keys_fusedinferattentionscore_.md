---
{
  "type": "Runbook",
  "title": "ACLGraph replay 输入更新与静态编译产物的区分：FA 参数名更新、ATB 参数位置更新及单次 dump 边界",
  "description": "在本次 torchair npugraph_ex 源码快照中，FA v1/v2 通过 updated_param_keys 登记参数名更新，ATB paged attention 通过 updated_param_indices 登记位置更新。同一 run 的 _debug 有4份 FA op-info，_opcompile 的10份 JSON 中没有 FA；这只证明本次 FA 未进入静态编译子集，不足以断言 API 在整个版本不支持静态编译。workspace 替换、replay 更新与静态 kernel 编译应分别核对。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "910"
  ]
}
---
# ACLGraph replay 输入更新与静态编译产物的区分：FA 参数名更新、ATB 参数位置更新及单次 dump 边界

## 适用场景

- 框架/机制：torchair npugraph_ex（随 torch_npu 2.10.0.post4 内置，源码仓 `${TORCHAIR_ROOT}/torchair/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py` 的 `_REPLACE_FUNC_MAP`）的 ACLGraph 捕获/重捕/replay 机制；以及 npugraph_ex 静态 Kernel 编译（`static_kernel_compile_outputs` 产物目录）。
- 平台：Ascend 910B3 真机（CANN 9.1.0 容器内核对代码；运行产物证据来自 `.torchair_cache` 内的 npugraph_ex smoke 测试运行目录）。
- 目标：判别两个易混淆的问题——"哪些算子在 ACLGraph replay 期需要更新输入参数（FA 更新）"、"op_compiler 静态编译是否支持 FusedInferAttentionScore"。

路径约定：`${TORCHAIR_ROOT}` 为torchair 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发（用户问题，事件 1036/1053）："需要fa更新的具体是安歇算子"、"静态编译支持fuseinferattentionscore算子吗"。这两个问题在排查 replay 期参数更新与静态编译产物时极易互相混淆：`static_kernel_compile_outputs/<run>/` 下同时有 `${pid}_debug`（全量算子信息）与 `${pid}_opcompile`（本次送入静态编译的算子子集）两个目录，只看 `_debug` 不能证明 FA 已被静态编译；本轨迹随后通过 `_opcompile` 目录更正了对本次运行的判断。

客观观测：

- 全仓 grep `actual_seq_lengths|actual_seq_lengths_kv|actual_shared_prefix_len|actual_seq_qlen|actual_seq_kvlen`（限 npugraph_ex，事件 1039）：赋值处只有 `acl_graph.py:114`（v1）与 `:127`（v2）两行，即只有两族 FA 的 `updated_param_keys`。
- 用户业务日志 `npugraph_ex_stream_20261015.log` 中 `acl_graph.py:310` 打印 `all updated inputs user nodes params: {...}`（事件 1011），内容与 `_REPLACE_FUNC_MAP` 登记完全一致。
- 同一 run（`ts20261013084304352847_pid1277329_outputs`）的目录切片（事件 1061）：`1277329_debug/` 14 个 json 含 4 份 FA op-info；`1277329_opcompile/` 10 个 json 中一个 FA 都没有。

## 探针与操作

探针 1（代码定位，事件 1039/1045/1049）：

```bash
grep -rIn "actual_seq_lengths\|actual_seq_lengths_kv\|actual_shared_prefix_len\|actual_seq_qlen\|actual_seq_kvlen" npugraph_ex/ --include=*.py
sed -n '96,135p' acl_graph.py    # _REPLACE_FUNC_MAP 登记
sed -n '132,186p' acl_graph.py   # ATB paged attention 登记（updated_param_indices）
```

探针 2（运行产物目录切片比对，事件 1056/1060/1061）：

```bash
B=<run>/ts..._pid1277329_outputs
ls $B/1277329_debug      # 全量算子信息 dump
ls $B/1277329_opcompile # 支持静态编译的算子子集（实际送 op_compiler）
```

关键操作纪律：判别本次运行是否送入静态编译，应比对 `_opcompile`（而非仅看 `_debug`）目录；`FusedInferAttentionScore_*.json` 文件名由「算子类型_dtype_format_shape_序号」构成，两个目录里同算子的序号不同，必须逐文件比对目录全集，不能只 grep 文件名是否存在。

## 机制与判别

判别 1（按名与按位置更新）——结论：该源码快照中按 `updated_param_keys` 登记的 FA 有两族：npu_fused_infer_attention_score（v1）更新 actual_seq_lengths、actual_seq_lengths_kv、actual_shared_prefix_len；npu_fused_infer_attention_score_v2（v2）更新 actual_seq_qlen、actual_seq_kvlen；同表中的 ATB _npu_paged_attention 与 _npu_paged_attention_splitfuse 不走 updated_param_keys，而是按 updated_param_indices（context_lens=7 / context_lens、seq_len=[4,6]）更新。

代码原文（`acl_graph.py:104-130`，锚点事件 1046 逐字）：

```
104: _REPLACE_FUNC_MAP = {}
105:
106: if hasattr(torch.ops.npu, "npu_fused_infer_attention_score"):
107:     _REPLACE_FUNC_MAP.update(
108:         {
109:             torch.ops.npu.npu_fused_infer_attention_score.default: StaticWorkspaceReplaceFunc(
110:                 get_workspace=torch.ops.npu._npu_fused_infer_attention_score_get_max_workspace.default,
111:                 out_operator=torch.ops.npu.npu_fused_infer_attention_score.out,
112:                 workspace_keys=["workspace"],
113:                 output_keys=["attention_out", "softmax_lse"],
114:                 updated_param_keys=["actual_seq_lengths", "actual_seq_lengths_kv", "actual_shared_prefix_len"],
115:             )
116:         }
117:     )
118:
119: if hasattr(torch.ops.npu, "npu_fused_infer_attention_score_v2"):
120:     _REPLACE_FUNC_MAP.update(
121:         {
122:             torch.ops.npu.npu_fused_infer_attention_score_v2.default: StaticWorkspaceReplaceFunc(
123:                 get_workspace=torch.ops.npu._npu_fused_infer_attention_score_v2_get_max_workspace.default,
124:                 out_operator=torch.ops.npu.npu_fused_infer_attention_score_v2.out,
125:                 workspace_keys=["workspace"],
126:                 output_keys=["attention_out", "softmax_lse"],
127:                 updated_param_keys=["actual_seq_qlen", "actual_seq_kvlen"],
128:             )
129:         }
130:     )
```

ATB 对照（同表 `acl_graph.py:132-147`）：`torch.ops.atb._npu_paged_attention.default` 登记 `get_workspace=None, workspace_keys=[], output_keys=[], updated_param_keys=[], updated_param_indices=[7]`（即按 arg index 更新 `context_lens`）；`_npu_paged_attention_splitfuse` 为 `updated_param_indices=[4, 6]`（`context_lens`、`seq_len`）。即 FA 走"参数名"更新、ATB paged attention 走"参数下标"更新，是两种不同登记形态。

判别 2（本次 FA 未进入静态编译子集）——结论：同一 run 中 FA 只出现在 `1277329_debug` 全量算子信息目录（4份 JSON），`1277329_opcompile` 的10份 JSON（Add/Mul/RealDiv/ReduceMean/Slice/MatMulV2）没有 FA。这是本次运行产物的范围，不能据此证明所有 shape、配置或整个版本的 op_compiler 均不支持 FA。

目录证据（锚点事件 1061 逐字）：

```
== _debug (全量) ==
Add_float16_NCHW_3_32_1_128_0.json
Add_float16_ND_128_128_1.json
FusedInferAttentionScore_float16_ND_3_32_1_128_10.json
FusedInferAttentionScore_float16_ND_3_32_1_128_11.json
FusedInferAttentionScore_float16_ND_3_32_1_128_12.json
FusedInferAttentionScore_float16_ND_3_32_512_128_13.json
MatMulV2_float16_ND_128_96_9.json
Mul_float16_NCHW_3_32_1_128_3.json
Mul_float16_NCHW_3_32_1_32_2.json
Mul_float16_NCHW_3_32_512_128_4.json
RealDiv_float16_NCHW_3_32_512_128_5.json
ReduceMean_float16_NCHW_3_32_512_128_7.json
ReduceMean_float16_ND_128_128_8.json
Slice_float16_NCHW_3_32_128_6.json

== _opcompile (支持静态编译) ==
Add_float16_NCHW_3_32_1_128_2.json
Add_float16_ND_128_128_5.json
MatMulV2_float16_ND_128_96_9.json
Mul_float16_NCHW_3_32_1_128_3.json
Mul_float16_NCHW_3_32_1_32_1.json
Mul_float16_NCHW_3_32_512_128_4.json
RealDiv_float16_NCHW_3_32_512_128_6.json
ReduceMean_float16_NCHW_3_32_512_128_7.json
ReduceMean_float16_ND_128_128_8.json
Slice_float16_NCHW_3_32_128_0.json
```

判别 3（workspace 与 replay 更新）——源码显示 `_REPLACE_FUNC_MAP` 为 FA 登记 `get_max_workspace`、`.out` 重载及 replay 更新参数。这与静态 kernel 编译是不同机制。事件1033的 op-info 摘录中，`key`/`value` 可见 `param_type: dynamic`，两行后段被截断；不能补写它们的 `value_depend`。`actual_seq_lengths_kv` 则完整显示 `param_type: optional` 与 `value_depend: True`。这些字段本身不能判定 FA 的静态编译支持范围；本次为何被排除仍未确认。

## 验证信号

（平台：Ascend 910B3 真机环境；证据等级：源码 grep + 既有运行产物目录证据，非本轨迹内端到端复验）

- 事件 1041：npugraph_ex 全仓 `updated_param_keys` 赋值只有 `acl_graph.py:114`（v1）与 `:127`（v2）两处。
- 事件 1046/1050：`_REPLACE_FUNC_MAP` FA v1/v2 与 ATB 两条目的逐字代码（上文原文）。
- 事件 1011：业务日志 `npugraph_ex_stream_20261015.log` 中 `acl_graph.py:310` 的 `all updated inputs user nodes params: {_npu_fused_infer_attention_score_get_max_workspace: [actual_seq_lengths, actual_seq_lengths_kv, actual_shared_prefix_len], npu_fused_infer_attention_score.out: [同上], _npu_fused_infer_attention_score_v2_get_max_workspace: [actual_seq_qlen, actual_seq_kvlen], npu_fused_infer_attention_score_v2.out: [同上]}`——运行时确认与代码登记一致（既有日志证据，单次抓取）。
- 事件 1057：`.torchair_cache` 场景同 run 计数 `_debug: 18 / _opcompile: 14 / _opcompile_selected: 0`（含 cache 目录内合并计数）。
- 事件 1061：`_debug` 14 个 json 含 4 份 FA，`_opcompile` 10 个 json 无 FA——FA 不进静态编译子集。
- 事件 1033：`key`/`value` 可见 `param_type: dynamic`（后段截断）；`actual_seq_lengths_kv` 为 `param_type: optional`、`value_depend: True`。

## 适用与失效边界

- 版本适用：判别基于 torch_npu 2.10.0.post4 内置 npugraph_ex（及同源 torchair 仓），Ascend 910B3 / CANN 9.1.0 与 9.3.0 环境下核对；其他版本 `_REPLACE_FUNC_MAP` 条目可能增删（登记形态用 `hasattr(torch.ops.npu, ...)` 守护，随算子可用性变化）。
- 方法适用：判别"replay 期更新输入参数的算子"看 `_REPLACE_FUNC_MAP` 中 `updated_param_keys` 非空条目（参数名更新）与 `updated_param_indices` 非空条目（下标更新，ATB paged attention）；判别本次是否送入静态编译，应比对 `_opcompile`；实际编译成功仍需编译结果/执行信号。
- 误判风险：`_debug` 中存在 op-info 不等于编译成功，`_opcompile` 中一次缺席也不等于 API 永不支持；`value_depend: True` 不能独自解释静态编译支持性或 replay 更新登记。
- 未验证边界：未用 `static_kernel_compile=True` 的最小 FA 用例复测确认 `_opcompile` 无 FA（结论基于既有运行产物目录）；排除 FA 进 `_opcompile` 的具体机制（上游 dump 阶段策略）为推断；`_opcompile_selected` 目录仅在未启用模型编译缓存时生成，启用缓存后实际使用 `_opcompile`。
- 停止/回退条件：若某版本 FA op-info 出现在 `_opcompile`，应怀疑上游 dump 策略变化，需以该 run 的目录切片重新判别；静态 kernel 编译（op_compiler）与 replay 期参数更新（_REPLACE_FUNC_MAP）是两条独立机制，不可互相推断。
