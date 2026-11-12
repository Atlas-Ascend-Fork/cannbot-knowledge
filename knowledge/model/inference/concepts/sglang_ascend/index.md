# SGLang 昇腾量化与通信概念

本目录收录固定版本来源支持的知识；具体平台、配置和验证边界见各卡正文。

- [SGLang Ascend runner 的多通信模式与全容量汇合](sglang_ascend_moe_ascend_runner_routes.md)：连接 Standard、AllToAllV、AllGather、MC2 与 DeepEP hooks，说明全局 expert 范围和 FP32 汇合边界。
- [SGLang 昇腾路由的 count、逆映射与 scale 复用](sglang_ascend_moe_routing_scale_contract.md)：明确 RoutingV2 的量化枚举和 expert 顺序，并区分计数、累积边界以及 weighted/unweighted finalize。
- [SGLang 昇腾 TopK 的物理专家映射与 padding 统计](sglang_ascend_moe_topk_placement_padding.md)：说明 NPU router 分支、biased selection/unbiased weight、共享槽保留及 padding 对通信容量和 EPLB 的影响。
- [SGLang 昇腾量化配置与后端选择边界](sglang_ascend_quant_backend_selection.md)：区分量化注册名、权重格式、Dense 与 MoE 分派，避免把 GPU 配置名等同于 NPU 内核支持。
- [SGLang 昇腾 MX dtype 与 E8M0 scale 字节解释](sglang_ascend_quant_mx_dtype_scale_bytes.md)：说明 torch 与 torch_npu dtype 参数差别、两类 FP32 scale 容器和 E4M3 手动解码的加载边界。
