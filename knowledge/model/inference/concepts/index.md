# 概念

- [框架](frameworks/index.md)：共 20 张知识卡（如 AscendC、AutoFuse（Inductor NPU 自动融合编译组件）、CANN Executor：统一模型执行与调度 等）。
- [融合 Kernel](kernels/index.md)：共 13 张知识卡（如 Compressor (C4A / C128A KV 压缩融合算子)、Deepseek Indexer Attention Kernel、FIA v1/v2：参数名、TND/Paged NZ 布局与分路径 mask 等）。
- [模型](models/index.md)：共 21 张知识卡（如 DeepSeek-R1、DeepSeek-V3.2-Exp、DeepSeek-V4 等）。
- [网络模块](modules/index.md)：共 10 张知识卡（如 Blockwise Sparse Attention (TopK / SVG)、Diffusion Transformer (DiT)、DSA（DeepSeek Sparse Attention）架构模式 等）。
- [并行策略](parallelism/index.md)：共 12 张知识卡（如 CFG Parallel、上下文并行（Context Parallel / CP）：长上下文 Prefill 的序列切分、Data Parallel 等）。
- [平台](platforms/index.md)：共 2 张知识卡（如 Ascend 950 (950PR / 950DT)、Atlas A3）。
- [量化](quantization/index.md)：共 6 张知识卡（如 MXFP8 量化注意力（HunyuanVideo）、DeepSeek-V4 950 混合量化：HiF8、MXFP8 与 MXFP4、Int8 / Hybrid INT8-INT4 (DeepSeek-V4 Atlas A3 Pod) 等）。
- [优化技术](techniques/index.md)：共 21 张知识卡（如 Attention-FFN Disaggregation (AFD)、AICPU Scheduler（值依赖分核下沉 ARM 核）、CANN SHMEM 通信编程模型 等）。

- [SGLang 昇腾量化与通信概念](sglang_ascend/index.md)：共 5 张知识卡（如 SGLang Ascend runner 的多通信模式与全容量汇合、SGLang 昇腾路由的 count、逆映射与 scale 复用、SGLang 昇腾 TopK 的物理专家映射与 padding 统计 等）。

- [SGLang 推理组件验证概念](sgl_kernel_npu/index.md)：说明 check_accuracy/check_performance/make_executor 的独立基线、原地输入隔离、开关优先级、NPU task计时与产物边界。
