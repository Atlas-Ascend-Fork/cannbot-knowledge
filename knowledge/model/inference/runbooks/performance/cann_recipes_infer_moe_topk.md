---
{
  "type": "Runbook",
  "title": "cann-recipes-infer MoE TopK 三流分流编排与 vllm-ascend 移植的 join 点判别（分析）",
  "description": "cann-recipes-infer 的 K3 MoE decode 采用模型级 MoEContext 三流（shared/shared_comm/router）+ 11 槽事件池：router_stream 上 [gate GEMM(控核32,1)]→event3→[npu_moe_gating_top_k]→event4，与主流 [mx_quant→latent down→dispatch] 并行，event3 显式串行化两个 Cube MatMul 避免争抢。vllm-ascend 侧 gate GEMM+TopK 全在主流串行；topk 结果只在 dispatch 被消费，但 MC2 的 prepare 也消费 router_logits，故 join 必须放在 prepare 之前而非 TopK 之前。本卡为分析结论，未实现、未运行验证。",
  "tags": [
    "task.debugging",
    "topic.model_serving",
    "topic.mixture_of_experts"
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

# cann-recipes-infer MoE TopK 三流分流编排与 vllm-ascend 移植的 join 点判别（分析）

## 适用场景

- 框架/模型：cann-recipes-infer（裸机推理，PyTorch + torch_npu）的 Kimi K3 样例作为参照系；目标仓为 vllm-ascend `releases/v0.27.1rc`（K3 走 external router，MoE 为 Stable LatentMoE：896 routed experts、Top-16、1 shared expert、latent down 7168→3584、decode 用 MC2 EP32 + Shared TP8）。
- 目标：把 recipes 中"路由专家分流 + 路由 gating（gate GEMM + MoeGatingTopK）分流"的多流编排迁移到 vllm-ascend（其 shared-expert 多流 `multistream_overlap_shared_expert` 已有，但 gate+TopK 仍在主流串行）。
- 缺失信息：本卡是只读分析（用户明确"不要修改代码"），无实现、无运行验证；引用的 recipes 代码细节来自会话内研究子代理对源文件的报告（MODEL = models/kimi_k3/models/modeling_kimi_k3.py 等），主线会话未直接重读源文件。

## 触发与观测

触发（优化目标，代码事实）：vllm-ascend 中 K3 的 `AscendKimiMoE.forward` 里 `router_logits, _ = self.gate(hidden_states)`（gate GEMM）先于 `self.experts(...)`，而 TopK 位于 runner 深处（`routed_experts.forward_impl` 的 `_select_experts`）——**gate GEMM 与 TopK 全部在主流上、串行**，是 MoE 层内除共享专家外唯一未被重叠的计算段。观测来自子代理对两个仓库的调研（T523/T524）。

参照系观测（recipes，T523 逐字，decode 并行窗口总览）：

```
主流:      [mx_quant(latent)]→[latent down 7168→3584]→[MC2 dispatch]→[GMM1]→[SiTU+quant]→[GMM2]→[combine]→[latent up]→[Add]
router_stream: [event2]→[router GEMM(控核32,1)]→event3→[npu_moe_gating_top_k]→event4
comm_stream:   [event0]→[Shared AG]→event1 ·································· [event9]→[Shared RS]→event10
shared_stream: ················[event1+5]→[shared gate_up(控核32,1)]→[event6]→[SiTU]→event7 ··[event8]→[down_proj]→event9
```

## 探针与操作

探针（均为只读调研）：

1. recipes 的多流资源池（MoEContext，模型级一次性创建，T523 逐字）：

```
enable_multi_streams = custom_params.get("enable_multi_streams", False)
exe_mode = infer_config.model_config.exe_mode
# All MoE layers share this stream for multi-stream computation of shared experts.
self.shared_stream = create_stream('shared', exe_mode) if enable_multi_streams else None
# Split Decode uses the same communication stream with or without
# SuperKernel, keeping shared collectives outside the fusion scope.
self.shared_comm_stream = (create_stream('shared_comm', exe_mode) if enable_multi_streams else None)
self.router_stream = (create_stream('router', exe_mode) if enable_multi_streams else None)
# One shared pool sized for the largest consumer so every decode path
# reads the same tuple: split Decode uses slots 0-10, prefill uses slots 0-3.
event_count = 11
self.events = tuple(create_event(exe_mode, enable_multi_streams) for _ in range(event_count))
```

2. vllm-ascend 侧的调用顺序与消费点（routed_experts.py，T524 逐字）：

```
prepare_output = _EXTRA_CTX.moe_comm_method.prepare(           # L516 ① 通信预处理（pad/TP切分/DP all-gather router_logits）
    hidden_states=hidden_states, router_logits=router_logits, ...)
topk_weights, topk_ids = self._select_experts(                  # L530 ② ★ 路由/TopK
    hidden_states=hidden_states, router_logits=router_logits, ...)
fused_experts_results = self.quant_method.apply(                # L539 ③ dispatch + GMM + combine
    layer=self, x=hidden_states, topk_weights=topk_weights, topk_ids=topk_ids, ...)
routed_out = _EXTRA_CTX.moe_comm_method.finalize(...)           # L573 ④ finalize
```

3. 可复用基建盘点（T524）：`npu_stream_switch` + 懒单例流模式（utils.py）、`FusedMoEEvents` 6 槽事件协议、custom op 边界（`ascend_moe_forward_shared_sp`）、KDA 多流+图捕获三定律（kimi_kda.py L281-318：fork 前主流 record_event + 输入 tensor record_stream；辅助流内先 wait_event 再尾部 record_event；join 时主流 wait_event 精确尾部 event、输出 tensor record_stream(main)）、DSV4 `_select_topk_multistream`（indexer.py L573-599）GEMM 分流样板、shared 多流 e2e 先例（`test_multistream_overlap_shared_expert.py`）。

操作：无代码修改；产出分析文档 `KIMI3-MoE-TopK分流分析.md`（353 行、7 章，T528 写入成功、T537 行数校验 353/残留标记 0）。

## 机制与判别

1. 资源池形态：**cann-recipes-infer 的 K3 MoE 分流采用模型级 MoEContext 三流（shared_stream/shared_comm_stream/router_stream）+ 11 槽事件池，模型 init 一次性创建、92 层共享，capture/replay 期间对象引用稳定。**stream/event 不在 forward 内创建是 npugraph_ex 图捕获兼容的前提（"Graph mode requires such tensors to be created outside the captured region with a stable object id"）。
2. 编排精髓（Cube/Vector 资源对偶）：**router_stream 的编排为 [router GEMM(控核32,1)] → event3 → [npu_moe_gating_top_k] → event4，与主流 [mx_quant(Vector) → 等event3 → latent down(Cube) → 等event4 → dispatch] 并行；event3 显式串行化两个 Cube MatMul（router GEMM 与 latent down），避免 Cube/Cube 争抢。**事件槽位语义（T523 逐字）：

```
| 2 | 主流 | router_stream | hidden_states 就绪，router GEMM 可以开始 |
| 3 | router_stream | 主流 | **router GEMM 完成**（主流 latent down 投影等待，串行化两个 MatMul） |
| 4 | router_stream | 主流 | **gating TopK 完成**（topk_idx/weight 可消费） |
```

TopK(AIV) 与 latent down(Cube) 对偶并行、gate GEMM(Cube) 与 mx_quant(Vector) 对偶并行；同类资源（Cube/Cube）靠 event 串行 + 控核（`limit_core_num(32,1)`），异类资源控核后并行。prefill 不分流（`switch=False # OOM while 128K 32TP`），decode 分流（shape 稳定）。

3. vllm-ascend 侧的 join 点判别（本卡最关键的判别规则）：**vllm-ascend 侧 topk_ids/topk_weights 的全部消费点在 dispatch/combine，且 routed_experts.forward_impl 的顺序是 prepare → select_experts(TopK) → apply(dispatch/GMM/combine) → finalize，其中 prepare（MC2 的 pad/TP 切分、AllGather 模式的 DP all-gather router_logits）也消费 router_logits，故 join 必须放在 prepare 之前，只放在 TopK 之前会静默读错数据。**即 [gate GEMM+TopK] ∥ [量化+latent down] 是天然并行窗口，但 join 晚于 prepare 不会报错而是静默数据错乱；UT 可用 `switch_stream` 顺序断言锁定。
4. 推荐路径（两阶段）：阶段一在模型层 fork gate GEMM（kimi_k3.py gate 调用点），单例 gating 流 + KDA 三定律 fork/join，join 放 runner 的 prepare 前，侵入最小；阶段二把 K3 下沉 internal router 并在 runner 内做 [gate+TopK] 完整分流，完整复刻 recipes 编排，但需同步解决 internal 路径 `weight_fp32` 与 bf16 化的冲突。

## 验证信号

本轨迹内为只读分析，客观信号仅限工件级：

- T523/T524：两个研究子代理的调研报告（recipes 编排与 vllm-ascend 现状的事实链；T523/T524 中段截断部分已用 event reader 补读核验引用段）。
- T528：分析文档写入成功（`Wrote file successfully.`）。
- T537：文档完整性检查（353 行、无残留标记）。

未观测到的信号：任何运行时验证。**本卡为分析结论（输出 353 行分析文档），未做任何代码修改，亦无 NPU 运行验证；Cube/Cube 争抢是否负优化、ACLGraph 流资源（错误码 207008）等风险均为代码级推断，实施前需 profile 验证。**

## 适用与失效边界

- 适用：vllm-ascend K3（external router）或 internal-router 模型的 gating 分流设计；参照 recipes 编排时以 decode（shape 稳定）为首要目标。
- 失效/风险边界：
  1. Cube/Cube 争抢：gate GEMM 与 latent down/gate_up 均 Cube，盲目并行可能负优化；recipes 用 event 串行化 + 控核规避，实施时先整段 fork/join 验证正确性，profile 确认争抢后再插入中间事件与控核。
  2. ACLGraph 流资源：多流 × 层数 × 捕获档位放大流节点数，错误码 207008（acl_graph.py 已有"减 capture sizes / 改 FULL 模式"建议）；gating 流应为全局单例（1 条）。
  3. join 点错误是静默错乱不是报错（见机制 3）；MoECommType 逐 forward 动态切换（ALLGATHER/MC2/ALLTOALL 三者 topk 消费点不同），join 放 prepare 前对三者统一安全，e2e 需覆盖 MC2（decode）与 ALLTOALL/ALLGATHER（prefill 大 token）。
  4. shared 辅助流是全层单例，gating 需独立流（参照 KDA/DSA 各自模块单例），不能复用 shared 流。
  5. 多机 MC2：event join 只保证本 rank 就绪，跨 rank 由集合通信自身同步；需双卡 e2e。
  6. 引用的 recipes 行号来自子代理报告，未经主线会话直接重读源文件复核；采用前应以源文件为准。
