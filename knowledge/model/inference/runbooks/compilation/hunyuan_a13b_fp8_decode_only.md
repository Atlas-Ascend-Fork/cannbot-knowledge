---
{
  "type": "Runbook",
  "title": "Hunyuan-A13B-FP8 Decode-only npugraph_ex 图模式适配：三类图中断修复与 Runner 集成",
  "description": "在 Ascend950PR 上为 Hunyuan-A13B-Instruct-FP8（W8A8 FP8、细粒度 MoE、Paged KV + FA v2 TND 路径）做 npugraph_ex 图模式适配：修复三类图中断（RoPE `.item()` 派生动态 seq_len 改为捕获前建表冻结、FA v2 长度改传 host List[int]、`repeat_interleave` 加 `output_size=S*K` 钉静态形状），Runner 仅在 batch=1 时 `torch.compile(model.decode, backend=\"npugraph_ex\", fullgraph=True, dynamic=True)`，Prefill 保持 eager、batch>1 回退 eager。改造后 graph_break_count 12→0、无重编译，图模式贪心 token 与 eager 及 CPU golden 一致，单次观测 Decode 稳态 18.62 ms/step vs eager 112.85 ms/step（约 6.06×）。",
  "tags": [
    "task.implementation",
    "topic.compilation",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# Hunyuan-A13B-FP8 Decode-only npugraph_ex 图模式适配：三类图中断修复与 Runner 集成

## 适用场景

- 模型/框架：Hunyuan-A13B-Instruct-FP8（80.39B 细粒度 MoE，32 层，GQA 32/8 heads，head_dim 128，Top-8/64 专家 + 每层 1 个共享 MLP；W8A8 FP8，E4M3，静态激活 per-tensor scale），独立部署自管 Runner（Paged KV block_size=128 + FA v2 TND `sparse_mode=3` 路径，阶段 3 融合算子全开）。
- 平台/版本：Ascend950PR_9589 单卡；CANN 9.1.0（需含 ascend950 `ops_nn` 子包）；torch 2.12.0+cpu / torch_npu 2.12.0 / Python 3.12；`torch_npu.dynamo.npugraph_ex` 可直接 import（torchair/GE 因环境缺 protobuf 不可用）。
- 目标与工作负载：仅对 Decode 阶段启用 npugraph_ex（`fullgraph=True, dynamic=True`）；Prefill 按 skill 硬约束保持 eager；batch=1 decode（输入 21 token、输出 8 token）为验证负载。缺失信息：其它芯片型号、其它 torch_npu 版本未在轨迹内验证。

## 触发与观测

对阶段 3 融合后 eager 路径做图模式分析（见 compilation/llm_decode_torch_dynamoexplain_npugraph_ex.md）发现三类图中断，未改造代码直接 `torch.compile(backend="npugraph_ex")` 时：

- `fullgraph=True` 失败：`Could not guard on data-dependent expression u0 + 1 > 0 ... Caused by: if seq_len > self.m`（RoPE 分支 guard 失败）。
- `fullgraph=False` 失败：`aclrtMemcpy, error code is 107030`（capture 阶段即不可用）。
- 小模型 `torch._dynamo.explain`：`===SUMMARY=== graph_break_count = 12 graph_count = 13`（去重 7 条原因）。

因此当前代码不能直接入图，必须先修图中断。

## 探针与操作

改造分五部分（文件：`models/modeling_hunyuan.py`、`runner_hunyuan_a13b_fp8.py`、`config/hunyuan_a13b_fp8.yaml`；新增 `tools/verify_graph_stage5.py`）。

**（1）R3/前置——`ForwardMetaData` 增加 host list 长度字段**（FA v2 op schema 为 `SymInt[]?`，传 Tensor 强制 `aten._local_scalar_dense` 设备→host 同步并打断图）：

```
    block_size: int = 128
    # Graph-mode (npugraph_ex) Decode lengths: the FA op schema is ``SymInt[]``,
    # so passing a Tensor forces a device->host sync (``_local_scalar_dense``) and
    # a graph break. For Decode we therefore carry the lengths as host ``List[int]``
    # (Prefill keeps the cumulative Tensor form, unchanged, and stays eager).
    actual_seq_lengths_list_q: Optional[List[int]] = None
    actual_seq_lengths_list_kv: Optional[List[int]] = None
```

**（2）R1——RoPE 去 `.item()` + 静态表（`_prepared` 门控，eager 保留动态增长语义；注意初版曾因 eager 不增长触发静默越界，见 [RoPE 静态表冻结后 eager 路径 NPU 越界 gather 静默出错：`_prepared` 门控修复](../runtime/rope_eager_npu_gather_prepared.md)）**：

```
221:     def build_cache(self, seq_len, device, dtype):
222:         """Precompute the cos/sin tables up to ``seq_len`` (idempotent)."""
223:         if (self.cos_cached is not None and self.max_seq_len_cached >= seq_len
224:                 and self.cos_cached.device == device and self.cos_cached.dtype == dtype):
225:             return
226:         self._set_cos_sin_cache(seq_len, device, dtype)
227:
228:     def prepare(self, seq_len, device, dtype):
229:         """Freeze the table for graph capture: build it and mark it complete."""
230:         self.build_cache(seq_len, device, dtype)
231:         self._prepared = True
232:
233:     def forward(self, x, position_ids=None):
234:         # Eager path (``_prepared`` False): grow the table as positions increase,
235:         # exactly like the original dynamic RoPE. This branch is never traced
236:         # inside the compiled Decode graph because ``prepare`` has frozen the
237:         # table and each compiled step only reads it.
238:         if not self._prepared:
239:             need = (int(position_ids.max().item()) + 1 if position_ids is not None
240:                     else self.max_position_embeddings)
241:             if (self.cos_cached is None or need > self.max_seq_len_cached
242:                     or self.cos_cached.device != x.device or self.cos_cached.dtype != x.dtype):
243:                 self._set_cos_sin_cache(need, x.device, x.dtype)
244:         return self.cos_cached, self.sin_cached
```

顶层 `HunYuanModel.forward` 删除 `seq_len = int(position_ids.max().item()) + 1`，改为 `cos_sin = self.layers[0].self_attn.rotary_emb(hidden_states, position_ids=position_ids)`；捕获前由 `prepare_graph` 一次性冻结表（RoPE 表全层共享，只需 layer 0）：

```
908:     def prepare_graph(self, max_seq_len, dtype=torch.bfloat16):
909:         """Materialise graph-invariant buffers (RoPE cos/sin tables) before capture.
910:
911:         The RoPE table is layer-agnostic (all layers share the same rotary), so
912:         only layer 0's is needed; it is read by every layer via the shared
913:         ``cos_sin`` returned from ``forward``.
914:         """
915:         p = next(self.parameters())
916:         self.layers[0].self_attn.rotary_emb.prepare(max_seq_len, p.device, dtype)
```

**（3）R2/R3——Decode 入口拆分 + FA 长度 host list 分支**（新增 `HunYuanMoEV1ForCausalLM.decode()`，固定 `is_prefill=False`，仅编译该入口）：

```
733:     def _fa_forward(self, query_states, key_states, value_states, k_cache, v_cache, fm):
734:         # FA wants cumulative Q lengths and (cumulative prefill / direct decode) KV lengths.
735:         # Decode under npugraph_ex passes host ``List[int]`` (op schema is ``SymInt[]``);
736:         # a Tensor here would force a device->host sync + graph break.
737:         if not fm.is_prefill and fm.actual_seq_lengths_list_kv is not None:
738:             actual_seq_qlen = fm.actual_seq_lengths_list_q
739:             actual_seq_kvlen = fm.actual_seq_lengths_list_kv
740:         else:
741:             actual_seq_qlen = torch.cumsum(fm.q_lens, dim=0).to(torch.int32)
742:             if fm.is_prefill:
743:                 actual_seq_kvlen = torch.cumsum(fm.kv_lens, dim=0).to(torch.int32)
744:             else:
745:                 actual_seq_kvlen = fm.kv_lens.to(torch.int32)
```

注意：TND 布局下 `actual_seq_lengths_list_q` 必须为 cumulative（`list(range(1, B+1))`），batch>1 传 `[1]*B` 会触发 FA tiling 校验失败（见 [TND 布局 FA v2 host list `actual_seq_lengths_list_q` 在 batch>1 必须为 cumulative](../runtime/tnd_host_list_actual_seq_lengths_list_q_batch.md)）。

**（4）M——MoE 去 `repeat_interleave` 动态形状（钉 `output_size`；M-b 替代方案实测不可行，见 [M-b 方案不可行：`npu_moe_init_routing_v2` 的 scale/第 4 输出不承载 per-expert input_scale](../runtime/npu_moe_init_routing_v2_scale_per_expert_input_scale.md)）**：

```
        # ---- w13 = [gate | up] ----
        # ``output_size=S*K`` pins the repeat output to a static shape: without it
        # Dynamo treats the (expert-count-derived) length as a dynamic/data-dependent
        # shape and breaks the graph.
        row_is13 = torch.repeat_interleave(self.w13_input_scale, tokens_per_expert, output_size=S * K)  # [M]
```

以及 w2 侧：

```
        row_is2 = torch.repeat_interleave(self.w2_input_scale, tokens_per_expert, output_size=S * K)
```

**（5）T——Runner 集成**：yaml `exe_mode: "npugraph_ex"`（切回 `"eager"` 即回退）；`TASK_QUEUE_ENABLE=1` 在 import torch_npu 前设置；仅 batch==1 编译，batch>1 回退 eager（MoE `_fused_forward` 的 `if S>1` 容量兜底分支含 host `.item()` 同步，且 `int(counts.max().item())` 在 batch>1 会触发图中断）：

```
    def _build_decode_fn(self, batch_size):
        """Return the callable used for the Decode step.

        Prefill always stays eager. Decode uses ``npugraph_ex`` only when
        requested *and* the batch is 1: the fused MoE capacity-overflow branch
        (``S > 1``) performs a host ``.item()`` sync, so batch > 1 falls back to
        eager. Graph capture is selected via the ``exe_mode`` yaml key.
        """
        if self.exe_mode != "npugraph_ex" or batch_size > 1:
            if self.exe_mode == "npugraph_ex" and batch_size > 1:
                logger.warning("npugraph_ex requested but batch=%d > 1; Decode falls back to eager",
                               batch_size)
            return self.model.decode
        options = {
            "inplace_pass": True,
            "input_inplace_pass": True,
            "pattern_fusion_pass": True,
            "reuse_graph_pool_in_same_fx": True,
            "remove_noop_ops": True,
            "clone_input": False,
            "clone_output": False,
        }
        logger.info("compiling Decode with npugraph_ex (fullgraph=True, dynamic=True) ...")
        return torch.compile(
            self.model.decode,
            backend="npugraph_ex",
            fullgraph=True,
            dynamic=True,
            options=options,
        )
```

Decode 循环按步构造 list 长度（`actual_seq_lengths_list_q=list(range(1, batch_size + 1))`、`actual_seq_lengths_list_kv=kv_lens_step_list`）传入 `ForwardMetaData`；batch 变化时重建 `_decode_fn`。

失败路线（不可采用）：未修图中断直接编译（fullgraph True/False 均失败，见"触发与观测"）；RoPE 只冻结不保留 eager 增长语义（触发静默越界，见 [RoPE 静态表冻结后 eager 路径 NPU 越界 gather 静默出错：`_prepared` 门控修复](../runtime/rope_eager_npu_gather_prepared.md)）。

## 机制与判别

- 修复三类图中断（RoPE `.item()` 派生动态 seq_len、FA v2 长度 Tensor 触发 `aten._local_scalar_dense`、`repeat_interleave` 数据依赖输出形状）后，npugraph_ex `fullgraph=True, dynamic=True` 对全模型 batch=1 Decode 捕获成功，小模型 `torch._dynamo.explain` 的 decode 路径 graph_break_count 由改造前的 12 降至 0。
- 三类中断的机制各不相同且可区分：`.item()` 是 Dynamo 强制中断点；FA v2 的 ATen schema 将长度声明为 `SymInt[]?`，eager 绑定下传 Tensor 会经 `aten._local_scalar_dense` 转 host 标量（每层每步 3 次中断）；`aten.repeat_interleave.Tensor` 输出形状依赖输入 Tensor 数据，属数据依赖动态形状（每层每步 3 次中断）。
- 图复用机制：RoPE 表、`atten_mask[2048,2048]`、静态 `block_table`、paged KV cache 均图外预建且地址固定，图内只读/原地更新（`npu_scatter_nd_update_`），故 `dynamic=True` 下 kv 逐步增长不需要重编译。
- 未验证推断（假设）：MoE `if S>1` 容量分支对 batch>1 图模式的改造（无 `.item()` 的 capacity mask）未实施，轨迹内 batch>1 一律回退 eager。

## 验证信号

均在本机（Ascend950PR_9589 单卡、CANN 9.1.0、torch/torch_npu 2.12.0）实测，证据等级：工具运行日志/退出码 + 独立 reviewer 复跑。

- 编译：实施者与 reviewer 各自独立跑小模型探针，均得 `===SUMMARY=== graph_break_count = 0 graph_count = 1` 且 `NPUGRAPH_EX OK`（实施者事件 227、reviewer 事件 105）；全模型 `compiling Decode with npugraph_ex (fullgraph=True, dynamic=True)` 捕获成功。
- 重编译：warmup 后无重编译：`TORCH_LOGS=recompiles` 下全模型图模式多步 Decode 无任何 `Recompiling` 日志（graph 日志中唯一 recompil 命中为 TORCH_LOGS 环境变量回显行）。（reviewer grep `Recompiling|Compiling|graph break` 为 `(none)`，事件 135）
- 精度对齐：图模式贪心 token `[27, 9399, 397, 60704, 627, 524, 9399, 29]` 与 eager 逐 token 完全一致，前 4 token 与 `agentic/golden/cpu_golden` 完全一致；prefill logits 余弦 0.9998937845230103（与阶段 0 记录一致，Prefill 未改）。（reviewer 独立复跑 `compare_golden_npu.py` RC=0，输出重定向 /tmp 未触碰产物）
- 性能：单次观测（同会话、同机、batch=1、输入 21 token）：Decode 单步时延由 eager 平均 112.85 ms 降至图模式稳态平均 18.62 ms（约 6.06×，首步捕获 177.82 ms 剔除）；Prefill 保持 eager，166.01→162.79 ms（-1.9%，噪声范围）。实施者独立一轮测得 eager 92.94–108.78 ms、图模式稳态 18.28–19.39 ms，量级一致。
- 相对原始基线（阶段 0 eager：Prefill 1923.02 ms / Decode 1740.72 ms，`agentic/baseline/baseline_metadata.json`）的累计变化：Prefill -91.5%、Decode -98.9%（93.5×）——该累计值包含阶段 2/3 优化贡献，不能全部归因图模式。
- 回退路径：batch>1 自动回退 eager：`_build_decode_fn` 仅在 batch==1 时编译 `model.decode`，batch>1 打告警并回退；batch=1 图 + batch=3 packed eager 的 `reviewer_multibatch_check` RESULT: PASS（逐请求 greedy token 一致）。

## 适用与失效边界

- 版本/平台：torch_npu 2.12.0、CANN 9.1.0、Ascend950PR_9589 单卡上验证；npugraph_ex 官方标注为实验特性（暂不支持商用），GE 路径在本环境因缺 protobuf 不可评估，未做对比。
- batch 条件：图模式仅覆盖 batch=1 decode（S=1）；batch>1 回退 eager（MoE 容量分支的 `.item()` 未改造），混跑 batch 变化时需重建编译入口。
- Prefill 边界：Prefill 保持 eager 是硬约束（变长输入），本方案未评估 Prefill 入图。
- 精度边界：本验证仅覆盖固定单 prompt（21 token、贪心、前 4 token 与 golden 比对 + prefill 余弦）；更长序列、更大 batch、beam 采样未验证。
- 性能边界：6.06× 为单次运行观测（均值口径见上），非多轮基准；首步含图捕获 177.82 ms，短输出场景需摊销。
- 回退条件：yaml `exe_mode` 切回 `"eager"` 即整体回退；出现精度分歧时优先检查 RoPE 表增长语义与 FA list 长度构造（见 [RoPE 静态表冻结后 eager 路径 NPU 越界 gather 静默出错：`_prepared` 门控修复](../runtime/rope_eager_npu_gather_prepared.md) / [TND 布局 FA v2 host list `actual_seq_lengths_list_q` 在 batch>1 必须为 cumulative](../runtime/tnd_host_list_actual_seq_lengths_list_q_batch.md)）。
