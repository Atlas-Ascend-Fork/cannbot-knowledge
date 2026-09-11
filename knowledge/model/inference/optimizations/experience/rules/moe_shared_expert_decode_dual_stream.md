---
type: Optimization
title: 带共享专家的 MoE decode 双流重叠：共享专家副流掩盖路由专家 dispatch/GMM/combine
description: 带共享专家的 MoE decode 双流重叠：共享专家副流掩盖路由专家 dispatch/GMM/combine。MoE 结构 = 路由专家 + 共享专家，做 decode 低时延优化时。共享专家通常和路由专家一起参与最终输出（hidden = shared + router），但两者在数据流上不严格串行依赖。单流顺序执行会把共享专家耗时完整暴露在关键路径上，压低吞吐与 TPOT。decode shape 稳定，最适合让多流收益稳定落地。
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
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 带共享专家的 MoE decode 双流重叠：共享专家副流掩盖路由专家 dispatch/GMM/combine

## 适用场景

MoE 结构 = 路由专家 + 共享专家，做 decode 低时延优化时。共享专家通常和路由专家一起参与最终输出（`hidden = shared + router`），但两者在数据流上不严格串行依赖。单流顺序执行会把共享专家耗时完整暴露在关键路径上，压低吞吐与 TPOT。decode shape 稳定，最适合让多流收益稳定落地。

## 核心手段

主流跑路由专家主路径（gate/topk → dispatch → GMM → combine），副流跑共享专家前向，汇合点再同步、相加。仅在 decode（`not is_prefill`）启用。

判据（维护者定性）：**让路由专家流当关键路径、共享专家流藏在其影后时性能最好**。据此共享专家的**启动要下沉到拿到路由结果 `topk_idx` 之后**，保证路由/dispatch 先行，而不是与路由并行起跑抢关键路径。进一步可把共享专家拆成 `up/gate 投影 → swiglu → down_proj` 三段，分别钉在路由侧三个里程碑之后（投影等 `topk_idx`、swiglu 等 dispatch 产物、down_proj 等路由专家 GMM 输出），逐段藏在对应路由算子影后。

## 关键洞见：想重叠就得放弃 combine 的 shared_expert_x 融合入参

`npu_moe_distribute_combine_v2` 有个 `shared_expert_x` 入参，会把「共享专家结果相加」融进 combine 算子内部。用它虽省一次加法，但等于**把共享专家钉死在 combine 之前的关键路径上**，无法与路由专家并行。想让共享专家与路由 dispatch/GMM 重叠，就必须：

1. 从 combine kwargs 里**删掉 `shared_expert_x`**；
2. 改为 combine 算子之后手动 `hidden = hidden + hidden_states_share`；
3. 用 `torch.npu.Event` 补齐顺序依赖——共享专家 `down_proj` 前 `wait_event`（等路由 GMM 完成标记）、主流最终相加前 `wait_event`（等共享专家算完标记），否则会读到未算完的中间结果。

这条 trade-off 对任何「路由专家 + 共享专家」结构在昇腾 decode 多流重叠上都成立。**反向的取舍**：若本来就不做多流重叠，则共享输出可作 `skip1` 残差项传给 `npu_moe_finalize_routing`（`skip1=shared_state`），让加法融进 finalize-routing 算子、省掉一次独立 elementwise add——即「融进 combine/finalize 省 add」与「解耦出来换重叠」是同一设计点的两端，按是否要重叠取舍。

## 落法变体（同一手段的几种参考写法）

- **TorchAir / GE 图模式（`npu_stream_switch` + tagged event）**：共享专家进 `"11"` 号 tagged stream，`enable_multi_streams = enable_multi_streams and not is_prefill`；叠加 ACL graph event 时切流前后 `tng.ops.npu_record_tagged_stream` / `npu_tagged_event_record` / `npu_tagged_event_wait`；GE 图跨流排序用控制边 `npu_wait_tensor(out, dep)`（给 `out` 挂一条到 `dep` 就绪的边）。图模式常给 superkernel 打开多流融合 `option="stream-fusion=1"`。
- **eager / patch（显式 `torch.npu.Stream` + `wait_stream`）**：旁路 stream 用全局单例惰性创建、跨 step 复用；`shared_stream.wait_stream(current_stream)` → `with torch.npu.stream(shared_stream): 共享专家` → `current_stream.wait_stream(shared_stream)` 收口。
- 共享流也可做成模块初始化能力（建层时注入 `share_mlp_stream`），不在前向里临时切上下文。
- 同一取向的姊妹掩盖：**用异步 all_reduce 掩盖路由专家 TP 通信**——都要求 MoE 带一条可与路由专家重叠的旁支。Gate/Dispatch（权重小 + 通信型、HBM 带宽占用低）也可与带宽瓶颈的共享专家并发。

