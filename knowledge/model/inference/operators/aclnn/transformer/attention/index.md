# 注意力算子

- [AttnResFwd（Kimi 残差 bank 融合）950 ACLNN 算子知识](vllm_ascend_attn_res_fwd_950.md)：解析 Kimi K3 残差 bank 融合算子 AttnResFwd 在 vLLM Ascend 950/A5 上的四条 Route、Tiling ABI、UB 容量、BF16 舍入及同步边界，支持框架适配和性能诊断。
- [RecurrentGatedDeltaRuleV310 310P ACLNN 算子知识](vllm_ascend_recurrent_gated_delta_rule_v310_310p.md)：解析 V310 recurrent GDN 的 AIV 递推、Host profile 与 vStep、17字段 ABI、TBuf 字节账、状态预取及 310P 搬运和归约边界。

- [ChunkGatedDeltaRuleFwdHVllm 310P ACLNN 算子知识](vllm_ascend_chunk_gated_delta_rule_fwd_h_310p.md)：说明 Chunk H 310P 公开ACLNN参数、key0四种gate/state模板、Host Workspace与注册/POD ABI，以及统一核心WH/Vnew/KV/HUpdate、CATLASS缓冲与同步尾部边界。

- [ChunkFwdOVllm 310P ACLNN 算子知识](vllm_ascend_chunk_fwd_o_310p.md)：说明 Chunk O 310P 公开ACLNN空校验、Tiling4ChunkFwdOVllm与136B静态线ABI、两种gate模板，以及统一核心QK/QH/AV、因果mask分块、五Workspace片与32行内联输出的同步和尾部边界。

- [ChunkGatedDeltaRuleFwdHVllm A2/A3 ACLNN 算子知识](vllm_ascend_chunk_gated_delta_rule_fwd_h.md)：还原 A2/A3 公开 Chunk H 接口、32种模板选择、逐字段线布局、双stream的AIC/AIV交接、gate与state精度、128/256维资源及尾块边界。

- [ChunkFwdOVllm A2/A3 ACLNN 算子知识](vllm_ascend_chunk_fwd_o.md)：说明 Chunk O 在 A2、A3 上的公开 ACLNN 空校验与强制门控输入、五 Workspace 切片和17字段静态线布局，闭合四种数据模板、三次 Cube 与两次 AIV 后处理的流水、局部因果掩码、调度排空及 V 维和尾块的容量边界。

- [ChunkGatedDeltaRuleFwdHVllm 950 ACLNN 算子知识](vllm_ascend_chunk_gated_delta_rule_fwd_h_950.md)：说明 Chunk H 在 Ascend 950 上的公开 ACLNN、23字段线布局和六 Workspace，完整展开32种模板与直接UB、bounded GM、普通GM及极短尾分支，记录FP32 state持续保存、Regbase双寄存器、zN衰减值、ready/free握手和静态数据合同缺口。

- [ChunkFwdOVllm 950 ACLNN 算子知识](vllm_ascend_chunk_fwd_o_950.md)：说明 Chunk O 在 950 上的公开 ACLNN、五 Workspace 切片和17字段静态线布局，闭合四模板与三次 Cube、两次 AIV 后处理，以及 Ascend950 的 ND2NZ、LoadData2DV2、CO12Dst 搬运、248KiB UB 与固定视图和调度边界。

- [KdaGateCumsumVllm A2/A3 ACLNN 算子知识](vllm_ascend_kda_gate_cumsum.md)：说明 KDA 门控累加在 A2、A3 的公开 ACLNN 校验、六种数据与安全门控模板、四种布局和定长或变长任务调度，闭合16字段128B静态线布局、七个TBuf、FP32逐chunk前缀累加及手动搬运同步与精度边界。

- [KdaGateCumsumVllm 950 ACLNN 算子知识](vllm_ascend_kda_gate_cumsum_950.md)：说明 KDA gate cumsum（门控累加）在 950 的公开 ACLNN：chunkSize 取 32、64、128，六种数据与安全门控模板、四种布局和定长或变长分核，以及128B线布局、七个TBuf、逐chunk FP32前缀累加和手动同步与精度边界。

