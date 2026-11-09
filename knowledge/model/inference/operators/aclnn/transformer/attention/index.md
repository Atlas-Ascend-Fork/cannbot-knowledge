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
