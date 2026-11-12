# SGLang 昇腾模型部署与调优配方

本目录收录固定版本来源支持的知识；具体平台、配置和验证边界见各卡正文。

- [SGLang Ascend DeepSeek-R1：A3量化、PD拓扑与NEXTN配置](sglang_ascend_doc_deepseek_r1.md)：融合v0.5.18教程、W4A8/W8A8性能配方与旧DeepSeek例子，区分物理卡/TP设备、图档位和阶段通信，记录可复核性能条件。
- [SGLang Ascend DeepSeek-V3.2：DSA长上下文与CP/PD配方](sglang_ascend_doc_deepseek_v3_2.md)：限定v0.5.18+A3的W8A8、ZigZag CP32 Prefill和低时延Decode，按128K输入的真实并发保留上游TPOT观测与版本限制。
- [SGLang Ascend DeepSeek-V4-Flash：dsv4后端、分页与分角色投机](sglang_ascend_doc_deepseek_v4_flash.md)：限定A3教程/最佳实践与950待验证Flash Official cell的dsv4、page128、精度及分角色投机差异，不从variant列表推导Pro支持。
- [SGLang 在 A3 部署 GLM-5.1 的长上下文与前缀复用配方](sglang_ascend_doc_glm_5_1.md)：比较 GLM-5.1 W4A8 混部及 PD 分离中的 CP、DeepEP、推测解码和上游负载指标。
- [SGLang 在 A3 部署 GLM-5.2 的精度与 3P1D 配方](sglang_ascend_doc_glm_5_2.md)：区分A3 W8A8容量、W4A8 3P1D性能案例与950待验证生成器分支，保留MTP权重和镜像差异。
- [GLM-5.3 在 A3 与950的未验证参考部署拓扑](sglang_ascend_doc_glm_5_3.md)：融合A3单节点改编、四节点PD及950 MXFP8参考分支，保留未独立硬件验证、MTP与MemFabric边界。
- [GLM-5.3-Flash 在 A3 与 950 的分平台精度和 PD 配方](sglang_ascend_doc_glm_5_3_flash.md)：保留 A3 W8A8 与 950 W8A8_MXFP8 的页大小、推测参数、并行和传输协议差异。
- [GLM-5 在旧 CANN8.5 镜像的部署与 MTP 边界](sglang_ascend_doc_glm_5_legacy.md)：记录旧 GLM-5 的A2/A3镜像、A3单机W4A8/双机BF16及未测PD，不替代GLM5.1后续教程。
- [Hy3 在 A3 的 BF16 单节点服务与推理模式](sglang_ascend_doc_hy3.md)：记录 Hy3 的 A3 TP16 容量起点、EAGLE/graph 组合和按请求选择 reasoning_effort 的边界。
- [Kimi-K2.6 在 A3 的多模态、长输入与共享前缀配置](sglang_ascend_doc_kimi_k2_6.md)：把 Kimi-K2.6 的固定版本 W4A8/EAGLE3 配方按随机文本、共享前缀和图像负载区分。
- [Kimi K3在A3与950的参考混部、2P4D和草稿配置](sglang_ascend_doc_kimi_k3.md)：按生成器真实NPU cell限定W4A8/MXFP4、KDA预算、DSPARK和MemFabric，保留验证进行中、容量TODO及HiCache测试差异。
- [SGLang 旧昇腾配方的并行选择与性能证据边界](sglang_ascend_doc_legacy_recipe_comparison.md)：保留旧 R1、V3.2-Exp、Qwen/Coder/Next 的A2/A3工作负载与同名指标差异，避免跨版本比较。
- [MiMo-V2.5-Pro 的 MXFP4 与 DFlash PD 参考配置](sglang_ascend_doc_mimo_v2_5_pro_dflash.md)：记录A3固定v0.5.18-cann9.0.0-a3镜像下MiMo FP4/DFlash的DP2/TP8、device_urma与分角色验证要求。
- [MiMo-V2-Flash 在 A3 的 PD 与分层 EAGLE 配方](sglang_ascend_doc_mimo_v2_flash.md)：区分 MiMo W8A8 的容量起点、实际 P/D 资源、DP 选路、SWA 预算与 TTFT/TPOT 负载。
- [MiniMax-M2.5在A3的外部EAGLE3与A2单请求配方](sglang_ascend_doc_minimax_m2_5.md)：比较 MiniMax QuaRot W8A8 在长前缀、低延迟和高并发下的 DeepEP/fuseep 与调度选择。
- [Qwen3-235B 在 A3 的混部、256K 与 PCP 文档边界](sglang_ascend_doc_qwen3_235b.md)：区分 Qwen3-235B BF16/W8A8 的测量负载及同版本文档对 CP=TP 和 CP 整除 TP 的冲突。
- [Qwen3.5-397B 在 A3 的混合状态缓存与长输入配方](sglang_ascend_doc_qwen3_5_397b.md)：记录 Qwen3.5 W4A8 MTP 的 GDN、NEXTN、DeepEP 与 extra_buffer 前缀复用配置及负载指标。
- [Qwen3.6 在 A3 的多模态与混合状态缓存配置](sglang_ascend_doc_qwen3_6_hybrid.md)：合并 27B 和 35B-A3B 的 BF16/W8A8、NEXTN、ViT graph、extra_buffer 与超长输入案例。
- [Qwen3.8-Max 在 A3 四节点的 W4A8 混部起点](sglang_ascend_doc_qwen3_8_max.md)：记录 daily build 的 TP64/DP4、DeepEP 和容量条件，不把内置 MTP 或教程命令当已测推测收益。
- [Qwen3 小中规模模型在 A3 的延迟与并发配方](sglang_ascend_doc_qwen3_compact_serving.md)：比较 8B、30B-A3B 和 32B 的容量起点、EAGLE3、graph、请求负载及 A2 证据边界。
- [Qwen3-Next 在当前上游的量化主模型与 NEXTN 配方](sglang_ascend_doc_qwen3_next_current.md)：把 v0.5.18 的 Qwen3-Next A3 混部与已有旧补丁的 CP 方案区分，保留图和 draft 权重条件。