- [KdaLayoutSwap12 A2/A3 ACLNN 算子知识](vllm_ascend_kda_layout_swap12.md)：说明 KDA layout swap12（布局交换）在 A2、A3 的公开ACLNN：rank3交换轴0/1、rank≥4交换轴1/2，三dtype的六条分组或单行DMA路线、48B静态线布局、8192元素TBuf，以及dependency、stride单位、尾块和手动同步边界。
- [KdaLayoutSwap12 950 ACLNN 算子知识](vllm_ascend_kda_layout_swap12_950.md)：说明 KDA layout swap12（布局交换）在 950 的公开ACLNN：rank3交换轴0/1、rank≥4交换轴1/2，三dtype的六条分组或单行DMA路线、48B静态线布局、8192元素TBuf，以及dependency、stride单位、尾块和手动同步边界。

- [SGL 自适应块稀疏注意力 A2/A3 ACLNN 算子知识](sgl_ada_block_sparse_attention.md)：闭合 SglAdaBlockSparseAttention 的八个 router、动态负载分配与双 Matmul/在线 softmax；draft保留空展开Host guard、无匹配key、回调参数和UB容量风险。
- [SGL 分块门控 Delta 递推 A2/A3 ACLNN 算子知识](sgl_chunk_gated_delta_rule.md)：追溯 aclnnSglChunkGatedDeltaRule 在A2/A3上的三阶段 Cube/Vector 原生实现、POD、状态与 workspace；长度内容和 chunk 容量未校验，本卡为未经运行验证的源码草稿。
- [SGL 分块门控 Delta 递推 950 ACLNN 算子知识](sgl_chunk_gated_delta_rule_950.md)：追溯 aclnnSglChunkGatedDeltaRule 在950上的三阶段 Cube/Vector 原生实现、POD、状态与 workspace；长度内容和 chunk 容量未校验，FP32 状态仍以 BF16 镜像参与 Cube，本卡为未经运行验证的源码草稿。
- [分块 KDA 前向 A2/A3 ACLNN 算子知识](sgl_chunk_kda_fwd.md)：说明 aclnnSglChunkKdaFwd 在A2/A3上的逐通道门控分块前向、Host/POD、五阶段及安全与非安全解路线；固定源码存在静态校验、索引/地址风险，供draft源码分析，未经运行验证。
- [分块 KDA 前向 950 ACLNN 算子知识](sgl_chunk_kda_fwd_950.md)：说明 aclnnSglChunkKdaFwd 在950上的逐通道门控分块前向、Host/POD、五阶段及融合/直接UB路线；固定源码存在静态校验、索引与初始化风险，供draft源码分析，未经运行验证。
- [有状态 KV 压缩 A2/A3 ACLNN 算子知识](sgl_compressor.md)：说明 aclnnSglCompressor 在A2/A3上的投影、APE、压缩、RMSNorm/RoPE、缓存更新与完整Host/POD/MIX路线；A2/A3带seqused的批次遍历在请求耗尽后仍可能读取seqused[B]，且大维度窄化、metadata内容未校验，为未经运行验证的draft源码事实。
- [有状态 KV 压缩 950 ACLNN 算子知识](sgl_compressor_950.md)：说明 aclnnSglCompressor 在950上的投影、APE、压缩、RMSNorm/RoPE、缓存更新与完整Host/POD/MIX路线；950 NORMAL环形缓存复用依赖零初始化readGen，FULL_LOAD对seq_used与容量的计数分歧及零产出loop更新次序存在静态风险，为未经运行验证的draft源码事实。
- [CompressorV2 A3 ACLNN 算子知识](sgl_compressor_v2.md)：说明 CANN9.2 aclnnCompressorV2 在 A3 的双投影、分组 softmax 压缩与原地环形缓存更新，闭合 FullLoad/Perf/空输入路线、POD及GM/UB/L1/L0字节账；保留初始化、资源和发布合同差异。
- [FlashMla 非量化分页共享 KV 950 ACLNN 算子知识](sgl_flash_mla_950.md)：解析aclnnFlashMla在950的576维QK与512维共享V、48个模板组合、FA/FD调度与CV握手；保留metadata必传、长度guard及stride窄化边界，未作运行验证。
- [LaserAttention A2/A3 ACLNN 算子知识](sgl_laser_attention.md)：追溯 aclnnSglLaserAttention 的 FP16 Cube/Vector 流水线、逐字段参数与内存同步；存在调度成员读前未初始化等静态缺陷，不能据此认定安全或数值正确。
- [LightningIndexer V3 候选块源 A3 ACLNN 算子知识](sgl_lightning_indexer_v3_candidates.md)：说明 CANN9.2 aclnnLightningIndexerV3 在A3的加权ReLU双级TopK、普通/BatchInvariant分核和CV内存同步；保留候选分片漏写、零任务TND清理与PA地址静态边界，未验证安全复用。
- [SGL MLA预处理浮点KV缓存 A2/A3 ACLNN 算子知识](sgl_mla_preprocess_float_cache.md)：闭合 aclnnSglMlaPreprocess 的qmode0浮点cache0/1/3、Host/POD、三乘与AIC/AIV交接；draft保留AIC未初始化成员、第三乘L0C地址及非匹配qmode终点风险。
- [SGL MLA预处理INT8缓存 A2/A3 ACLNN 算子知识](sgl_mla_preprocess_int8_cache.md)：闭合 aclnnSglMlaPreprocess qmode0/cache2 的BF16投影、INT8 NZ缓存与逐头Q量化；draft保留AIC未初始化成员、第三乘L0C地址和不匹配qmode风险。
- [MLA Prolog V4 浮点融合 A2/A3 ACLNN 算子知识](sgl_mlaprolog_v4_float.md)：说明V4WeightNz浮点五返回与两cache副作用、208B POD、全部布局及四MM/Vector路线，保留UB对齐和条件非法key静态边界。
- [MLA Prolog V4 浮点融合 950 ACLNN 算子知识](sgl_mlaprolog_v4_float_950.md)：说明V4WeightNz浮点五返回与两cache副作用、208B POD、全部布局及四MM/Vector路线，保留UB对齐和条件非法key静态边界。
- [MLA Prolog V4 BF16 与 INT8 部分量化 A2/A3 ACLNN 算子知识](sgl_mlaprolog_v4_w1_kv0.md)：说明V4(1,0,0)的BF16前投影与INT8第三投影、N阈值两路线、208B POD和typed内存同步，保留零scale、对齐与条件非法key边界。
- [MLA Prolog V4 BF16 与 INT8 部分量化 950 ACLNN 算子知识](sgl_mlaprolog_v4_w1_kv0_950.md)：说明V4(1,0,0)的BF16前投影与INT8第三投影、N阈值两路线、208B POD和typed内存同步，保留零scale、对齐与条件非法key边界。
- [MLA Prolog V4 部分量化与逐通道 INT8 缓存 A2/A3 ACLNN 算子知识](sgl_mlaprolog_v4_w1_kv2.md)：说明V4(1,2,0)的BF16前投影、INT8第三投影与KV/Kr逐通道量化、完整N路线和208B POD，保留两平台cast差异及arch22未绑定clip读取。
- [MLA Prolog V4 部分量化与逐通道 INT8 缓存 950 ACLNN 算子知识](sgl_mlaprolog_v4_w1_kv2_950.md)：说明V4(1,2,0)的BF16前投影、INT8第三投影与KV/Kr逐通道量化、完整N路线和208B POD，保留两平台cast差异及arch22未绑定clip读取。
- [MLA Prolog V4 部分量化与 tile INT8 合并缓存 A2/A3 ACLNN 算子知识](sgl_mlaprolog_v4_w1_kv3.md)：说明V4(1,3,0)的BF16与INT8投影、tile128裁剪量化和656B合并KV/Kr/scale，闭合ND与PA_BSND实际路线、POD及资源同步。
- [MLA Prolog V4 部分量化与 tile INT8 合并缓存 950 ACLNN 算子知识](sgl_mlaprolog_v4_w1_kv3_950.md)：说明V4(1,3,0)的BF16与INT8投影、tile128裁剪量化和656B合并KV/Kr/scale，闭合ND与PA_BSND实际路线、POD及资源同步。
- [MLA Prolog V4 INT8 投影与 BF16 缓存 A2/A3 ACLNN 算子知识](sgl_mlaprolog_v4_w2_kv0.md)：说明V4(2,0,0)的三次INT8投影、BF16吸收投影及BF16缓存、完整N阈值路线、208B POD和typed内存同步，保留零scale、UB对齐及条件非法key边界。
- [MLA Prolog V4 INT8 投影与 BF16 缓存 950 ACLNN 算子知识](sgl_mlaprolog_v4_w2_kv0_950.md)：说明V4(2,0,0)的三次INT8投影、BF16吸收投影及BF16缓存、完整N阈值路线、208B POD和typed内存同步，保留零scale、UB对齐及条件非法key边界。
- [MLA Prolog V4 INT8 全投影与 Query/KV 量化 A2/A3 ACLNN 算子知识](sgl_mlaprolog_v4_w2_kv1.md)：说明V4(2,1,1)的INT8三投影、Query逐head动态INT8与KV标量INT8量化、BF16 Kr及Qr倍率，闭合全部splitN路由、208B POD、字节与同步，保留零scale和静态边界。
- [MLA Prolog V4 INT8 全投影与 Query/KV 量化 950 ACLNN 算子知识](sgl_mlaprolog_v4_w2_kv1_950.md)：说明V4(2,1,1)的INT8三投影、Query逐head动态INT8与KV标量INT8量化、BF16 Kr及Qr倍率，闭合全部splitN路由、208B POD、字节与同步，保留零scale和静态边界。
- [MLA Prolog V4 INT8 全投影与分组量化合并缓存 A2/A3 ACLNN 算子知识](sgl_mlaprolog_v4_w2_kv3.md)：说明V4(2,3,0)的INT8三投影与四组classic INT8裁剪量化、656B合并KV/Kr/scale、完整splitN路由和208B POD，保留零scale、typed内存峰值和条件错误边界。
- [MLA Prolog V4 INT8 全投影与分组量化合并缓存 950 ACLNN 算子知识](sgl_mlaprolog_v4_w2_kv3_950.md)：说明V4(2,3,0)的INT8三投影与四组classic INT8裁剪量化、656B合并KV/Kr/scale、完整splitN路由和208B POD，保留零scale、typed内存峰值和条件错误边界。
- [MLA Prolog V4 MXFP8 投影与 BF16 缓存 950 ACLNN 算子知识](sgl_mlaprolog_v4_w3_kv0_950.md)：说明V4(3,0,0)的E4M3/E8M0分组投影、完整splitN/M与208B POD及资源同步，保留单行尾通知、空缓存预零和条件内存缺陷。
- [MLA Prolog V4 MXFP8 投影与 Query、KV 量化 950 ACLNN 算子知识](sgl_mlaprolog_v4_w3_kv1_950.md)：说明V4(3,1,1)的MXFP8投影、Query动态量化、KV乘法量化与Qr缩放，闭合splitN/M资源同步并保留尾通知、预零及零scale静态限制。
- [MLA Prolog V4 MXFP8 投影与分组混合缓存 950 ACLNN 算子知识](sgl_mlaprolog_v4_w3_kv3_950.md)：说明V4(3,3,0)的E4M3/E8M0投影、tile128动态缓存和656字节合并槽，闭合splitN/M、12个selector、208B POD及精度同步边界。
- [MLA Prolog V4 FP8 投影与 BF16 缓存 950 ACLNN 算子知识](sgl_mlaprolog_v4_w4_kv0_950.md)：说明V4(4,0,0)的E4M3投影与FP32 scale、26个splitN selector、208B POD和逐head同步，保留MX搬运特化、零scale及UB边界。
- [MLA Prolog V4 FP8 投影与静态缓存及动态 Query 950 ACLNN 算子知识](sgl_mlaprolog_v4_w4_kv1_950.md)：说明V4(4,1,1)的FP8投影、静态KV量化与动态Query/Qr尺度补偿，闭合26个selector、134016B后处理UB及逐head同步。
- [MLA Prolog V4 FP8 投影与分组混合缓存 950 ACLNN 算子知识](sgl_mlaprolog_v4_w4_kv3_950.md)：说明V4(4,3,0)的FP8投影和656字节KV/Kr/scale合并缓存，闭合6个selector、分组量化精度、208B POD及clip指针静态边界。
- [MLA Prolog V4 HIF8 投影与 BF16 缓存 950 ACLNN 算子知识](sgl_mlaprolog_v4_w5_kv0_950.md)：闭合V4(5,0,0)在950的HIF8投影、FP32直量化Cq、BF16缓存与完整splitN资源同步，保留条件非法key、尺寸窄化及UB预算边界。
- [MLA Prolog V4 HIF8 投影、Query 与逐张量缓存量化 950 ACLNN 算子知识](sgl_mlaprolog_v4_w5_kv1_950.md)：闭合V4(5,1,1)在950的HIF8投影、逐张量KV与Query动态量化、Qr二次缩放及MIX资源同步，保留零scale、条件非法key与UB预算边界。
- [MLA Prolog V4 HIF8 投影与逐块合存缓存 950 ACLNN 算子知识](sgl_mlaprolog_v4_w5_kv3_950.md)：闭合V4(5,3,0)在950的HIF8投影、tile128量化与656B KV/Kr/FP32scale合存及MIX资源同步，警示Host禁止clip但Device仍可达读取表达式。
- [PoolKeyIndexer V2 浮点池索引 950 ACLNN 算子知识](sgl_pool_key_indexer_v2_float_950.md)：闭合 CANN9.2 aclnnPoolKeyIndexerV2 非量化/仅索引的950 CV路径、legacy/compact尾部布局及SGL旧pair映射；保留L0分块、小G权重读取与UB容量静态边界，未验证安全复用。
- [SGL 共享KV稀疏注意力 A2/A3 ACLNN 算子知识](sgl_sparse_attn_sharedkv.md)：闭合 aclnnSglSparseAttnSharedkv 的 A2/A3 SWA、CFA、SCFA 源码路线与MIX资源；draft保留SWA/CFA非首S2的UB容量风险及SCFA索引、分页子块和未写workspace风险，不代表运行正确性。
- [SGL 稀疏 FlashAttention A2/A3 ACLNN 算子知识](sgl_sparse_flash_attention.md)：说明 aclnnSglSparseFlashAttention 在A2/A3上的公开语义、Host/POD、逐key MIX流水、内存/同步与精度；小block V路线实际MM2复用K而非独立V，C路线稀疏游标读取与raw空KV路径存在静态风险，为未经运行验证的draft源码知识。
- [SGL 稀疏 FlashAttention 950 ACLNN 算子知识](sgl_sparse_flash_attention_950.md)：说明 aclnnSglSparseFlashAttention 在950上的公开语义、Host/POD、逐key MIX流水、内存/同步与精度；实际MM2复用K而非独立V，SharedParams及本地地址字段有未初始化读取，索引越界/空KV路径无安全保证，为未经运行验证的draft源码知识。
- [SparseFlashMla 稀疏共享 KV 注意力 A2/A3 ACLNN 算子知识](sgl_sparse_flash_mla.md)：闭合aclnnSparseFlashMla在A2/A3的SWA/HCA/CSA与原始槽位选择、七槽L1和GM流水；保留TND长度绑定、UB子区搬运及metadata调度差异，未作运行验证。
- [SparseLightningIndexer A3 ACLNN 算子知识](sgl_sparse_lightning_indexer.md)：说明 CANN9.2 aclnnSparseLightningIndexer 在 A3 的候选块内加权 ReLU TopK、8 个 dtype/layout 实例、MIX Cube/Vector 同步与字节账；保留 PA stride、前缀求值和资源 guard 的静态限制。
