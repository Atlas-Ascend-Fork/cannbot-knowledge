# SGLang 内核库集成指南

- [DeepEP A2：单机与跨机通信的缓冲、量化与人工验收](deepep_a2_communication.md)：按A2专用来源区分单机/跨机token边界、HCCL缓冲预算、分层通信变量和CI缺口，保留Normal API与配置指南的容量差异。
- [DeepEP Buffer：通信组绑定、策略选择与事件兼容边界](deepep_buffer_strategies.md)：说明 DeepEP Buffer 初始化时的 HCCL 通信组与策略绑定、Normal/Low-Latency 混用窗口，以及 EventOverlap 和清理接口在固定源码中的实际边界。
- [SGLang Batch Invariant：外部算子包安装与懒加载依赖](sgl_batch_invariant_installation.md)：区分sgl-kernel-npu中的Python封装、外部CANN算子.run包与batch_invariant_ops扩展，说明arch22/arch35接口支持与目标平台安装边界。
- [SGLang Kernel NPU 构建选择、依赖与安装身份](sgl_build_and_install.md)：区分 REFACTOR 和 legacy 构建入口、2201/3510 目标、原生算子选择、第三方依赖、子集 wheel 替换与加载边界。
- [SGLang pooled索引链的长度、页表和tail准备](sgl_pooled_indexer_metadata.md)：串联decode投影、pooled页表抽样、逐query因果长度展开及pool/tail索引展开，区分Torch与Triton后端和输出复用。
- [SGLang Torch Memory Saver：region、暂停恢复与内容保留边界](sgl_torch_memory_saver.md)：说明NPU虚拟地址保留、物理内存暂停恢复、tag与CPU备份，以及C++配对调用、同步和错误处理边界。

- [SGLang legacy因果卷积与recurrent GDN的状态接入](sgl_legacy_causal_conv_recurrent.md)：区分causal_conv1d原生与Python布局，说明线性verify候选窗口、BF16 recurrent_gated_delta_rule门控及状态提交边界。
- [SGLang legacy GDN的chunk、mega与三角逆调用路线](sgl_legacy_gdn_chunk_mega.md)：说明GDN_USE_MEGA_GDN分派、chunk64与mega128状态几何、FP16中间转换、构建范围及triangular_inverse单位三角布局。
- [SGL旧Torch路径的KV与状态传输接入](sgl_legacy_state_transfer.md)：识别kvcacheio四个Torch绑定的构建实现，区分整页KV、Mamba和direct槽位搬运的检查、空V风险与异步错误边界。

- [SGLang GE Helper直调Tiling缓存与图捕获地址生命周期](sgl_ge_helper_tiling_cache.md)：从固定ge_helper.h解释按Tiling类型与设备分区的512记录缓存、完整序列化键、eager预热、溢出路径与Host数据同步。
- [SGLang 原生算子声明与架构变体替换规则](sgl_native_operator_registration.md)：说明 sgl_register_operator 的执行单元、源码角色、架构变体整字段替换、combined Host 与 codegen 编译边界。
