# 模型训练性能优化

- [torch._foreach_copy_ 的 fast/slow path 判别与 host 派发收益边界](foreach_copy_fast_slow_path_dispatch.md)：ATen/CUDA foreach copy 的形状限制是 self[i]/src[i] 逐对匹配，不要求列表内所有参数同形；异形 FSDP 参数本身不能判定 slow path。CPU/device offload 因设备不同不满足所读 CUDA fast path 的同设备条件；已进入 slow path 时才有逐对 copy_ 调用，实际 host 收益和 DMA 数需运行测量。

- [DeepEP offload 反向重计算中 dispatch 反量化前大空泡的定位](deepep_dispatch_antimxquant_h2d_wait.md)：kimi k3 训练（k3-shared-w13 代码路径）开启 DeepEP offload + FP8 后反向重计算时间线空泡的离线 profiling 定位，服务 MoE 训练性能优化。
- [flashkda replay 路径修复——npu_kda 复用缓存边界 + TND cu_seqlens（不走 BSND wrapper、不重做 nonzero）](flashkda_replay_nonzero_cu_seqlens_reuse.md)：torchtitan-npu 上 kimi_k3 模型训练开启 FlashKDA offload 后 replay 路径的修复：KDAKernel 直接复用 InnerKDA 已算好的 _query_start_loc 缓存并把 q/k/v/gate/beta 展平成 TND、直接传 cu_seqlens，不再走 BSND wrapper（不调用 _npu_kda_packed_boundaries、不重做 nonzero）。
- [训练图 prefetch balance——被 lease/预算推迟的恢复单元不得吞掉队头空隙（deferred + later_candidate 守卫）](tge_prefetch_deferred_head_later_candidate.md)：TGE 训练图估计器为 Kimi 用例排布 FSDP 参数恢复（allgather）与计算通信掩盖，本修复解决被推迟恢复单元吞掉队头空隙的调度饿死问题。
- [tyro 1.0.15 bool 否置语法判别与关闭 SwapOptimizer 的合法 CLI 写法](tyro_bool_negation_disable_swap_optimizer.md)：torchtitan-npu 训练关闭 SwapOptimizer 的调优动作中的 tyro CLI 否置语法判别：tyro 1.0.15 下 --optimizer.swap-optimizer=true/=false、--optimizer.swap-optimizer false、--no-optimizer.swap-optimizer 均被拒，唯一合法写法是 --optimizer.no-swap-optimizer。
- [W13 profiling 区间差分与 Add 归属：先绑定反向调用链再解释收益](w13_operator_gain_not_realized_end_to_end.md)：W13离线profiling中等待总和与标记区间elapsed都减少，但后续host/device关联把指定Add定位到反向MatmulBackward0/aten::add_。保留原区间统计，撤回前向共享专家合并及等待移出窗口的确定归因。
