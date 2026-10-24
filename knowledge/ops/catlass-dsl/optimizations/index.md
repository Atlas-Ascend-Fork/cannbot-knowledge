# optimizations

- [AIV 向量布局与 MTE](aiv_vector_layout_mte.md)：面向 AIV/vector-only 算子的布局、连续访问和任务粒度优化候选。
- [CANN Performance：Attention 多级流水与负载均衡](attention_pipelines.md)：从 Flash Attention Lite 与全量化 FIA 递进样例提取片内交换、CV/L0/I-O 多级流水、代价感知分核和 DN 归约候选；另含任务映射 swizzle、掩码窗口化、decode split-KV、HEAD_DIM 参数化、sink 状态播种与单 KV 块双 Q 块融合方案。
- [CANN 样例：带宽扫描与模板选择](bandwidth_template_selection.md)：用隔离读、读写、读算写数据流和 UB tile/buffer 成对扫描，为 CATLASS 搬运候选建立实测上限。
- [Buffering 与数据搬运](buffering_and_data_movement.md)：L1/L0/UB buffering、复用与 GM 流量优化的可证伪策略。
- [优化证据门禁](evidence_gates.md)：将源码启发、profile 假设、正确性和 benchmark 结论严格分离。
- [CANN Performance：MatMul 与 Grouped MatMul 模板选择](matmul_and_grouped.md)：从 MatMul/GMM 递进样例提取按 Bound 选模板、组间连续排核、动态 M 均衡、Scale/Weight 布局和 L2 bypass 候选。
- [CANN 样例：MatMul 片上复用与布局候选](matmul_memory_and_layout.md)：从 CANN Features 样例提取全载、L1 Bank 隔离、Scale 聚合缓存、SWAT 遍历和预转换权重候选。
- [CANN 样例：MatMul 深流水与预取候选](matmul_pipeline_and_preload.md)：从 CANN Features 样例提取 N-buffer、MMAD/Fixpipe unit flag 和跨 tile MTE2 预取实验。
- [Mixed CUBE/VECTOR 局部块算子](mixed_cube_vector_kda.md)：面向 attention-like 和 KDA 局部块的 CUBE/AIV 分工、片上交接与 solve 优化候选。
- [CANN Performance：MoE 通信前量化](moe_communication.md)：从 MoE Dispatch/Combine 专题提取通信前量化、搬运、反量化三阶段候选及端到端门禁。
- [CANN 样例：多核尾轮与 Split-K 调度候选](multicore_load_balancing.md)：从 CANN Features 样例提取尾块再切分、DP+Split-K 混合调度及 workspace 归并候选。
- [计算搬运重叠与同步轴](pipeline_and_synchronization.md)：使用显式 buffer 轮换、unit_flag、flag、mutex 和 barrier 调整流水依赖。
- [CANN Performance：RegBase、SIMD 与归约链优化](regbase_and_reduction.md)：从 GELU、Softmax、RmsNormQuant、KV-RMSNorm-RoPE 和 SIMD VF 专题提取寄存器融合、循环组织、归约并行与大 tile 候选。
- [CANN Performance：Scalar 代码生成减负](scalar_codegen.md)：从 ScalarBound 专题提取寄存器 spill、I-cache、分支和动态别名的诊断与可证伪代码形态候选。
- [舍入差异集合的选择性修正](selective_rounding_exception_fastpath.md)：当硬件 cast 与正确性 oracle 只在稀有位型上不同，先刻画差异集合，再修正例外并保留原生 cast 主路径。
- [CANN Performance：SIMT 不规则访存与冲突处理](simt_irregular.md)：从 Histogram、Scatter 和 MoE Routing 专题提取 grid-stride、原子/单写者、二维线程布局、向量 load 与 GridDim 扫描候选。
- [Tile 与本地内存容量预算](tiling_and_capacity.md)：依据 C310 L1/L0/UB 容量筛选 tile 候选，并用实测决定是否接受。
- [CANN 样例：Vector、寄存器与 CUBE–Vector 数据路径候选](vector_register_and_cv_path.md)：从 CANN Features 样例提取 VF 融合、寄存器搬运选型、SIMD 约束、SIMT Gather、HiF8 与 L0C→UB 直通候选。
