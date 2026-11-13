# Ascend C 开发指南

- [Ascend C多层级编程接口选择参考](asc_how_to_choose_api.md)：欢迎使用 Ascend C 进行昇腾AI处理器算子开发。Ascend C不仅致力于开放芯片完备编程能力支撑实现极致性能，同时通过多层级编程API设计，让您能够根据项目需求、团队技能与性能目标，灵活选择最合适的API，在开发效率与运行性能之间取得最佳平衡。
- [cross gen migration guide](cross_gen_migration_guide/index.md)：Ascend C的核心设计目标之一是实现跨代兼容。然而，每一代芯片在微架构上都存在独特的硬件特性，因此无法保证所有接口仅通过重编译就能达成完全的跨代兼容。基于这一前提，本手册旨在为Ascend C算子开发者提供系统化指导，帮助将算子Kernel代码从当前芯片平滑移植到目标代际芯片上运行，实现高效、可控的迁移。（共 18 张知识卡：A3→A5 移植先看驻留量，不是先看算法、arch22 → arch35 AscendC Migration and Backward-Generation Reference、Ascend C API兼容性策略 等）
- [getting started](getting_started/index.md)：共 7 张知识卡（如 Ascend C概述、环境准备 等）。
- [msprof Agent 使用指南](msprof_agent_guide.md)：让 Agent 用 msprof 做性能分析而不撑爆 context 的指南：先用系统级 msprof 定位瓶颈，落到单算子再用算子级 msopprof（等同 msprof op）展开；核心是分层读取——优先只读 op_statistic 聚合 csv，再按需 grep op_summary 取关键指标，避免读二进制 trace。
- [operator practice](operator_practice/index.md)：共 133 张知识卡（如 本文档组织结构（算子实践）、异构计算（算子实践）、Host Tiling 单元测试开发 等）。
- [精度验证](precision/index.md)：共 44 张知识卡（如 aclnn 接口调用指南、激活参考实现的权重状态、边界与稳定公式、APACE 编码 golden 与容差边界 等）。
- [programming guide](programming_guide/index.md)：共 125 张知识卡（如 本文档组织结构（编程指南） 等）。
- [快速开始](quick_start.md)：根据本地是否有NPU设备和使用目标选择对应的环境准备方式：
- [AscendC SIMD Development Reference](simd_development_reference.md)：AscendC SIMD 开发参考，主张 arch35/A5 上多算子计算链默认走 Reg 类 API（Regbase）而非 Membase LocalTensor（后者每步 UB 往返加 PipeBarrier，实测拖累可达数十倍）；另含量化 kernel 常用 SIMD API 与 MXFP4 范式。
- [technical appendix](technical_appendix/index.md)：共 8 张知识卡，分布在 2 个子目录（concepts_and_terms、cpp_standard_support）。

- [regbase](regbase/index.md)：共 34 张知识卡（如 RegBase API 的操作数、掩码与存储合同、AscArange：固定 reference 调用约束、asc_bfloat162e1m2x2 (废弃)：固定 reference 调用约束 等）。

- [blaze](blaze/index.md)：共 21 张知识卡（如 Blaze 硬件基形与运行期尾块范围的区别、权重反量化的 Cast 顺序与 V→C 释放关系、Blaze 逐元素 Epilogue 的广播映射与加载边界 等）。
- [catlass](catlass/index.md)：共 17 张知识卡（如 CATLASS FA 接口映射及参考配方冲突、CATLASS 编译架构与启动资源合同、CATLASS 的 Tile、Block 与 Kernel 组件契约 等）。
- [diagnostics](diagnostics/index.md)：共 25 张知识卡（如 assert（AI CPU API）：固定 reference 调用约束、printf（AI CPU API）：固定 reference 调用约束、Printf：固定 reference 调用约束 等）。
- [memory](memory/index.md)：共 25 张知识卡（如 对齐单位、布局行距与填充值、BF16 别名缓冲与平台采样路径、Ascend C 缓冲所有权、流水交接与槽位布局 等）。
- [moe](moe/index.md)：共 19 张知识卡（如 MoE Dispatch 与 Combine 的元数据对应关系、MoE 容量公式与路由假设、MoE Combine 的可选路径与量化角色 等）。
- [reductions](reductions/index.md)：共 34 张知识卡（如 归约算法选择与数值边界、归约轴映射与全载、分载设计、Blaze Pure Reduce 的 partial 状态与模板缺口 等）。
- [vector](vector/index.md)：共 19 张知识卡（如 Ascend C API 家族与存储位置决定的搬运、原子 GM 回写与事件边界契约（SetAtomicAdd/DisableDmaAtomic）、字节 Mask、Bit Mask 与数值谓词 等）。

