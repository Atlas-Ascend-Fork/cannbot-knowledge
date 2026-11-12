# SGLang 昇腾优化规则与适用边界

本目录收录固定版本来源支持的知识；具体平台、配置和验证边界见各卡正文。

- [SGLang HiCache的MemFabric映射Host池与异步staging](sglang_ascend_cache_memfabric_host_io.md)：区分AIV可解引用的映射Host内存与普通pin-memory，说明首池固定reserve、MLA split/kernel_ascend条件、pinned事件保活与回退边界。
- [SGLang稀疏KV卸载的模型准入与预算分离](sglang_ascend_cache_sparse_offload_enable.md)：说明SGLANG_NPU_ENABLE_SPARSE_KV_OFFLOAD的Ascend双阶段DSA/MLA门槛、显式并发上界、indexer-only设备cell预算和Host容量代价。
- [SGLang KV静态预算与mem-fraction-static的正确调参方向](sglang_ascend_cache_static_budget.md)：用_profile_available_bytes说明权重后free内存、非静态slack、Mamba和多模态预留的扣费，并保留FAQ关于KV占用方向的冲突。
