# implementation patterns

- [在 SIMD 中复现 bf16 的 ties-to-even 舍入](bf16_ties_to_even.md)：SIMD 的 f32→bf16 转换默认 round-half-away-from-zero，与 GEMM 的 round-half-to-even 不一致，需位运算仿真。
- [广播加载与 SIMT 收尾](broadcast_and_simt_epilogue.md)：用 DIST_BRC_B32 做行广播，用 simt 模式的 thread_block_dim 处理非对齐标量写。
- [容量反推 tiling](capacity_driven_tiling.md)：先枚举 L1/L0A/L0B/L0C/UB 的可用字节，再反推 tile 形状，而不是先定 tile 再撞容量。
- [单个 cross flag 的双向互斥用法](cross_flag_bidirectional.md)：用一个 cross flag 在 CUBE 与 VECTOR 之间交替传递所有权，代替 ready/free 两个单向 flag。
- [显式声明支持域，禁止静默回退](declare_support_domain.md)：用前置断言声明算子支持域；不得在 host 侧静默回退到 torch/vendor 实现。
- [GEMM 主导 kernel 的优化阶梯](gemm_optimization_ladder.md)：当时间集中在 MAC 与 MTE2 两条管道时，按"定位 → 波次量化 → L1 双缓冲 → L0 双侧双缓冲 → 判停"的顺序推进，并记录各级的结构上限。
- [用 @tla.jit 把 kernel 拆成可独立验证的 stage](jit_stage_decomposition.md)：把缩放/统计更新/收集/写回拆成 @tla.jit 函数，主 kernel 变短且每个 stage 可单独编译验证。
- [L0C 经 SPLIT_M 直通 UB](l0c_to_ub_split_m.md)：累加结束后用 CopyL0C2DstParams(SPLIT_M) 一次搬进两个 AIV 的 UB，中间结果不落 GM。
- [L1 半区偏移与双缓冲 flag 配对](l1_half_region_double_buffer.md)：用固定字节偏移把 L1 分成两个半区，每半区放 A 与 B tile，配合两套 flag 实现搬运与计算重叠。
- [在线 softmax 的统计量递推](online_softmax_stats.md)：逐块更新 running max 与 running sum，并正确处理 rescale、尾块掩码与缩放顺序。
- [预计算索引结构（bucket + 链表）替代 gather](precomputed_index_structure.md)：逐 chunk 寄存器 gather 的成本随 V 线性增长（O(M·K·V/64)）；预计算索引把它降到 O(M·K + M·V/BN)，大 V 时快两个数量级。
- [按行独占的并行划分（每 block 一个 Cube 与两个 AIV）](row_ownership_parallelism.md)：按 M 切块让每个 block 独占完整行，行统计免跨块归约；代价是小 M 时块数不足。
- [静态展开优先，动态循环只用于真正运行时边界](static_unroll_first.md)：编译期常量用 Constexpr 形参 + Python range 展开；动态 trip count 循环里避免复杂 vec.func。
- [统计量打包在同一 UB 张量的列偏移里](ub_stats_packing.md)：把行 max、临时值、行 sum 存在 [rows, 64] 张量的第 0/16/32 列，配合广播加载减少 buffer 数量。
- [零拷贝视图：用 layout 表达转置与切片](zero_copy_views.md)：通过 ColumnMajor/ptr 算术构造 GM 视图，避免 host 侧预转置与额外搬运。
