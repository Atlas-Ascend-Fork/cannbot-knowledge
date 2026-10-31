# 模型优化指南

分阶段实施优化并验证精度、性能与回退。

- [LLM Decode 图编译指南（当前 GE 与 npugraph_ex）](graph_mode_decode_only_compile_backends.md)：当前 Decode-only 路由、主/draft独立接口、两种编译后端、宽度命名空间、队列修复与预热验收。
- [R1 Prefill 微批双流：按请求切分并对齐通信轮次](prefill_micro_batch_dual_stream_moe_overlap.md)：更新当前R1按请求边界切packed微批、两种双流流水及EP一致chunk轮次，明确开关和验收。
- [单卡推理优化指南：分阶段验证 KV、融合算子与 Decode 图模式](staged_single_card_optimize_pipeline.md)：记录来源 model-optimize Skill 的三阶段参考流程：KVCache 与 FA、其他融合算子、Decode 图适配；每阶段对照基线验证，具体阶段是否需要取决于现有实现和瓶颈。
- [多流优化流程：拆解依赖、选择后端并验收真实收益](multi_stream_optimization_workflow.md)：当前多流依赖拆解、后端API分发、LongCat GE/npugraph编排与真实性能验收，替换旧GE-only片段。
