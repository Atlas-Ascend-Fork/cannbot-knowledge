# performance

- [逐 block 串行启动退化多核并行](block.md)：Ascend950 上按行切分多核的算子，若 launch 函数用 host 侧 for 循环逐 block 调 <<<1, nullptr, stream>>>，多核并行会退化为'启动开销 × block 数'的串行链；改单次 <<<numBlocks>>> + kernel 内 GetBlockIdx/GetBlockNum 自算行区间后，case1 耗时 42866µs→705µs（约 60× 相对）、20/20 精度不变。
- [block 数应覆盖可用 Vector 核](block_count_uses_all_available_vector_cores.md)：Host 的固定 block 上限低于目标设备实测 Vector Core 数；把上限绑定到同设备探针结果后，配对端到端性能改善且正确性未退化。
- [blockLength 对齐 slice 致 numBlocks 塌缩单核](blocklength_slice_numblocks.md)：SwiGlu host tiling 把 blockLength 对齐到 slice 边界后，当 totalSlices < coreNum（极端 totalSlices=1）时 numBlocks=min(coreNum,totalSlices/minSlicesPerCore) 塌缩为 1，整 block 串行单核，大 shape case 退化约一个数量级；判别方法：对齐版大 slice case 成对耗时远高于不对齐版即命中。
- [301 非连续多核启用：preferMultiCore 守护](broadcast_301_nlast_transpose_multicore_reverse_search.md)：brc 301 NLastTranspose 非连续 case 多核未触发因 preferMultiCore 对连续/非连续混用；须 `preferMultiCore && !inputAllContiguous` + DoTiling(0,0,true) 强制。
- [按序列位缓存 cos/sin 并让 q/k 共享搬运](cache_position_coefficients_across_shared_inputs.md)：逐行重复搬入和展开相同 cos/sin 会拖慢小行宽 Vector kernel；按序列位缓存并在 q/k 间共享可减少 GM→UB 事务。
- [csr2gebsr 双指针法窄矩阵退化](csr2gebsr.md)：csr2gebsr Convert 用双指针法替代 BinarySearchCsrRow，窄矩阵严重退化、大矩阵改善，回退禁用。
- [cube_l1_reuse_setting 32 非单调反退](cube_l1_reuse_setting_32.md)：Ascend950 上 cube_l1_reuse_setting={-1:32} 相对甜点 {-1:16} 略差，L1 占用上升挤压其他 cube 数据；banned，不得盲目增大 L1 复用次数。
- [cummin 非末维 batch-inner 跨步扫描 banned](cummin_batch_inner_banned.md)：cummin 非末维用 batch-inner（按 dim 步逐次搬入 innerSize 元素并标量比较）替代 transpose，在大 dimSize case 上相对 transpose 路线慢 37-78×，整体评分下降；该路线 banned，应保留 transpose。
- [Duplicate 掩码向量化未修复 triu 大 shape 失败](duplicate_triu_shape.md)：triu 大 shape Case9 失败初判为标量 SetValue 掩码瓶颈，改 Duplicate 0 填充向量化后仍失败；后续 timing 定位实为 per-tile event flag 耗尽的正确性问题（非超时），Duplicate 向量化路线 banned。
- [UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽](duplicate_ub_prefill_hurts_pure_write_bandwidth.md)：在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。
- [flat 多核切分 elementwise scalar 主导诊断](flat_elementwise_scalar.md)：flat 多核切分的 elementwise 算子在 msprof PipeUtilization 上呈现 scalar_ratio 主导、核间严重不均衡、MTE2 带宽远未饱和的诊断方法与机制解释。
- [Gather 非 last-dim 转置+索引换算预处理占比高](gather_last_dim.md)：Ascend950 上 Gather 算子当 dim != last 时，plugin 端 permute+contiguous 转置与 Cast/Mul/Cast 三段索引 byte-offset 换算合计占 case 总耗时的 58-83%，kernel 本身仅占 17-41%。
- [L2 读写端口独立并行 HBM 总线串行共享](l2_hbm.md)：Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。
- [MIX_AIC_1_1 仅启用 28/56 AIV 带宽不饱和](mix_aic_1_1_underutilizes_aiv_on_1_to_2_topology.md)：A5（Ascend950PR，28 CubeCore:56 VectorCore）上 KERNEL_TYPE_MIX_AIC_1_1 强制 1:1 配比，blockNum 上限=28，只启用 28/56 AIV（50%），HBM 带宽无法饱和；测 HBM 带宽应回退到 AIV_ONLY 56 核路线，MIX_AIC_1_1 在此场景 banned。
- [Mix合图包入 V2 致任务数减半 E2E 劣化](mix_v2_e2e.md)：Ascend950（CANN 9.1.0）上 sparse_flash_attention_quant _d_950 变体，把 sg_set_scope Mix合图闭合点后移使 V2 段（division+cast）也包入调度域后，AICore Utilization 从 67% 升到 80% 但 Total Task Count 从 2304 减半到 1536（并行度下降），E2E 反而从 729us 劣化约 1.13× 到 824us；精度未退化但仍回退，V2 入 Mix合图在本算子结构下 banned。
- [MulPreferContiguous 稀疏广播拦截失败且慢于 304](mulprefercontiguous_304.md)：B 类稀疏广播（首轴稀疏、stride 大）触发 MulPreferContiguous 拦截转连续，baseline GetWorkspaceSize 返回 -1.0（schMode 空）或性能慢于 fixed 直接走 304 nddma_transpose_noLoop。
- [PyPTO loop_unroll 串行 s2 循环诊断](pypto_loop_unroll_s2.md)：PyPTO decode 算子 no_flash compute 路径 s2_kv tile 循环以 unroll_list={1} 串行执行 4 次独立迭代，AICore E2E 超 500us 目标而利用率已 93%+、0 瓶颈；用 perf-analyze 解析 bubble_analysis.log + 内核源码检视 unroll_list 与迭代依赖性二分定位为串行迭代链未并行化，而非调度/搬运瓶颈。
- [随机 Gather 每元素 DMA 过慢—改 SIMT 直访 GM](random_gather_per_element_dma_should_switch_to_simt_direct_gm.md)：逐输出独立的随机索引读取不应为每个元素提交 GM→UB→GM DMA；优先用 SIMT grid-stride 直访 GM，保留逐元素 DMA 槽路线作安全回退。
- [逐rank flag同步打断MTE2连续搬运](rank_flag_mte2.md)：ReduceScatter 远程读逐 rank DataCopy 被前后 V_MTE2/MTE2_V flag 包夹，MTE2 流水反复 stall 无法连续，msprof 显示 aiv_mte2_time 占 T_comm 主导、带宽打不满；判别靠 msprof task-based aiv_mte2_time + 三段注释法交叉验证 vec/reduce 非瓶颈。
- [每核最少行数地板压低 AIV 并行度—按可用核数切分](row_reduction_min_rows_floor_underutilizes_aiv.md)：行级归约 tiling 不应先用每核最少行数限制 block 数；按可用 AIV 核数上限切分可恢复并行度。
- [稀疏不规则输出算子 SIMD 标量退化诊断](simd.md)：每行输出长度不规则的稀疏索引算子在 SIMD 模型下退化为逐行标量 GetValue 循环，scalar pipe 占比 80%+；用 msprof PipeUtilization 的 aiv_scalar_time ratio 判别。
- [删 smalle slim TU 致 e≤32 decode icache 税](smalle_slim_tu_e_32_decode_icache.md)：对 moe_topk_softmax 去重重构尝试删 smalle slim TU（base 并入 full 大 TU，4→2），msprof N=9 interleaved 18 档实测 full 入口相对 smalle 在 e≤32 decode 全 FAIL（+2.53%~+15.38%），门未过→保 smalle（4→3）；记录 banned 删除路线与 icache 取指税边界。
- [通算流水 tileCnt>1 性能反降 banned](tilecnt_1_banned.md)：matmul_reducescatter 通算流水 tileCnt>1 即使精度通过、死锁解除，端到端耗时随 tileCnt 反增；根因为 fixpipe 固定开销随 Blaze 调用次数线性累积 + Pattern B 依赖链限制流水窗口。tileCnt>1 路线 banned。
- [按行均分 tiling 致 nnz 倾斜时约半数核空闲](tiling_nnz.md)：稀疏算子 Host 按行数均分多核（不按 nnz），nnz 前重后轻时后半核约半数空闲，逐核 cycle 差距 20×+；用 msprof sample-based + ai_vector_core.db task_cyc 判别。

- [MLA Prolog decode A5 tile 调优配方](mla_prolog_decode_a5_tile_tuning_recipe.md)：A5/Ascend950 上 mla_prolog_quant_d decode 算子通过 4 项独立 tile_config 旋钮调优 (pre_quant_cube_tile k=256 / q_vec/k_vec 翻倍 / cube_wuk_tile k=64 / stitch_function_max_num=128) 使 E2E 相对初始 baseline 约 0.85x，精度全 PASS。
