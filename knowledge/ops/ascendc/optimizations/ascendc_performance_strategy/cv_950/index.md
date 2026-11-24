# 950 Cube-Vector 融合算子策略

> 目录划分：cv_950 收 Cube-Vector 融合类（MatMul/GEMM/BMM 及后处理融合）；conv_950 收卷积/反向传播类。平台 ID 为 950；正文中的 A5 为产品代际别名。

- [950 自动探索有效策略脱敏归档 — 2026-09-09](auto_exploration_archive_20260909.md)：A5 自动探索有效策略脱敏归档（2026-09-09）：收录 WQBM、GMMSQ 与 CV 任务 C 中构建、全量精度与同条件性能验证均通过的 adopted 机制，并记录被否方向的负向边界。

- [host 按 shape 与 dtype 自适应 tile 参数（行块高 / 列块宽 / 归约块深，含精度边界）](adaptive_tiling_params.md)：把切分参数（行块高/列块宽/归约块深）从编译期固定改为 host 按 shape 与 dtype 运行时分档下发。
- [AIV Chunk 级双缓冲流水](aiv_chunk_double_buffer_pipeline.md)：用深度 2 队列重构 Chunk 内 MTE2 读、向量计算、MTE3 写的软件流水，段内不变量外提 Chunk 循环、尾部专用工作改条件执行。
- [按行窗拆分 AIV 双 Lane 数据面](aiv_dual_lane_datapath_split.md)：把一核双 Vector Lane 中仅 Lane0 执行的数据面工作按互斥行窗均分给两条 Lane，保持跨核协议与数值路径不变。
- [GM→L1 面板宽搬运合并（按归约行块整行带宽 Nd2Nz，砍小搬运指令数）](bpanel_wide_nd2nz_kblock_copy.md)：把非驻留操作数面板 GM→L1 搬运粒度从「分形列带×归约行块」小搬运改为每行块整行带宽一次宽 Nd2Nz，L1 槽同步改按行块×分形紧排并同源改写内层装载寻址。
- [控制面去标量化（队列簿记显式槽位化 / tiling 块搬 / 批量 flag 轮询）](control_plane_dequeuing_and_batched_poll.md)：稳态循环的 staging 队列簿记换预分配槽位视图加最小 set/wait flag，tiling POD 改块搬进 TBuf，逐 flag 轮询改 32B 块批量轮询。
- [核亲和面板复用与跨 Tile 流水](core_affine_panel_reuse_and_cross_tile_pipeline.md)：把跨步轮转 tile 指派改为连续块核亲和指派（共享面板相邻 tile 同核复用），累加器队列加深双槽使写回与计算跨 tile 重叠，移除 tile 间全屏障。
- [归约分段跨 Block 扇出](cross_block_reduction_segment_fanout.md)：把输出块内彼此独立的归约分段作为独立任务扇出到空闲 Block，非属主写独占完成标志，属主确认全部分段可见后按原合并树汇聚。
- [归约轴跨 Lane 切分与两级合并](cross_lane_two_level_reduction.md)：把长归约轴切成互斥片段分配给各 Lane，各算局部统计量写独占 partial，阶段屏障发布后按稳定组合公式两级合并，各 Lane 只处理自己的输出片段。
- [多 Pass 操作数平面驻留复用](cross_pass_operand_plane_residency.md)：固定多 Pass 计算在每个外层块开始一次性装入去重后的唯一操作数平面并驻留片上，各 Pass 仅按索引只读复用，最后消费者结束后统一释放。
- [矩阵核到向量核交接流水（环形加深 + 同步精确化 + 条件等待 + 批量信用同步）](cv_handoff_pipeline.md)：组合环形加深、同步精确化、条件等待与批量信用同步，消除逐任务全流水排空与严格握手。
- [延迟释放等待以重叠相邻归约段](deferred_segment_free_double_buffer.md)：把段级 lock-step 握手中「段已释放」的等待推迟到下一段覆写前，形成深度 2 软件流水，稳态周期由生产+消费降为二者最大值。
- [按输出 dtype 自适应选择 scan 数值链（低精度输出用朴素累加替换补偿链）](dtype_adaptive_naive_scan.md)：按输出 dtype 编译期分支选择 scan 数值链：低精度输出用 fp32 域朴素累加替换补偿求和链（Kahan），高精度输出保留补偿链逐指令不变。
- [按有效跨度收缩尾块计算与向量工作域](effective_span_contraction_and_tail_work_elision.md)：执行计数、矩阵乘维度、转置网格和清零范围只覆盖对齐后的真实有效区，尾块不再计算或搬运整块填充区，布局容量保持满块。
- [收尾段代数化死工作消除（只喂养单调比较通路的偏置加法整段删除）](epilogue_algebraic_dead_work_elision.md)：删掉只喂养单调比较通路的偏置加法及其装载，连带其后随屏障与目标段 UB 写读往返一并消除。
- [scatter 宽度与 cube 内部 tile 宽度解耦（相邻列块融合 handoff slot）](epilogue_scatter_fusion.md)：把相邻输出列块融合进一个更宽的 handoff slot，scatter 宽度与 cube 内部 tile 宽度解耦。
- [显式向量索引转置替代微码转置原语](explicit_vector_gather_transpose.md)：放弃微码转置原语，改为常驻等差索引表（初值表+一次仿射修正）加每输出行一次字节粒度索引收集完成转置，行间零栅障，整块暂存缩为单张索引表。
- [尾部退化维阶段卸载到向量核并与相邻向量级融合（n≪分形宽的 GEMV）](gemv_tail_stage_aiv_offload_fusion.md)：把链上退化维矩阵级（N≪分形宽的 GEMV）整体卸载到上游向量级同一 pass，与下游点态融合后直接写出，删除该级与 workspace 往返及两对跨核标志。
- [HF32 操作数模式（尾数可精确表示时用半精度 MAC 速率跑 fp32 累加）](hf32_operand_mode_exact_mantissa.md)：把窄 dtype 实例化路径的 Cube 操作数模式切到 HF32：操作数全部来自 ≤11 位尾数 cast 时乘积与 fp32 累加序不变、L0C 逐位不变，MAC 走半精度档。
- [宽 dtype 操作数 hi/lo 分解 + 多项补偿 Mmad（用窄 dtype 速率替代 fp32 速率）](hi_lo_split_compensated_narrow_mmad.md)：把 fp32 操作数拆成 hi/lo 两个窄面板，每 K 块发 3 项 Mmad（hi·hi+hi·lo+lo·hi）累加进同一 fp32 L0C、K 序不变。
- [同核相邻 Tile 操作数驻留复用](intra_core_adjacent_tile_operand_residency.md)：让共享同一操作数面板的相邻输出 Tile 同核连续调度，面板在 L1 跨 Tile 驻留复用或成对计算两 Tile 共用一次装载，消除重复 GM→片上搬运。
- [增大归约维计算块以缩短串行依赖链](k_tile_dependency_chain_coarsening.md)：增大每次搬入片上并参与矩阵乘累加的连续归约维块，减少细粒度串行轮次
- [选最小访存计算比的矩阵乘基本块——单核分块复用](matmul_block_reuse_min_memory_compute_ratio.md)：增大二维基本块让驻留块被对侧维度复用，按「访存计算比最小」在片上容量约束下选块，减少操作数块从 GM 重复搬入。
- [多核铺核（宏块任务分区 + 设备侧分组边界解码 + 分区粒度自适应）](mn_multicore_partition.md)：把按整组分核改为宏块任务全局取模认领，分组边界表在设备侧流式解码，并按任务数自适应分区粒度。
- [转置折入搬运描述符（列组跨距装载 + 逐行跨距源散写）](mte_descriptor_transpose_scatter.md)：把向量管转置移入搬运引擎二维描述符：装载侧每列组一笔跨距搬运（源步距=行距−组宽），写出侧每输出行一笔跨距源散写，宽类型一次原地低位掩码折叠。
- [多行步距归约 Repeat 合批](multi_row_strided_reduce_repeat.md)：多行独立归约改用带 repeat 和行步距的归约指令一次描述整批行，每 repeat 对应一行、结果按固定目标步距落入独立槽，标量发射与屏障从按行缩为按行块。
- [原生 Cast 加索引 Gather 替代软件位重建](native_cast_indexed_deinterleave.md)：交错存储低精度系数的长串位运算手工重建改为硬件原生 Cast 整段转换，再用预生成偏移表和 Gather 按固定字节偏移解交错聚集到连续向量。
- [原生 dtype 面板直读（折叠 V0 cast 阶段与 fp32 环槽 GM 往返）](native_dtype_panel_direct_read.md)：删掉只做 cast/重排的 V0 阶段：C0 以 Nd2Nz 直读 GM padded 输入并改用原生 dtype 面板，环槽与 host 预 cast 一并消失，主路径 3→2 launch。
- [占用率驱动的分块与核数分档（人为核数上限与固定块高改为主机侧自适应）](occupancy_adaptive_tile_and_core_cap.md)：按派发占用率自适应块高 baseM'=Align16(clamp(ceil(M/核数),16,64)) 并重算派发，同时解除沿自上一代硬件的人为核数上限、同步上移守门阈值。
- [精度分层补偿 + D 段切分 + UB 驻留单次折叠（硬精度约束下的梯度归约提速）](precision_tiered_compensation_dseg_ubfold.md)：按输出逐个确认逐位一致约束的必要范围——仅 D 长归约输出用轻量补偿（b16×b16 积天然精确+每 chunk TwoSum+(hi,lo) 末次单舍入），其余输出 plain fp32 凭解析误差界（≥100 倍裕量）免补偿。
- [预取深度按片上缓存余量动态定尺（加深搬运与计算的重叠窗口）](prefetch_depth_adaptive.md)：把流式操作数预取队列深度从固定值改为按「片上缓存余量−常驻操作数−安全余量」÷单槽字节动态上浮。
- [生产者侧冗余工作提升与去重（消除按 (m,n) tile 放大的重复生产）](producer_redundant_work_hoist_and_dedup.md)：宿主把 round-robin 任务序换成每核连续 m-块核亲和映射，生产者条带级工作提出 n 循环、握手重定标到条带级；环槽写降为每 M-行块一次、消费者按绝对地址解析。
- [归约维流式操作数双缓冲软件流水（大块合并搬运为次要增强）](reduce_dim_doublebuffer_pipeline.md)：把非常驻操作数片上源缓冲加深到双缓冲，用预取序幕加稳态循环软件流水，使搬运与计算重叠。
- [逐行归约存树模式 + 定点事件同步（减全排空次数）](reduction_tree_fixedpoint.md)：把每块归约后全排空改为结果存片上不同偏移加循环外树形合并，块内跨流水依赖改用定点事件。
- [向量核串行 scan 链两阶段改造（屏障强度按 dtype 分裂降级 → 串行链改对数深度树扫描）](scan_chain_barrier_downgrade_and_log_tree_scan.md)：串行 scan 链两阶段改造：链内屏障按输出 dtype 降级（低精度 PIPE_V、高精度保留 PIPE_ALL）；串行链改对数树扫描，每波单屏障、ping/pong 双缓冲。
- [split-K 消费侧归并的全局行条带摊平（把归并工作从 tile 属主解绑）](split_k_consumer_global_striped_merge.md)：把 split-K 消费侧归并从 tile 属主解绑：每 tile 的 baseM 行切自适应条带、(tile,条带) 展平后跨全部 2×usedCores lane 派发，段升序累加。
- [链式原地计算的输出宿主槽轮转（消除段间整阵回拷）](staged_chain_output_slot_rotation.md)：把链式原地算法每段「写临时槽再整阵拷回权威槽」改为输出直写本逻辑流的下一个宿主槽，两条逻辑流在宿主槽对间轮转，消除段间回拷。
- [行块级带源步距批量写](strided_row_block_batched_store.md)：把向量尾段逐行小额 GM 写合并为行块级每数组一笔带源步距批量写，按行数等比例收缩 MTE3 事务数与逐行标量发射。
- [转置段批量化与屏障对合并（按通道分形批 / 跨 fi 融合）](transpose_stage_batched_barrier_collapse.md)：把转置段逐分形的「读+双全屏障+转置+写」按通道分形批（B=4~16）或跨 fi 融合（F≈32~40）合并，批边界落在同一 batch 元素内。
- [向量核收尾段批量化（整块读写 + 整块类型转换 + 屏障塌缩 + 系数向量广播）](vec_epilogue_batched.md)：把向量核收尾段逐行循环改为按行块批量：整块读写、整块类型转换、屏障塌缩、系数向量二维广播。
- [整面板搬运与片上索引转置（逐列发射链坍缩 + 三引擎双槽流水）](whole_panel_dma_onchip_transpose.md)：把每 tile 逐列装载+逐行写坍缩为整面板通路：一笔行面板二维装载→片上每输出行索引收集转置→一笔二维面板写+尾部二维零写，双槽轮转三引擎重叠。
- [归约循环操作数整 Tile 批量装载](whole_tile_batched_operand_load.md)：把归约循环中操作数按行带碎片的多笔 GM→片上变换合并为单笔整 Tile 变换、行带×分形双重循环装载合并为单笔显式两维步距网格装载。
- [宽粒度索引收集与纯移位抽道](wide_gather_byte_lane_extract.md)：把字节粒度逐行收集提升四倍访问宽度：源按四字节视图重释，每四个连续输出行组一次宽粒度收集，四字节道用移位零扩展+截断窄化抽出，非整除尾部与宽类型回退。
