# 模型优化指南

分阶段实施优化并验证精度、性能与回退。

- [LLM Decode 图编译指南：来源实现的 GE 与 ACLGraph 入口及验收](graph_mode_decode_only_compile_backends.md)：按来源实现组织 Decode 图编译、预热和回退，列出 GE、ACLGraph/npugraph_ex 的配置差异；入图取舍引用图模式决策，不将 Prefill eager 或历史后端限制泛化为 NPU 平台禁令。
- [Prefill 用 micro-batch 双流把 MoE dispatch/combine 通信藏进计算](prefill_micro_batch_dual_stream_moe_overlap.md)：Prefill 用 micro-batch 双流把 MoE dispatch/combine 通信藏进计算。大 EP MoE 模型 prefill：整体是计算 bound，但 MoE 的 dispatch/combine 两段 AllToAll 通信仍占一定比例（本仓一手优化文档称 prefill 通信耗时占比可达约 30%）。计算与通信由不同硬件单元完成、可并行——把它们错开就能用计算掩盖通信、把 prefill 推向纯计算 bound。 拓扑：MLA 走 DP 切分、MoE 走 EP 切分（DP+EP），或更一般的「EP + 可切 micro-batch」场景。 目标：用一路的计算穿插另一 micro-batch 的通信，隐藏 MoE EP 的通信空洞。
- [单卡推理优化指南：分阶段验证 KV、融合算子与 Decode 图模式](staged_single_card_optimize_pipeline.md)：记录来源 model-optimize Skill 的三阶段参考流程：KVCache 与 FA、其他融合算子、Decode 图适配；每阶段对照基线验证，具体阶段是否需要取决于现有实现和瓶颈。
- [多流优化流程：拆解依赖、选择后端并验收真实收益](multi_stream_optimization_workflow.md)：从基线和依赖图开始，按实际后端实现跨流同步，逐步验证精度、重叠和端到端收益；实现参数由关联规则维护。