- [layouts](layouts/index.md)：共 34 张知识卡（如 广播 Mask 极性、步长与暂存复用、重排路线启发式与连续搬运证据、Gather 尾轴模式与有符号索引规范化 等）。
- [shmem](shmem/index.md)：共 31 张知识卡（如 Blaze Heavy Kernel 覆盖与性能条件、Blaze-SHMEM Host Bootstrap 生命周期与失败传播、Blaze 本地 MX 模板的 L1 尺度窗口与事件 等）。
- [synchronization](synchronization/index.md)：共 22 张知识卡（如 向量递推中的真实依赖与别名冲突、APACE ReduceScatter 时序与通知计数、原子模式切换与首次覆盖顺序 等）。
- [torch extensions](torch_extensions/index.md)：共 9 张知识卡（如 PyTorch 自定义 ACLNN 算子的四层接口契约、ACLNN 扩展辅助层的符号解析与异步资源生命周期、PyTorch Ascend C 扩展的编译单元与启动 ABI 等）。

- [communications](communications/index.md)：共 29 张知识卡（如 APACE AllGather 预触发与 scale 等待边界、APACE AllGather 三区与输出归属、APACE AllToAll Matmul 的全局与局部坐标 等）。
- [matmul](matmul/index.md)：共 21 张知识卡（如 异步 Matmul 的结果空间与完成等待、Matmul 基本块流量模型与输出对齐、Batch/Group Matmul 分区身份与分支顺序 等）。
- [sorting](sorting/index.md)：共 9 张知识卡（如 排序聚合同索引更新的排列与所有权、硬件排序的行边界、索引与 Padding、多核排序的分层归并与工作区交接 等）。

- [simt](simt/index.md)：共 10 张知识卡（如 SIMT API 迁移的签名、lane 与版本边界、SIMT 调试上下文与缓存可见性、SIMT 调试输出的资源与执行影响 等）。

- [tiling](tiling/index.md)：共 39 张知识卡（如 自适应算法的退化域与 Fallback、自适应容量分块与多行缓冲预算、自适应分块搜索、可行性与安全容量 等）。

- [environments](environments/index.md)：共 17 张知识卡（如 API 示例清单与真实编译合同、Ascend C API 家族与文档版本的兼容边界、Blaze 设备地址空间与 VF 循环约束 等）。

- [registration](registration/index.md)：共 23 张知识卡（如 Add 注册模板的跨层 shape 与 dtype 合同、算子文档模板中的接口事实与占位值边界、DAG 输出与 Foreach Tensor 区间合同 等）。

- [attention](attention/index.md)：共 58 张知识卡（如 Attention 在线输出归一化与最终除法必须一致、反向 Cube 融合需保留全部梯度路径、因果窗口、GQA 与整块跳过的证明 等）。
- [performance](performance/index.md)：共 40 张知识卡（如 APACE Host 参数接线与实际计时、APACE 调优假设与负收益的适用范围、asys 系统采样的参数范围与 msprof 下发身份 等）。