## 何时不适用 / 风险 / rollback

- prefill 阶段不启用（`not is_prefill`）；shape 太小、host bound 太重时收益不明显；共享专家很小、掩盖窗口不足则无净收益；共享专家已吃满资源时多流不一定正收益；eager patch 里 `hidden.clone()` 有额外显存开销。
- 流间同步没处理好会在 `shared + router` 汇合处出精度/同步错误——图模式要 stream tag + event + superkernel scope 一起设计，不能只切流不同步；重排 combine 重叠时须同步改「删 `shared_expert_x` + 手动相加」这条数据流，否则共享分支被漏加或与 combine 形成假依赖破坏重叠。
- rollback：保留 `enable_multi_streams` 开关与原始单流路径；关闭时 `record_stream/record_event/wait_event/npu_stream_switch` 均降级为 no-op。
- **多流之后往往还要分核**（给两条流按 `limit_core_num` 配不同 Cube/Vector 核数）才稳定获益，见 [moe-multi-stream-limit-core-num](../cases/moe_multi_stream_limit_core_num.md)；判断两算子能否并流看 vector 核是否占满，见 [gmm-swigluquant-vector-core-parallel](gmm_swigluquant_vector_core_parallel.md)。

## 收益

各参考实现均无 before→after 时延数字（无 benchmark 表），定性目标为把共享专家耗时移出关键路径、降低 decode TPOT。参考实现涵盖 DeepSeek-V3.2-Exp / DeepSeek-R1 / DeepSeek-V4 / Kimi-K2-Thinking / GLM-5（torchair 图模式）、Qwen3-Next（SGLang/DeepEP eager patch）、HunyuanImage-3.0（初始化注入共享流）；作为「MoE+共享专家 decode 多流重叠」可迁移模式陈述，不升为整栈通用律、不外推固定加速比。

## 相关经验

- 另见 [NPU fused_topk 默认先归一化再按 routed_scaling_factor 缩放：保留 norm_topk_prob=True 会二次归一化破坏路由缩放语义](../../../runbooks/precision/moe_router_norm_topk_prob_fused_topk_npu.md)。
- 另见 [GE 图模式 decode superkernel 按功能段分别包 scope（attention 段、MoE 段各一）+ 可门控空上下文零开销](superkernel_scope_segmented_gated.md)。


## Evidence

- torchair `npu_stream_switch(enable_multi_streams,"11")` 包裹共享专家 + IndexerProlog 多流：diff 事实 @fa6892b。溯源下探 [cann-recipes-infer-pr-3-feat-add-deepseek-v3-2-exp-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/3)。
- decode 共享专家副流 overlap 干预配方（tagged event / eager Stream 两风格 + 同步协议 + superkernel stream-fusion）：diff 事实 @d739fecb4232（skill 示例具名披露，未逐字核各模型源建模文件）。溯源下探 [cann-recipes-infer-pr-351-feat-update-agent-skills-with-full-optimization-pipeline-and-role-based](https://gitcode.com/cann/cann-recipes-infer/merge_requests/351)。
- 「路由流掩盖共享流」判据 + 三段控制边（`topk_idx`/dispatch 产物/路由 GMM 输出）+ combine `shared_expert_x` 改显式相加（W8A8/非量化双分支）：diff 事实 @2c7e797f60e3 + 维护者确认。溯源下探 [cann-recipes-infer-pr-121-feat-ge-graph-multistreams](https://gitcode.com/cann/cann-recipes-infer/merge_requests/121)。
- decode 共享专家切独立 stream 与 dispatch/GMM/combine 重叠、从 combine `shared_expert_x` 解耦 + `torch.npu.Event` 串联两处顺序依赖：diff 事实 @22f2f847833a；性能收益为机制推断（源无 benchmark），prefill 多流推迟。溯源下探 [cann-recipes-infer-pr-487-enable-qmm2-and-combine-parallel](https://gitcode.com/cann/cann-recipes-infer/merge_requests/487)。
- eager 双流同步骨架（旁路 stream 单例 + `wait_stream` + `with torch.npu.stream(...)`）掩盖 deepep 路由专家开销：diff 事实 @874b41df5de8；收益未量化。溯源下探 [cann-recipes-infer-pr-235-feat-support-qwen-next](https://gitcode.com/cann/cann-recipes-infer/merge_requests/235)。
- 共享输出作 `skip1` 融进 `npu_moe_finalize_routing`、NPU 分支去掉 Python 层单独加法（不重叠时省一次 add）：diff 事实 @8cd85a87af03 + 维护者确认。溯源下探 [cann-recipes-infer-pr-284-feat-llada2-x-sglang-ascend](https://gitcode.com/cann/cann-recipes-infer/merge_requests/284)。