# A3 Cube-Vector 融合算子策略

- [host 按 shape 与 dtype 自适应 tile 参数（行块高 / 列块宽 / 归约块深，含精度边界）](adaptive_tiling_params.md)：将编译期固定 tile 参数改为 host 按 shape、dtype 运行时选择并下发，kernel 读取使用
- [bias 进矩阵乘累加器初始值（消除收尾加法与中间缓冲中转）](bias_into_accumulator_init.md)：将向量核收尾段的bias加法前移为矩阵乘累加器初始值。
- [右矩阵 img2col 类单指令加载（替代归约维窄分形循环）](bpath_img2col_load.md)：将B路逐分形窄宽度转置加载循环替换为一次img2col类单指令搬运。
- [矩阵核到向量核交接流水（环形加深 + 屏障精确化 + 条件等待 + 批量信用同步）](cv_handoff_pipeline.md)：按规模加深环形中转槽，交接时排空写回流水；满足预释放和连续全局计数条件才跳过等待。
- [scatter 宽度与 cube 内部 tile 宽度解耦（相邻列块融合 handoff slot）](epilogue_scatter_fusion.md)：融合相邻输出列块，并将scatter宽度与Cube内部tile宽度解耦。
- [多核铺核（宏块任务分区 + 设备侧分组边界解码 + 分区粒度自适应）](mn_multicore_partition.md)：由主机回读边界并按整组分核，改为宏块任务分区并在设备侧解码分组边界
- [右操作数跨内层循环片上复用（含片上预算守卫回退与任务分组前提）](operand_persistent_onchip.md)：将行段外、列段内重排为列段外、行段内，使右操作数片上驻留复用，并加片上预算守卫回退。
- [预取深度按片上缓存余量动态定尺（加深搬运与计算的重叠窗口）](prefetch_depth_adaptive.md)：将固定预取深度改为按片上缓存余量定尺，先计算深度，再按所得深度初始化。
- [非常驻操作数沿归约维攒大块搬运 + 双缓冲软件流水](reduce_dim_bigchunk_doublebuffer.md)：将归约维多个小块合成大块一次搬入，并把片上源缓冲改为深度 2 的双缓冲。
- [逐行归约存树模式 + 定点事件同步（减全排空次数）](reduction_tree_fixedpoint.md)：将每块后全排空改为归约结果分偏移存树，并在片外读入到向量计算间用定点事件。
- [矩阵乘结果随路转换直出（消除中间缓冲与独立转换段）](result_pipe_cast_direct.md)：配置结果回写流水的目标dtype转换模式，将累加结果边转换边直接写出，去除中间缓冲和独立转换段。
- [向量核收尾段批量化（整块读写 + 整块类型转换 + 屏障塌缩 + 系数向量广播）](vec_epilogue_batched.md)：将收尾段逐行循环改为行块循环，批量二维读写并整块完成点态运算与类型转换。