- [pooling](pooling/index.md)：共 8 张知识卡（如 池化地址对齐守卫与算术反例、池化反向的梯度贡献与 gather/scatter 归属、深度池化 Direct Buffer 路径与同步修订 等）。

- [data movement](data_movement/index.md)：共 8 张知识卡（如 批量搬运、LoopMode 与交错 Scale 偏移、DataCopyPad 多行搬运的有效长度、padding 与物理行距、DataCopyPad 的版本、重载与尾部真实范围 等）。

- [testing](testing/index.md)：共 32 张知识卡（如 APACE 多rank启动与 context 复用范围、APACE 对标路径与失败证据边界、算子测试的行为断点与属性交叉覆盖 等）。

- [compilation](compilation/index.md)：共 2 张知识卡（如 APACE 构建根目录与版本化符号、Softmax 模板ABI与独立头文件依赖）。

- [GM 布局已内联零填充的操作数用整块紧凑拷贝载入，根除 DataCopyPad 跨步读 AlignUp 行距错位](gm_datacopypad_alignup.md)：（A3 侧行距公式一致为推断，未实测）A3→A5 port of chunked/padded-layout operands: when the GM operand already carries its zero padding inline, load the full padded region as ONE contiguous block copy (strides all 0) instead of a strided multi-block DataCopyPad whose UB row pitch (AlignUp(blockLen,32)+dstStride*32) silently mismatches the kernel's row-index constant whenever blockLen is not 32B-aligned. Verified on 14_ChunkScaledDotKktFwd (950DT, CANN 9.2.0) 50/50 PASS_T1.
- [共享 NPU 上跨 run 性能 A/B 必须以候选侧绝对时间 cand_us 为判据（ratio 差 <5% 被噪声主导）](npu_run_a_b_cand_us_ratio_5.md)：reference 侧小用例 ref_us 分钟级摆动 40-50%；跨 run ratio A/B ~5% 以下为噪声；回归排查重测两侧、不做跨 session 纯 ratio 比较
- [PipeBarrier 删减实测边界：同管道 V barrier 删除安全但饱和管道无收益；MTE3 逐 store barrier 被 SetFlag<MTE3_V> 覆盖](pipebarrier_v_barrier_mte3_store_barrier_setflag_mte3_v.md)：4-14 实测：266 个 V→V barrier 删除逐位不变但 perf≈0（吞吐饱和非杠杆）；逐 store MTE3 barrier 冗余可删；删除前先判延迟停滞 vs 吞吐饱和
- [wrapper 数据搬移是端到端 perf 合同的一等优化目标（at::empty 替代 at::zeros + Tp==T 跳过 pad-copy）](wrapper_perf_at_empty_at_zeros_tp_t_pad_copy.md)：wrapper-inclusive 计时下 host 布局变换占落后用例 19-44%；两项零风险消除 +11% 平均 ratio，50/50 逐位不变；含 at::empty 合同 falsifier
- [knowledge-query 报 ValueError『card set changed after index build』= 派生索引陈旧：build+verify 分钟级原地重建即可，语料没坏；verify 门全拒是设计不是故障](knowledge_index_stale_valueerror_rebuild_first_not_bypass.md)：knowledge-query 每次查询（正控负控同错）返回 ValueError『knowledge card set changed after index build; rebuild the index』或『cannot prove its corpus tip』时，坏的是 gitignored 派生索引（artifacts/indexes/knowledge.sqlite3），不是语料：pull/切分支/合新卡/搬迁 local root 后索引 meta（commit、卡数、卡哈希）与磁盘不再一致，verify 门（retrieval/index.py）按设计 typed-stop 全拒，宁可零投递也不静默给陈旧答案。修复是对自有克隆或本地库原地跑 knowledge_index.py build + verify（验收 meta.repository_state.commit==HEAD、provenance 合法、card_count 与该 tip 应有数一致；非 git 的 local-kb 用同一工具，no_git_directory 是合法状态），不得绕过门、从已知陈旧索引降级消费，也不需要重新克隆——重建不动卡片字节，本地卡住在语料克隆之外，天然免疫。
- [Debug markers must not SetFlag a shared functional event at pending==1 (depth-2 excursion = the wedge class being diagnosed)](debug_markers_must_not_setflag_a_shared_functional_event_at_pending_1_depth_2_excursion_the_wedge_class_being_diagnosed.md)：Progress markers SetFlag+WaitFlag on a functional event id whose pending is 1 at entry drive the counter 1->2 — same overflow class as the wedge under diagnosis; stripping markers changed a deterministic wedge to pass. Use a dedicated event id or assert pending==0; strip after localization. Found on 11_BigBirdAttention CubeMark_ eFixM_.
- [fp32 (b32) ifTranspose=true L1->L0B LoadData silently wrong on arch35 — V-pre-transpose sidestep (PB-43 instance #2)](fp32_b32_iftranspose_true_l1_l0b_loaddata_silently_wrong_on_arch35_v_pre_transpose_sidestep_pb_43_instance_2.md)：fp32 b32 transpose-fractal L0B load miscomputes on arch35 while ifTranspose=false fp32 loads are bit-exact; kStep-units variants falsified. Mitigation: host pre-transposes V; kernel stages [D,BLOCK_N] and uses the proven ifTranspose=false K-form. Verified bit-exact on 11_BigBirdAttention fp32 case.
- [Intra-core event credits consumed per call SITE — work-loop boundary double-consume self-deadlocks](intra_core_event_credits_consumed_per_call_site_work_loop_boundary_double_consume_self_deadlocks.md)：One credit across an item boundary + two wait call sites (item-head + first-tile) = first tile of item 1 waits on empty counter (matching Set later in same thread) -> deterministic 507014. Fix: reset the any-issued flag after the item-head wait. Count Sets vs Waits across the loop boundary. Found on 11_BigBirdAttention eMte1Mte2_.
- [Per-core GM workspace slab stride is a three-party contract (producer/consumer/pybind) — grep-audit cid-indexed expressions](per_core_gm_workspace_slab_stride_is_a_three_party_contract_producer_consumer_pybind_grep_audit_cid_indexed_expressions.md)：Slab stride mismatch between producer class, consumer class and allocator is invisible to single-core numeric probes and multi-core marker probes (cid=0 coincides; markers are addressing-blind). Grep-audit every cid* expression; one multi-core probe must check numerics. Found on 11_BigBirdAttention ws2 (+4096 vs +2048).
- [Unbounded-pending cross-core flag channel overflows mode-4 line counter — drain-credit ring bound (MIX deadlock)](unbounded_pending_cross_core_flag_channel_overflows_mode_4_line_counter_drain_credit_ring_bound_mix_deadlock.md)：arch35 MIX looped-handshake kernels: any CrossCoreSetFlag channel whose producer can run unboundedly ahead overflows the mode-4 line counter under GM contention -> non-deterministic 507014. Audit every channel's run-ahead; add drain-credit ring (ConsumerReleaseMte2 form). Verified on 11_BigBirdAttention (c12 4/4-wedge -> 8/8 clean @28 cores, 50/50 PASS).

- [Chunk GLA 输出：分别保留块内权重、状态缩放与尾块掩码](chunk_gla_output_scale_mask_and_native_input_boundary.md)：从原 Torch 输出公式提炼 Ascend C 分块实现边界：A 已含 scale，状态项用自然 exp，保留 chunk32/64、因果及尾块列掩码。
- [最近邻 Resize：先固定坐标规则，再按原 dtype 搬移数值](nearest_resize_native_value_gather_and_coordinate_contract.md)：将最近邻坐标选择与数值搬移分开；区分 nearest、nearest-exact 和原任务分支，用同输入 CPU 索引真值检验 Ascend C 实现。
- [要把归档的精度判定用在今天的候选上之前先问两件：判据字节还在吗？那次实际映射的是哪个库？](user_local_archived_verdict_declares_its_criterion_without_preserving_it.md)：触发物=你打算复用一份归档 precision_report 的判定。两条必查：(1) bindings 里 comparator/profile/reference_worker 的 sha 只是【声明】——实测 2_GroupedMatmul 归档 5 份报告都声明同一组三件，而对该目录全部 84 个文件逐件 content-hash 后三件一个都不在 ⇒ 判定不可复算、精度只能记 UNBOUND_NOT_JUDGED；按 sha 去 hash，不要按文件名去 ls。(2) runtime_evidence.mapped_libraries[].sha256 是那次【实际映射】的库——归档 PASS 映射的是 25b2bead，而当前候选 DSO 是 f4565a84 ⇒ 不同构建，不能借那次 PASS；这比报告的candidate_digest 更直接，两者是不同的量。判据模块丢了但【查了什么】仍在逐例 metrics 里（eco-open-source / required_matched_ratio 0.9 / atol 1e-3 / rtol 1.220703125e-4 / max_abs_error_limit 0.01 / 四项 checks）⇒ 不要猜判据；且 eco 与 6e5 不能互换。拿到三件＋公共签名只关闭判据接线，当前候选的 P 仍须在原判据下实测。边界：extension_access 里的 cpython-312-x86_64 是【路径名】，不证明被映射库的 ELF 架构，没读 ELF 头不得断言。多次运行归档（harness2..6，passed 44/45/49/48/50，candidate_digest 互不相同，hardware_verified 仅末次 true，而 first_attempt_is_verdict 五份都有）⇒ 哪一次是行判定从字节判不出来，标未决交 schema 所有者。附带：wrapper 可能故意跳过 *.cpython-*.so（whl 打包的空 pybind 壳，注册不了算子），只加载无 tag 的 fat 库 ⇒ 目录里有 .so 不等于算子已注册。
- [要报一个【从选中子集测出来】的逐例数之前先问：参考/候选的 forward 往 self 回写吗？——回写即令每例结果成为分片组成的函数](user_local_reference_forward_persists_state_across_selected_cases.md)：触发物=你只测了 50 例里的一部分，而消费者是『全部用例各生成一次 + 每臂各构造一次 + 只迭代被选中例』。此时若 forward 里有 self.x = f(self.x, 本例形状) 这种单调回写，第 N 例的计算就取决于它前面跑过哪些例，换个选择集或换个顺序，同一例测的不是同一件事。实测：16_LongformerAttention(catalog24) 的 model.py 与 model_new_ascendc.py 都把 window=min(window,S)、global=[min(i,S-1)] 回写进 self；原全 50 升序里 case0(S=256) 第一下就把 global 钉成 [0,255] 并对其余 49 例生效，而只选 {2,...} 的新跑在 case2(S=512) 得 [0,511]、到 case4(S=384) 变 [0,383]，46/47 例与原序不同。判别控制=未整备 S=512 给 [0,511]、恢复后给 [0,255] 且两者不同（只报『恢复后是 [0,255]』会假过，因为 S=256 的例两边都给 [0,255]）。修法优先级：先问恢复态是不是不动点，而不是先想『加一例整备』——(32,[0,255]) 对全部 50 例满足 min(255,S-1)=255 且 min(32,S)=32（实测 min seq_len=256），所以它是不动点，分片怎么切/什么顺序都不再改变 mask 状态；整备能到同一状态但要多花一例时间，且『片内第一例是小 S』这种性质在下次重切分片时会静默失效。作用域：不动点只覆盖那两个属性，不证明输出/W_o 缓存/分配器/计时与顺序无关。两臂都镜像了同一状态机（候选注释自述『镜像参考的 mask 状态机』）⇒ 臂间可比性不受影响，已录数字不因此作废；污染改的是『算了什么』，不是『两臂能不能比』。
