# 950 FlashAttention 类算子策略

> 平台 ID 为 950；正文中的 A5 为产品代际别名。

- [FA 类算子性能优化通用策略](fa_perf_optimization_strategy.md)：适用范围：昇腾平台上 Attention 族融合算子（含标准/因果/稀疏/分页/变长等变体）的 kernel 与 tiling 优化。

- [随机稀疏索引下的"合批"（M 维合并 / 多头合并）](antipattern_batching_under_random_sparse_indices.md)：反模式：随机稀疏索引下把多个 query 位置合批共享 gather 填满 M 维（G=4 补 16 仅 25%），并集膨胀算力浪费 47%~81% 净负。
- [搬运描述符外提与同步位置微调（两类"看似免费"的微优化）](antipattern_descriptor_hoisting_and_sync_nudging.md)：反模式：DataCopy 参数结构体外提循环外复用（+21.2%）、WaitFlag 后挪填气泡（+67% 长尾），两类微优化均证伪。
- [用"单缓冲驻留"换取搬运请求数（牺牲双缓冲）](antipattern_single_buffer_residency_vs_double_buffering.md)：反模式：把分片多次 GM→L1 装载改成单缓冲 TBuf 整块常驻省请求数，实测两可信刻度均 0 收益（−0.04%），勿做。
- [QKV 两级分块 L1 复用在 ring 流水模板上三连回退](antipattern_two_level_tiling.md)：反模式：放大 mBase 做 Q 微块共享 K/V 两级 L1 复用，ring 流水模板三连回退 0.904/0.856/0.999x 证伪。
- [causal 整块全掩码跳过（块级稀疏计算删除）](causal_block_skip.md)：用整数边界判定并跳过causal下整块全掩的s2块，删除对应块级计算。
- [因果掩码 visEnd 归约块裁剪 + 块内列宽自适应](causal_visend_reduce_tile_pruning.md)：为每个Q块计算保守联合可见终点visEnd，停止为整块不可见的s2后缀生成任务。
- [分块粒度按"每核任务数是否留有流水稳态余量"自适应](chunk_granularity_adaptive_to_pipeline_steady_state.md)：在减少块数的同时，以 totalWork 和每核任务数约束 chunk 粒度，避免无脑增大。
- [并发阶段共用片上 buffer 的隐蔽竞争（识别、诊断与修复）](concurrent_stage_shared_buffer_race.md)：识别、诊断并修复并发阶段共用片上buffer造成的隐蔽竞争。
- [11 - CV 通路迁移：BufferManager 模式（arch35 对齐）](cv_path_migration_buffer_manager.md)：以BufferManager模式迁移CV通路，打通AIC↔AIV的UB→L1直通。
- [decode 分 KV 任务轴重组（S<=16 场景）](decode_splitkv_task_axis.md)：将decode任务按KV块重组为B×N_kv×headBlocks×s2OuterBlocks，并在线性任务轴上均分到核
- [decode 分支 wsS fp32 高精度回退（双量化误差陷阱）](decode_wss_fp32_precision.md)：将 decode 的 S<=16 分支中 wsS staging 从 2B 量化表示回退为 fp32。
- [dual-AIV 子核行分担与 Cube M 轴 group 满载的自包含融合落地（无前置结构依赖版）](dual_aiv_msplit_fused_cube_m_group_packing.md)：由单AIV工作改为dual-AIV子核分担；按B·N_kv组织任务，将G打包到Cube M轴并按BLOCK_M切块
- [GQA/950 已证伪方向（勿重复投入）](falsified_directions.md)：收录 2026-08 多会话中**完整跑通评测但性能回退**的策略——每条都有实测锚点，用于防止 K-Search 与人工优化重复踩坑；回退定义为子集均值劣于当轮基准且超噪声（>2%）。
- [MM1 Fixpipe 随路量化 2B staging（wsS fp32→2B）](fixpipe_quantpre_2b_staging.md)：按 QType 启用 Fixpipe quantPre，将 L0C FP32 随路量化后以 GM 2B 落盘。
- [索引驱动散读的 N 路展开 + 索引预取（打散"标量装载→搬运发射"依赖链）](indexed_gather_unroll_index_prefetch.md)：将索引散读循环N路展开：主循环先批量预取索引，再连续发射搬运；尾部逐行处理。
- [输入队列加深一级的 GM 搬入/向量计算重叠](input_queue_deep_double_buffer.md)：将输入队列深度由 2 增至 3，或对半拆分片上缓冲并增加一级深度。
- [索引驱动散读的循环不变量地址计算外提](loop_invariant_address_hoisting.md)：将addr(idx)拆为base+idx×stride，把不依赖idx的base和stride移到循环外只计算一次
- [单调可见边界下沉到 L1→L0 搬载级裁剪](monotonic_visibility_l1_l0_load_skip.md)：将单调可见边界判定下沉至L1→L0搬载，跳过完全不可见微块的装载。
- [内层 tile 的 MTE2 预发 + 游标轮转 depth-2 右操作数槽（PRELAUNCH gap=1）](mte2_prelaunch_cursor_rotated_double_slots.md)：将右操作数即时单槽搬运改为MTE2预发，并以slot[2]和游标轮换双槽。
- [未跑通的高价值方向（冲 score 1.10 的剩余弹药）](pending_opportunities.md)：状态：世界模型已排队但因会话中断（LLM 代理故障/轮次耗尽）未落地评测的方向；每条附预期收益模型与实施要点，按性价比排序。
- [prefill GM 中转最小化（P/O 中转字节削减，两轮迭代）](prefill_relay_min.md)：保留 GM 五分区中转架构，按有效行列缩减 MM1→Vec1→MM2→Vec2 的 GM 往返字节。
- [方法论策略：发射受限 vs 带宽受限的判定探针（改搬运量、不改发射数）](probe_issue_bound_vs_bandwidth_bound.md)：用搬运量减半而发射数不变的探针判定发射受限与带宽受限。
- [逐元素标量构造 → 整数域纯算术向量化（掩码/惩罚向量生成）](scalar_elementwise_to_integer_domain_vectorization.md)：将逐元素标量条件写入改写为整数指示量驱动的纯算术向量表达式。
- [短序列分块参数网格重调（MTP / S∈\[2,16\] 场景）](shortseq_tiling_grid_retune.md)：将固定分档函数替换为按S档、S_kv档和任务量档索引的参数表。
- [slot 环形分级软流水（MM1/Vec1/MM2/Vec2 交错重叠）](staged_ring_pipeline.md)：将 3 个环形 workspace 槽改为分级软流水，使相邻槽分别处于 MM1、Vec1/MM2、Vec2
- [FA-950 模板族能力清单（K-Search no_op 排查表）](template_capability_checklist.md)：在 FA-A5 模板族（MHA/GQA 同源三段中转 ring 流水）算子上跑 flash_attention_strategies catalog 前，先对照本表剔除「模板已实现」的策略，避免 no_op 轮次浪费。
- [UB→L1 直通（消除 CV 通信的 GM 中转往返）](ub_to_l1_direct_cv_communication.md)：将Vector侧中间数据由UB经GM中转到L1，改为UB→L1直通，消除GM往返。
