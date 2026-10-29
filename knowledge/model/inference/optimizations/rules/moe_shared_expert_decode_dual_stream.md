---
type: Optimization
title: 带共享专家的 MoE decode 双流重叠：共享专家副流掩盖路由专家 dispatch/GMM/combine
description: 带共享专家的 MoE decode 双流重叠：共享专家副流掩盖路由专家 dispatch/GMM/combine。MoE 结构 = 路由专家 + 共享专家，做 decode 低时延优化时。共享专家通常和路由专家一起参与最终输出（hidden = shared + router），但两者在数据流上不严格串行依赖。单流顺序执行会把共享专家耗时完整暴露在关键路径上，降低吞吐、增加 TPOT。decode shape 稳定，最适合让多流收益稳定落地。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.graph_execution
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/3
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/351
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/121
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/487
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/235
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/284
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:41:05Z'
platforms:
- agnostic
---

# 带共享专家的 MoE decode 双流重叠：共享专家副流掩盖路由专家 dispatch/GMM/combine

## 适用场景

MoE 结构 = 路由专家 + 共享专家，做 decode 低时延优化时。共享专家通常和路由专家一起参与最终输出（`hidden = shared + router`），但两者在数据流上不严格串行依赖。单流顺序执行会把共享专家耗时完整暴露在关键路径上，降低吞吐、增加 TPOT。decode shape 稳定，最适合让多流收益稳定落地。

## 核心手段

主流跑路由专家主路径（gate/topk → dispatch → GMM → combine），副流跑共享专家前向，汇合点再同步、相加。LLM 的相应实现仅在 decode（`not is_prefill`）启用；HunyuanImage 多模态变体另按 (c) 的后端与混合 MLP 门控解释，没有 is_prefill 守卫。

判据（维护者定性）：**让路由专家流当关键路径、共享专家流藏在其影后时性能最好**。PR121 的特定调度方案将共享专家**启动下沉到拿到路由结果 `topk_idx` 之后**，保证路由/dispatch 先行，而不是与路由并行起跑抢关键路径。进一步可把共享专家拆成 `up/gate 投影 → swiglu → down_proj` 三段，分别钉在路由侧三个里程碑之后（投影等 `topk_idx`、swiglu 等 dispatch 产物、down_proj 等路由专家 GMM 输出），这是资源调度方案，不能作为所有共享分支的必要数据依赖。

## combine 融合与并行窗口分别取舍

`shared_expert_x` 将共享输出相加融入 combine，要求共享输出在 **combine 消费之前**就绪，但不禁止此前共享分支与路由 dispatch/GMM 并行。固定 V3.2-Exp 的共享专家副流就保留该融合入参；TP 路径也可保留 finalize 的 skip1。

若目标是让 **combine 自身**也与共享计算重叠，可按 PR487 等特定方案删掉 `shared_expert_x`，在 combine 后显式相加。此时必须在最终消费共享输出前同步，并保证只加一次。共享 `down_proj` 等待路由 GMM 是该方案的资源调度顺序，不是它读取路由 GMM 数据的依赖；共享 down_proj 实际消费共享激活。是否解耦需比较该实现的融合收益、同步开销与可用重叠窗口，不能写成 dispatch/GMM 并行的必要条件。

## 落法变体（同一手段的几种参考写法）

- **TorchAir / GE 图模式（`npu_stream_switch` + tagged event）**：共享专家进 `"11"` 号 tagged stream，`enable_multi_streams = enable_multi_streams and not is_prefill`；叠加 ACL graph event 时切流前后 `tng.ops.npu_record_tagged_stream` / `npu_tagged_event_record` / `npu_tagged_event_wait`；GE 图跨流排序用控制边 `npu_wait_tensor(out, dep)`（给 `out` 挂一条到 `dep` 就绪的边）。图模式常给 superkernel 打开多流融合 `option="stream-fusion=1"`。
- **eager / patch（显式 `torch.npu.Stream` + `wait_stream`）**：旁路 stream 用全局单例惰性创建、跨 step 复用；`shared_stream.wait_stream(current_stream)` → `with torch.npu.stream(shared_stream): 共享专家` → `current_stream.wait_stream(shared_stream)` 收口。
- 共享流也可做成模块初始化能力（建层时注入 `share_mlp_stream`），不在前向里临时切上下文。
- 同一取向的姊妹掩盖：**用异步 all_reduce 掩盖路由专家 TP 通信**——都要求 MoE 带一条可与路由专家重叠的旁支。Gate/Dispatch（权重小 + 通信型、HBM 带宽占用低）也可与带宽瓶颈的共享专家并发。

