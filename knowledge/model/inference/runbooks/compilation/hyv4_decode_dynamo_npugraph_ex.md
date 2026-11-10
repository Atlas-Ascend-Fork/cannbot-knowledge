---
{
  "type": "Runbook",
  "title": "HYV4 Decode 29 处 Dynamo 图中断消除配方：npugraph_ex 整图捕获 + 0 重编译 + 同会话 decode 4×提速",
  "description": "按六类根因逐项修复（.is_npu 改 .device.type、FA actual_seq_* 改 list[int]、decode 图内跳过 DSA indexer、静态张量原地更新 + clone_input、融合全开规避 nonzero、import 外提）后，torch._dynamo.explain 从 30 graph/29 break 达到 1 graph/0 break，npugraph_ex fullgraph=True, dynamic=True 捕获成功且 kv_len 递增全程 0 重编译；同会话 A/B decode 单步中位数 17.289ms→4.353ms（比值 0.2518），图捕获开销 14252.1ms 仅 warmup 一次性；图 vs 非图 decode cos≈1.0、argmax 7/7，端到端 token 与非图路径逐位一致，reviewer 独立复跑确认。",
  "tags": [
    "task.debugging",
    "topic.compilation",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-09T09:37:53Z",
  "platforms": [
    "950"
  ]
}
---

# HYV4 Decode 29 处 Dynamo 图中断消除配方：npugraph_ex 整图捕获 + 0 重编译 + 同会话 decode 4×提速

## 适用场景

- 模型/框架：HYV4（`hy_v4`，MLA + DSA + iHC + 256 专家 MoE + sink）独立部署，阶段 2 Paged MLA + FA v2（`npu_fused_infer_attention_score_v2`，`TND_NTD`）+ 阶段 3 torch_npu 融合全开（MoE experts/router、RMSNorm、MLP SwiGLU、RoPE）之上的 Decode 图模式改造。
- 平台/版本：Ascend950PR_9589 单卡，CANN 9.1.0，torch 2.12.0+cpu，torch_npu 2.12.0（npugraph_ex 后端）；GE 因 protobuf 缺失不可用（见[HYV4 Decode 入图前的 Dynamo 图中断六类根因与最小判别探针（Ascend npugraph_ex 适配）](hyv4_decode_dynamo_ascend_npugraph_ex.md)）。
- 工作负载：L=4 缩减配置 6.039B、固定种子随机权重 seed=1234、batch=1、13 token prompt、单 token decode 步；无量化（BF16 + fp32-keep 模块）。
- 修复前状态（before）：decode 前向 `torch._dynamo.explain` 30 graph / 29 break（`.scratch/graph_break_fused.log`），`fullgraph=True` 编译失败于 `.is_npu`，`fullgraph=False` 仅能以 29 中断的非干净图运行（~11.38 ms/步含 warmup）。

## 触发与观测

修复的失败基线（融合全开、L=4、真实 paged decode 前向，`torch._dynamo.explain`）：

```
GRAPH_COUNT 30
GRAPH_BREAK_COUNT 29
```

```
BREAK[0] Data-dependent branching
    at modeling_hy_v4.py:991 forward
    at modeling_hy_v4.py:94 forward
...
BREAK[7] Error when attempting to resolve op packet
    at modeling_hy_v4.py:558 _forward_paged
```

fullgraph=True 首报（`.scratch/graph_compile_probe.log` 逐字要点）：`Developer debug context: attempted to jump with GetAttrVariable(TensorVariable(), is_npu)`。

## 探针与操作

按六类根因（A–F）逐项修复，全部修改限定在 `models/modeling_hy_v4.py`、`runner_hy_v4.py`、`config/hy_v4.yaml`：

1. **A（.is_npu → .device.type，6 处）**：RMSNorm / apply_rotary_pos_emb / _apply_rotary_half_packed / MLP / TopkRouter / Experts 的分支条件全部替换。以 RMSNorm 为例（edit newString 逐字）：

```
        # Stage-5: ``.is_npu`` on an intermediate tensor is a data-dependent
        # branch for Dynamo; ``.device.type`` is resolved statically at trace.
        if _fusion_enabled("rms_norm") and hidden_states.device.type == "npu":
            gamma = self.weight
```

2. **B（FA 长度改 list[int]）**：`_forward_paged` 新增 `actual_seq_qlen/actual_seq_kvlen` 形参，图分支改用入参、eager 分支保持 cache 张量字段（edit newString 逐字）：

```
        if graph_decode:
            is_prefill = False
            fa_mask = None
            seq_qlen = actual_seq_qlen
            seq_kvlen = actual_seq_kvlen
        else:
            is_prefill = paged_cache.is_prefill
            fa_mask = paged_cache.fa_mask if is_prefill else None
            seq_qlen = paged_cache.actual_seq_qlen
            seq_kvlen = paged_cache.actual_seq_kvlen
        attn_out, lse = torch_npu.npu_fused_infer_attention_score_v2(
            q_nope_abs, nope_view, nope_view,
            query_rope=q_rot, key_rope=rope_view,
            atten_mask=fa_mask,
            actual_seq_qlen=seq_qlen,
            actual_seq_kvlen=seq_kvlen,
            block_table=paged_cache.block_table,
```

3. **C（decode 图内跳过 DSA indexer、is_prefill 固定 False）**：`graph_decode` 分支直接沿用 `prev_topk_indices`，不调用 `indexer.forward_paged`（其 `[:kv_len]` 切片与逐步 mask 为动态）；`HYV4Model.forward` 在 graph 模式下不再构造默认 causal mask（decode `sparse_mode=0` 无需 mask）。当前规模 `index_topk(2048) >= kv_len`，indexer top-k 本就不被 FA 消费，跳过等价。
4. **D（静态张量原地更新）**：`HyV4PagedCache` 增 `graph_decode`/`graph_slot_mapping`（`torch.zeros(1, dtype=torch.int32)`）；新增固定形状单 token decode 入口（最终代码逐字）：

```
    # ------------------------------------------------------------------ #
    # Stage-5 decode graph entry
    # ------------------------------------------------------------------ #
    @torch.no_grad()
    def decode_graph(
        self,
        input_ids: torch.LongTensor,
        position_ids: torch.LongTensor,
        actual_seq_qlen,
        actual_seq_kvlen,
    ) -> "HyV4CausalLMOutput":
```

   其内部调用 `self.forward(input_ids=..., attention_mask=None, position_ids=..., past_key_values=self.graph_cache, use_cache=True, logits_to_keep=1, actual_seq_qlen=actual_seq_qlen, actual_seq_kvlen=actual_seq_kvlen)`。Runner 以 `torch.compile(self.model.decode_graph, backend="npugraph_ex", fullgraph=True, dynamic=True, options=compile_options)` 编译，`clone_input=True`（Runner 侧工件见[npugraph_ex 仅 Decode 入图部署模式：静态输入原地更新 + list[int] replay + 一键回退与依赖门控降级](npugraph_ex_decode_list_int_replay.md)）。
5. **E（融合全开规避 nonzero）**：不单独处理——图模式门控要求全部融合开启，融合路径无 `torch.nonzero`。
6. **F（import 外提）**：模块顶部 guarded `import torch_npu`（CPU-only 可导入），删除 5 处函数内 import。
7. **长 prompt overflow 门控修复（latent bug）**：prefill/decode 共用同一 paged cache 时，长 prompt（> prefill_chunk）的 eager q_len=1 余量步骤不应误入图分支；门控改为同时要求 FA 长度入参非空（最终代码逐字）：

```
        # ``graph_decode`` is a compile-time constant for the decode graph, but
        # the *same* paged cache is reused by the eager prefill path and by the
        # eager q_len=1 overflow steps of a long prompt (> prefill_chunk). Those
        # never pass the ``list[int]`` FA lengths, so requiring them here keeps
        # every eager call on the original path.
        graph_decode = (
            paged_cache.graph_decode
            and not paged_cache.is_prefill
            and actual_seq_qlen is not None
            and actual_seq_kvlen is not None
        )
```

## 机制与判别

- 按六类根因逐项修复（.is_npu 改 .device.type == "npu" 共 6 处、FA actual_seq_qlen/kvlen 改传 list[int]、decode 图内跳过 DSA indexer、Runner 预分配静态张量原地更新并开 clone_input=True、保持阶段 3 融合全开以规避 nonzero、import torch_npu 外提模块顶部）后，torch._dynamo.explain(decode_graph) 达到 GRAPH_COUNT=1 / GRAPH_BREAK_COUNT=0，npugraph_ex fullgraph=True, dynamic=True 捕获成功且 kv_len 递增全程 0 次重编译。
  - 判别依据：修复前同探针为 30/29 且 fullgraph=True 首报 `.is_npu`；修复后 explain 输出逐字为 `GRAPH_COUNT 1` / `GRAPH_BREAK_COUNT 0`；`torch._logging.set_logs(recompiles=True)` 下 kv_len 逐步递增（q→q+10）无任何 recompile 日志；decode 逐步 cos 1.0–1.000003 排除"图未真实生效/隐藏 fallback"（隐藏 fallback 会退化为 29 中断 partial-graph，性能与 cos 不会同时达标）。
  - 中间探针（修复后、最终门控前）：npugraph_ex 编译成功，eager 23.942 ms、首次调用（含捕获）14153.269 ms、稳态图 4.455 ms/步、cos_vs_eager_min 1.0、无重编译。
- 精度结论（候选结论原文）：图模式 decode 输出与非图 eager 精度一致：decode 逐步 cos 1.0–1.000003、argmax 7/7 一致，prefill 图 vs 非图 cos 1.000001 且 argmax 一致；bash infer.sh 图模式生成 token [101453, 58721, 70389, 70389, 76480, 76480, 76480, 76480] 与阶段 3 非图路径逐位一致。
- 精度证据（同会话，模型只构建一次，`tools/verify_graph_decode.py --reps 12`）tool_result 逐字：

```
EXIT=0
prefill_cos_g_vs_e 1.000001 argmax True vs_golden 0.99988
decode cos_g_vs_e_min 1.0 argmax_match 7 / 7 vs_golden_min 0.990861
capture_ms 14252.1
timing {"eager_decode": {"median": 17.289, "min": 15.052, "max": 31.467}, "graph_decode": {"median": 4.353, "min": 3.889, "max": 4.689}, "graph_over_eager": 0.2518}
recompiles:
0
```

- 未验证/假设：`npu_fused_infer_attention_score_v2.out` 的 deprecated aliasing UserWarning 在本版本结果正确，跨 torch_npu 版本风险未验证；警告原文、回退方式及版本边界见 [npugraph_ex Decode 图模式部署与验证](npugraph_ex_decode_list_int_replay.md)。捕获开销 ~14 s 是单次观测，随模型/图规模变化。

## 验证信号

仅列本组来源观测轨迹内实际观测到的信号（Ascend950PR_9589 单卡；随机权重 seed=1234）：

- **中断消除**：`explain` 达到 GRAPH_COUNT=1 / GRAPH_BREAK_COUNT=0（修复前 30/29）；修复后复跑两次一致（门控修复前后各一次）。

```
GRAPH_COUNT 1
GRAPH_BREAK_COUNT 0
```

- **精度**：decode 逐步 cos 1.0–1.000003、argmax 7/7、maxdiff ≤ 1 ULP 量级；prefill 图 vs 非图 cos 1.000001 且 argmax 一致；图 vs CPU golden min 0.990861 与非图 vs golden 逐 step 完全相等（图精确复现非图）。`bash infer.sh` 图模式 decode 稳态 ~4.5–5.0 ms，生成 token 与阶段 3 非图路径逐位一致。
- **性能（performance_gain，同会话 A/B）**：同会话 A/B（模型只构建一次、teacher-forced 单 token decode、12 reps 取中位数）下，阶段 3 全融合 eager decode 单步中位数 17.289 ms，npugraph_ex 图模式 4.353 ms（比值 0.2518，约 4.0×）；图捕获首次调用开销 14252.1 ms，仅 warmup 一次性发生，不计入稳态。早前一轮同会话 A/B 为 21.534 → 4.36 ms（比值 0.2025），方向一致、绝对值随宿主负载漂移，以比值为准。
- **回退**：`HYV4_EXE_MODE=eager bash infer.sh` 无图编译日志，token 逐位一致。
- **reviewer 独立复现**：reviewer 独立复跑确认 explain 1 graph/0 break 可复现、verify 日志 0 次 recompile，并独立测得图 vs 非图 decode cos_min 1.0、argmax 7/7、同会话比值 0.27（16.479 ms → 4.449 ms）。reviewer 另以 4 路同会话累计 A/B 测得 stage0 未融合 56.682 ms → 融合 18.781 ms → paged 20.282 ms → 图 4.718 ms（stage5_over_stage0_nofusion 0.0832，单次观测）。

## 适用与失效边界

- 版本条件：torch 2.12.0+cpu / torch_npu 2.12.0 / CANN 9.1.0 / Ascend950PR_9589；npugraph_ex 为试验特性（官方注明暂不支持商用）。Dynamo 对 `.device.type` 的静态折叠与 `SymInt[]` list 入参行为依赖 torch/Dynamo 版本。
- 规模条件：结论在 L=4、batch=1、单 token decode、KV ≤ 23、随机权重下取得；未覆盖 batch>1 不等长 packed、长上下文（kv_len > 2048 时 DSA 不再 no-op，图内跳过 indexer 不再等价，需另走 sparse FA 路径）、多卡。
- 依赖条件：图模式要求 Paged FA 路径 + 阶段 3 融合全开（部分融合关闭会因 eager MoE `nonzero` 无法入图，门控自动降级 eager）。
- 性能边界：decode 提速主要来自 launch/host 开销消除（融合后 decode 已是 launch-bound 的场景）；若模型/规模变为 compute-bound，比值不可外推。图捕获开销 ~14 s 为一次性 warmup 成本，短生命进程或频繁重启场景需摊销评估。
- 精度口径：cos/argmax 与 token 一致性为随机权重下的粗粒度口径；真实权重下需重做精度比对。宿主负载漂移使绝对耗时不可跨时段比较，只可引用同会话比值。
- 回退条件：`exe_mode: eager` / `HYV4_EXE_MODE=eager` 一键回退并逐位复现；若 npugraph_ex 升级后 FA `.out` aliasing 由警告变错误，需先治理该告警再启用。
