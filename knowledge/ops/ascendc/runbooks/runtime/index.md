# runtime

- [fp16 aUbFactor 被 cacheBuf 钳制，路由随 B 翻转](aub_factor_cachebuf_clamp_flips_base_group_route.md)：A 向单 chunk 因子 aUbFactor 不是 (dtype,H) 的函数：大 B 下经 cacheBuf 16KB 预算钳制 fp16 128→64，aLoopCntTotal 翻倍并翻转 base/group 路由；复算路由必须带实际 B 走完整钳制环。
- [空batch归约kernel：bias零填充+全核早退配方](empty_branch_kernel_empty_a_early_exit_empty_r_zero_fill.md)：reduction 算子 B==0 且 has_bias 时两路 bias 输出需零填充 6H 的完整 AscendC kernel 配方：Duplicate(0) 常量驻留 + 6 段 strided DataCopyPad + V_MTE3 单 crossing 同步；H==0 或 B==0 且无 bias 时全核早退。
- [空张量分类 H==0 必须先于 B==0 判定](empty_tiling_classify_h_zero_before_b_zero_div0.md)：双零输入若先判 B==0×isBias 会退化成 aTotal=0 的 EMPTY_R，(d) 约束把 aUbFactor 钳到 0 后 CeilDiv(0,0) 除零；H==0 先判则安全落 EMPTY_A 全核早退。
- [group 2D 分核：对齐 aLoop 与 SetScheduleMode](group_2d_core_split_numblocks_align_schedule_mode.md)：A×R 2D 分核 host tiling——totalOuter 均分后 numBlocks 对齐 aLoopCntTotal（放不下则 FloorAlign）、rGroupCnt 整除保证 2D 网格整齐；SetScheduleMode(1) 供跨核 SyncAll；bias 归约 workspace=rGroupCnt×6×H×4。
- [GRU workspace 五平面布局：平面 4 为 hn+隐藏偏置](gru_workspace_five_plane_layout.md)：PyTorch v2.7.1 RNN.cu 一手核验：融合 GRU 前向把 5 个中间平面按行内 5H 写入 workspace（rg/ig/ng/hx/hn+b2n），平面 4 是加过隐藏偏置的 hidden 门预激活——反向 grg 链消费它而非 ng，实现 storage 语义时照此契约。
- [kernel 侧打印定位崩溃：AscendC::PRINTF 宏](kernel_printf_ascendc_macro_ascendc_dump_bisect.md)：NPU kernel 无源码级调试器，用 AscendC::PRINTF 宏（大写、命名空间限定、无需单独 include）埋点 + ASCENDC_DUMP=1 运行输出；配逐段禁用二分定位异步队列故障。
- [TilingFunc 骨架：校验→空→组→基与收尾三件套](multi_branch_tilingfunc_skeleton_validation_order.md)：多分支 host TilingFunc 骨架——校验顺序 dtype→rank→shape（rank 先于索引防越界）→空张量短路→group 判定→默认基；收尾 SetTilingKey/SetBlockDim(max(usedCoreNum,1))/ws=sys+usr；含大小核均衡三元组与注册机制选择。
- [GetCoreNumAiv 实测≈56-57，group 路由分界 28](tiling_route_threshold_runtime_getcorenumaiv_not_ini.md)：host tiling 分支路由按运行时 GetCoreNumAiv() 而非平台 INI 核数整除判定；实机 group 进入分界 aLoopCntTotal≤28（coreNum/2，非按规格 64 核算的 32），用桩/实现不对称的二值边界探针实机定位。
- [TTK kernel 冒烟判定 tiling 分发命中 vendor V2](ttk_smoke_verify_vendor_v2_tiling_dispatch.md)：vendor 自定义算子在 ascend950 上用最小 kernel 用例冒烟，以 tiling data/blockDim 指纹、同名 V1 注册源排除与标记零计数判定 tiling 分发命中 V2，防 V1 劫持误判。
- [UB 预算反解切分：R 因子反解、R 驻留扩 A、钳制环](ub_budget_backsolve_dual_axis_split_clamp_ring.md)：双轴 tiling 的 UB 预算反解环——先定 aUbFactor，从剩余预算反解 rUbFactor；R 全驻时反向扩 A；cacheBuf 容量超限时 aUbFactor 减半 FloorAlign 重算；装不下一个 R 元素时显式失败。