## 何时不适用 / 风险 / rollback

- 相应 LLM 样例的 prefill 阶段不启用（`not is_prefill`），多模态 (c) 不套用该阶段门控；shape 太小、host bound 太重时收益不明显；共享专家很小、掩盖窗口不足则无净收益；共享专家已吃满资源时多流不一定正收益；eager patch 里 `hidden.clone()` 有额外显存开销。
- 流间同步没处理好会在 `shared + router` 汇合处出精度/同步错误——图模式要 stream tag + event + superkernel scope 一起设计，不能只切流不同步；若选择解耦 combine，须同步修改融合入参与显式相加的数据流，避免漏加或重复加；保留融合时则在 combine 消费前保证共享输出就绪。
- rollback：保留 `enable_multi_streams` 开关与原始单流路径；关闭时 `record_stream/record_event/wait_event/npu_stream_switch` 均降级为 no-op。
- **多流之后往往还要分核**（给两条流按 `limit_core_num` 配不同 Cube/Vector 核数）才稳定获益，见 [moe-multi-stream-limit-core-num](decode_multi_stream_overlap_core_balance.md)；判断两算子能否并流看 vector 核是否占满，见 [gmm-swigluquant-vector-core-parallel](gmm_swigluquant_vector_core_parallel.md)。

## 收益

各参考实现均无 before→after 时延数字（无 benchmark 表），定性目标为把共享专家耗时移出关键路径、降低 decode TPOT。参考实现涵盖 DeepSeek-V3.2-Exp / DeepSeek-R1 / DeepSeek-V4 / Kimi-K2-Thinking / GLM-5（torchair 图模式）、Qwen3-Next（SGLang/DeepEP eager patch）、HunyuanImage-3.0（初始化注入共享流）；作为「MoE+共享专家 decode 多流重叠」可迁移模式陈述，不升为整栈通用律、不外推固定加速比。

## 相关经验

- 另见 [NPU fused_topk 默认先归一化再按 routed_scaling_factor 缩放：保留 norm_topk_prob=True 会二次归一化破坏路由缩放语义](../../runbooks/precision/moe_router_norm_topk_prob_fused_topk_npu.md)。
- 另见 [SuperKernel 决策：融合范围、关闭门控与验证边界](superkernel_decode_ge_graph_fusion_scope.md)。


## Evidence

