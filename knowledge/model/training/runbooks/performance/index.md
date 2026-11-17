# 模型训练性能优化

- [torch._foreach_copy_ 的 fast/slow path 判别与 host 派发收益边界](foreach_copy_fast_slow_path_dispatch.md)：ATen/CUDA foreach copy 的形状限制是 self[i]/src[i] 逐对匹配，不要求列表内所有参数同形；异形 FSDP 参数本身不能判定 slow path。CPU/device offload 因设备不同不满足所读 CUDA fast path 的同设备条件；已进入 slow path 时才有逐对 copy_ 调用，实际 host 收益和 DMA 数需运行测量。

- [DeepEP offload 反向重计算中 dispatch 反量化前大空泡的定位](deepep_dispatch_antimxquant_h2d_wait.md)：kimi k3 训练（k3-shared-w13 代码路径）开启 DeepEP offload + FP8 后反向重计算时间线空泡的离线 profiling 定位，服务 MoE 训练性能优化。
- [flashkda replay 路径修复——npu_kda 复用缓存边界 + TND cu_seqlens（不走 BSND wrapper、不重做 nonzero）](flashkda_replay_nonzero_cu_seqlens_reuse.md)：torchtitan-npu 上 kimi_k3 模型训练开启 FlashKDA offload 后 replay 路径的修复：KDAKernel 直接复用 InnerKDA 已算好的 _query_start_loc 缓存并把 q/k/v/gate/beta 展平成 TND、直接传 cu_seqlens，不再走 BSND wrapper（不调用 _npu_kda_packed_boundaries、不重做 nonzero）。
- [训练图 prefetch balance——被 lease/预算推迟的恢复单元不得吞掉队头空隙（deferred + later_candidate 守卫）](tge_prefetch_deferred_head_later_candidate.md)：TGE 训练图估计器为 Kimi 用例排布 FSDP 参数恢复（allgather）与计算通信掩盖，本修复解决被推迟恢复单元吞掉队头空隙的调度饿死问题。
- [tyro 1.0.15 bool 否置语法判别与关闭 SwapOptimizer 的合法 CLI 写法](tyro_bool_negation_disable_swap_optimizer.md)：torchtitan-npu 训练关闭 SwapOptimizer 的调优动作中的 tyro CLI 否置语法判别：tyro 1.0.15 下 --optimizer.swap-optimizer=true/=false、--optimizer.swap-optimizer false、--no-optimizer.swap-optimizer 均被拒，唯一合法写法是 --optimizer.no-swap-optimizer。
- [W13 profiling 区间差分与 Add 归属：先绑定反向调用链再解释收益](w13_operator_gain_not_realized_end_to_end.md)：W13离线profiling中等待总和与标记区间elapsed都减少，但后续host/device关联把指定Add定位到反向MatmulBackward0/aten::add_。保留原区间统计，撤回前向共享专家合并及等待移出窗口的确定归因。

- [cu_seqlens 隐式 D2H：按 copy_ 的维度、dtype 与调用链分组](cu_seqlens_implicit_d2h_hostbound_attribution.md)：区分 metadata DeviceCopy 与 allfallback 标量提取；原汇总表单位矛盾，暂不采用其绝对耗时和占比。
- [DataLoader 消费等待：按结束时间与 duration 重建 fetch/compute 区间](dataloader_cross_step_overlap_failure_proof.md)：修正 fetch_all 与 compute_phase 时间线，保留实际阻塞观测；队列、feeder、FD 或 worker 瓶颈仍需分支探针，不能由 out=8 直接定论。
- [DSV4 CP 块对齐切分：区分边界几何与索引探针的前提](dsv4_cp_block_aligned_split_scheme_a.md)：文档内按块边界切分只证明几何条件；另造的非对齐段不满足索引探针前提，不据其结果裁定真实 aligned shard 的成败。
- [DSV4 host 元数据缓存：用生成代码核对 compiled region 的标量回读](dsv4_item_d2h_sync_host_replica_pattern.md)：在 eager 元数据构建处缓存 host 标量，并检查生成代码中的 _local_scalar_dense；记录中单卡结果无可测收益，不外推多卡加速。
- [CCU 性能回退的静态排查：区分直接改动与共享资源候选](hcomm_ccu_channel_side_attribution.md)：记录 channel 路径 diff 与共享映射声明，保留对照/采样方法；内存分配次数、锁争用和具体性能根因没有实测闭环。
- [增量式梯度范数穿刺：单次 backward 的 dtype、归约与验收边界](incremental_clip_grad_norm_fsdp2_hook.md)：对齐最终穿刺脚本的 float64 本地平方和与 fp32 HCCL 归约；仅保留单卡、单次 backward 的对拍结果，不宣称支持梯度累积或训练步加速。
- [MoE dispatch 删除 CalCumSum 的负结果：通信状态依赖不能按函数名省略](moe_dispatch_nocumsum_ablation_deadlock.md)：在指定 950 多卡路径跳过 CalCumSum 后出现缺 rank、带宽异常和设备错误；只保留该版本负结果，不把未量出的同步链条写成最终根因。
- [小张量 RepeatInterleave 回退：分开训练内观测与隔离微基准](repeat_interleave_small_tensor_fixed_overhead.md)：记录 metadata tensorize 路径中的 RepeatInterleave 观测；隔离 CPU/NPU/searchsorted 数字只解释各自用例，没有可信基线统计时不作调用次数增幅比较。