- torchair `npu_stream_switch(enable_multi_streams,"11")` 包裹共享专家 + IndexerProlog 多流：diff 事实 @fa6892b。溯源下探 [cann-recipes-infer-pr-3-feat-add-deepseek-v3-2-exp-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/3)。
- decode 共享专家副流 overlap 干预配方（tagged event / eager Stream 两风格 + 同步协议 + superkernel stream-fusion）：diff 事实 @d739fecb4232（skill 示例具名披露，未逐字核各模型源建模文件）。溯源下探 [cann-recipes-infer-pr-351-feat-update-agent-skills-with-full-optimization-pipeline-and-role-based](https://gitcode.com/cann/cann-recipes-infer/merge_requests/351)。
- 「路由流掩盖共享流」判据 + 三段控制边（`topk_idx`/dispatch 产物/路由 GMM 输出）+ combine `shared_expert_x` 改显式相加（W8A8/非量化双分支）：diff 事实 @2c7e797f60e3 + 维护者确认。溯源下探 [cann-recipes-infer-pr-121-feat-ge-graph-multistreams](https://gitcode.com/cann/cann-recipes-infer/merge_requests/121)。
- decode 共享专家切独立 stream 与 dispatch/GMM/combine 重叠、从 combine `shared_expert_x` 解耦 + `torch.npu.Event` 串联两处顺序依赖：diff 事实 @22f2f847833a；性能收益为机制推断（源无 benchmark），prefill 多流推迟。溯源下探 [cann-recipes-infer-pr-487-enable-qmm2-and-combine-parallel](https://gitcode.com/cann/cann-recipes-infer/merge_requests/487)。
- eager 双流同步骨架（旁路 stream 单例 + `wait_stream` + `with torch.npu.stream(...)`）掩盖 deepep 路由专家开销：diff 事实 @874b41df5de8；收益未量化。溯源下探 [cann-recipes-infer-pr-235-feat-support-qwen-next](https://gitcode.com/cann/cann-recipes-infer/merge_requests/235)。
- 共享输出作 `skip1` 融进 `npu_moe_finalize_routing`、NPU 分支去掉 Python 层单独加法（不重叠时省一次 add）：diff 事实 @8cd85a87af03 + 维护者确认。溯源下探 [cann-recipes-infer-pr-284-feat-llada2-x-sglang-ascend](https://gitcode.com/cann/cann-recipes-infer/merge_requests/284)。

## 固定版本的模型接入差异

以下代码形态来自旧 Concept 保留的固定提交 `2c45117d781ab9ab88dcb89a28ae30f5d2450399`，不将各模型的流标签、开关和后端前提相互套用。

cann-recipes-infer 里 MoE 多流落地分三种实现形态，思想一致（把 shared/MLP 分支从主路径剥离与路由专家的通信/计算重叠），但**切流 API、同步原语、注入时机**各不相同：

### (a) 共享专家双流 `npu_stream_switch "11"`（V3.2-Exp / GLM-5 / Kimi-K2）

**动机**：MoE decode 路径里，shared expert 与 routed expert 最终相加（`final = routed + shared`），但二者无严格串行依赖；单流执行会把 shared expert 整段耗时压在关键路径上。把 shared expert 切到副流 `"11"`，与主流的 `topk → dispatch → GroupedMatMul → combine` 重叠，隐藏 shared 分支耗时。**仅 decode**（`is_prefill=False`）。

**编排**（DeepSeek-V3.2-Exp `DeepseekV3MoE.forward`，[`models/deepseek-v3.2-exp/models/modeling_deepseek.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v3.2-exp/models/modeling_deepseek.py) L418–L430；GLM-5 [`models/glm-5/models/modeling_glm.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/models/modeling_glm.py) L406–L418 为逐行同构实现）：

```python
# modeling_deepseek.py L418–L430（@2c45117，与 glm-5 L406–L418 同构）
if self.n_shared_experts > 0:
    enable_multi_streams = self.enable_multi_streams and not is_prefill
    use_aclgraph_event = enable_multi_streams and self.enable_aclgraph
    if use_aclgraph_event:
        tng.ops.npu_record_tagged_stream(hidden_states, "11")
        tng.ops.npu_tagged_event_record(moe_npu_events[0])
    with npu_stream_switch(enable_multi_streams, "11"):
        if use_aclgraph_event:
            tng.ops.npu_tagged_event_wait(moe_npu_events[0])
        # shared_expert use multi streams
        hidden_states_share = self.shared_experts(hidden_states.view(-1, hidden_states.shape[-1]))
        if use_aclgraph_event:
            tng.ops.npu_tagged_event_record(moe_npu_events[1])
```

关键事实（@2c45117）：

- 副流标号是 `"11"`（regular `npu_stream_switch`）。**R1 不属本组**——R1 @2c45117 用 `npu_stream_switch_gegraph(True, "22")`（ge_graph 路径、无 tagged_event，见上文旧叙述段），与本组 acl_graph `"11"` + tagged_event 链是不同实现。
- `enable_aclgraph = (exe_mode == "acl_graph")`（L218），故 `tagged_event`/`tagged_stream` 这条同步链只在 **acl_graph 模式**下叠加；`moe_npu_events = [tng.ops.npu_create_tagged_event(tag=f"moe_evt_{i}") for i in range(2)]` 在模块级创建（v3.2 L69 / glm-5 L57）。下游 `npu_tagged_event_wait(moe_npu_events[1])` 在 dispatch/combine 汇合处等待 shared 分支完成（v3.2 L549/L654、glm-5 L537/L642）。
- superkernel 协同：图模式下整段 decoder 包在 `superkernel_scope(self.enable_superkernel and not is_prefill, label, option)` 内，多流开时 `option = "stream-fusion=1"`，否则 `"option_xxx2"`（v3.2 L1659–L1664、glm-5 L1663–L1668）。详见 [superkernel](../../concepts/techniques/superkernel.md)。
- Kimi-K2-Thinking 复用同一 `npu_stream_switch(enable_multi_streams, "11")` 写法（`models/kimi-k2-thinking/models/modeling_deepseek.py` L414）。代表实现 [deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md)；相似实现 GLM-5 / Kimi-K2-Thinking（R1 走 ge_graph `"22"` 另一路，见旧叙述段）。

### (b) Qwen3-Next SGLang patch 形态（全局 stream + 环境变量）

**动机**：优化不落在模型仓本体，而是通过 patch 嵌入 SGLang runtime + DeepEP dispatch/combine 流程。

**编排**（[`models/qwen3-next/patches/stage1/0003-feat-moe-multi-stream.patch`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3-next/patches/stage1/0003-feat-moe-multi-stream.patch)，改 `moe/utils.py` + `models/qwen2_moe.py` + `quantization/w8a8_int8.py`）：

- `moe/utils.py` 新增全局单例 `shared_expert_stream = None` + `get_npu_shared_expert_stream()`（懒创建 `torch.npu.Stream()`）。
- `Qwen2MoeSparseMoeBlock` 构造期读 `self.enable_npu_deepep_moe_multi_stream = get_bool_env_var("ENABLE_NPU_DEEPEP_MOE_MULTI_STREAM", "false")`；`_forward_deepep` 中当 `_is_npu and self.shared_expert is not None and self.enable_npu_deepep_moe_multi_stream` 时走 `npu_forward_normal_dual_stream`。
- `npu_forward_normal_dual_stream` 用 **`shared_expert_stream.wait_stream(current_stream)` + `with torch.npu.stream(shared_expert_stream)`** 三段切流（与 DeepEP dispatch/combine overlap），末尾 `current_stream.wait_stream(shared_expert_stream)` 汇合：

```python
# qwen2_moe.py（patch 注入，@2c45117）
current_stream = torch.npu.current_stream()
router_logits, _ = self.gate(hidden_states)
shared_expert_stream.wait_stream(current_stream)
with torch.npu.stream(shared_expert_stream):           # 段1：shared gate + gate_up
    hidden_states_copy = hidden_states.clone()
    shared_output = self.shared_expert_gate(hidden_states_copy)
    gate_up, _ = self.shared_expert.gate_up_proj(hidden_states_copy)
topk_output = self.topk(hidden_states, router_logits, ...)
dispatch_output = self.experts.dispatcher.dispatch(hidden_states=hidden_states, topk_output=topk_output)
shared_expert_stream.wait_stream(current_stream)
with torch.npu.stream(shared_expert_stream):           # 段2：sigmoid + act_fn
    shared_output = F.sigmoid(shared_output)
    gate_up = self.shared_expert.act_fn(gate_up)
combine_input = self.experts.run_moe_core(dispatch_output)
shared_expert_stream.wait_stream(current_stream)
with torch.npu.stream(shared_expert_stream):           # 段3：down_proj + 门控相乘
    shared_expert_output, _ = self.shared_expert.down_proj(gate_up)
    shared_output = shared_output * shared_expert_output
router_output = self.experts.dispatcher.combine(combine_input=combine_input)
current_stream.wait_stream(shared_expert_stream)
```

> **版本差异**：`2f82d10` 的 shared stream 实现分为两段；`2c45117` 则是**三段** `with torch.npu.stream(...)`，每段前都 `wait_stream(current_stream)`，`down_proj` 单独成段（不与 sigmoid/act_fn 合并）。

配套：`w8a8_int8.py` 把 NPU 上 `layer.w2_weight_scale` 转 `torch.bfloat16`（避免 GroupedMatMul scale 类型冲突）。详见 [qwen3-next](../../concepts/models/qwen3_next.md)。

### (c) HunyuanImage-3.0 多模态变体（init 注入 `share_mlp_stream` + Event 同步）

**动机**：多模态网络里 shared MLP 与路由路径串行会暴露在整网关键路径上；且实现风格偏「初始化阶段就把共享流作为模块能力注入」，而非前向里临时切 scope。

**编排**（[`models/hunyuan-image-3.0/adaptor_patches/hunyuan.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py)）：

- 模型 init 期 `kwargs["share_mlp_stream"] = torch.npu.Stream(device=torch.device(f"npu:{local_rank}"))`，再把整个 `kwargs` 传给每一层（L729）；MoE 模块构造期 `self.share_mlp_stream = kwargs.get("share_mlp_stream", torch.npu.Stream(...))`（L205）。
- 前向里 shared MLP 跑在 `with torch.npu.stream(self.share_mlp_stream):`（EP 路径 L295、非 EP 路径 L332），**同步用 `torch.npu.Event()` 而非 `npu_stream_switch`**：`input_ready_event.record(current_stream)` → 副流内 `input_ready_event.wait()`；汇合处 `mlp_done_event.record(self.share_mlp_stream)` → `mlp_done_event.wait(torch.npu.current_stream())`（L375），最后 `output = hidden_states_mlp + combined_output`。
- 共享副流要求 `_moe_impl == "npu_grouped_matmul"` 且 `self.config.use_mixed_mlp_moe`；其他后端在主流执行 shared_mlp。EP 路径先启动共享分支再执行路由；非 EP 路径在 finalize_routing 后才启动共享分支，用于重叠后续通信，两者窗口不同。这里没有 is_prefill 守卫。

```python
# hunyuan.py L292–L297（@2c45117）
input_ready_event = torch.npu.Event()
input_ready_event.record(torch.npu.current_stream())
with torch.npu.stream(self.share_mlp_stream):
    input_ready_event.wait()
    hidden_states_mlp = self.shared_mlp(shared_mlp_input)
```

详见 [hunyuan-image-3](../../concepts/models/hunyuan_image_3.md)。

### 三种形态对比 / 适用与风险

| 形态 | 切流原语 | 同步原语 | 注入时机 | 门控 |
|---|---|---|---|---|
| (a) V3.2-Exp/GLM-5/Kimi-K2 | `npu_stream_switch("11")` | tagged_event（acl_graph）+ superkernel `stream-fusion=1` | 前向临时切 scope | `enable_multi_streams` + decode |
| (b) Qwen3-Next patch | `torch.npu.stream(shared_expert_stream)` | `wait_stream`（×4） | 框架 patch + 全局单例 | `ENABLE_NPU_DEEPEP_MOE_MULTI_STREAM` env |
| (c) HunyuanImage-3.0 | `torch.npu.stream(share_mlp_stream)` | `torch.npu.Event` record/wait | init 期注入各层 | `config.use_mixed_mlp_moe` |

- **适用**：MoE / shared-expert（或 shared-MLP）结构，shared 分支计算量足以掩盖主流通信（dispatch/combine AllToAll）或专家计算；(a) 主走 decode + 图模式，(b) 走 SGLang+DeepEP，(c) 走多模态整网。
- **风险**：流间同步缺失 → `shared + routed` 精度/顺序错误；shape 太小或 host-bound 重时收益不明显；(b) 的 `hidden_states.clone()` 带额外显存开销且对上游 SGLang 版本敏感；(c) init 期注入 stream，不能简单拷一段前向，且多模态里若同时有 CFG/VAE 并行需防资源竞争。控核（`limit_core_num`）等更一般的双流并行约束与方法论见 [multi-stream](../../concepts/techniques/multi_stream.md)。

## 旧版适配差异与收益口径

- Qwen3-Next 的 SGLang stage1 patch（`2f82d10467e6fe8dae81c97a2cdac78d733a6703`）通过 `ENABLE_NPU_DEEPEP_MOE_MULTI_STREAM` 进入双流路径，配 DeepEP，需存在 shared expert；该 patch 包含输入 clone、共享门控及 INT8 scale 的 BF16 转换，复用时要计入开销和 dtype 约束。
- 同提交的 R1 GE 实现使用 stream tag `22`，后续 V3.2-Exp 等实现使用其他标签；标签不是算法必要条件，不能据此跨版本拼代码。
- Qwen3-Next 的 20.6 ms 和 LongCat 的 9.95 ms 属整套配置观测，没有多流独立对照；具体配置见对应模型卡，不用它们估算本规则单项加速比。
