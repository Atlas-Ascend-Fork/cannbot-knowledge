# concepts

- [Kernel、编译与运行时](compile_and_runtime.md)：当前 Host 编译、两级缓存、JitCompiledFunction 重复启动、stream 与 DLPack 工作流。
- [Constexpr 折叠与动态 if 初始化约束](constexpr_control_flow_folding.md)：tla.Constexpr 参数、dataclass 属性访问在 tla.range 循环体内的静态折叠边界、动态 if 的变量初始化检查，以及向量循环内动态 if 的性能代价。
- [Copy、flag、mutex 与流水同步](copy_and_sync.md)：数据搬运、同核 flag、跨核 flag、mutex、barrier 和流水循环的使用边界。
- [跨执行引擎 Credit 与 Publication](cross_engine_credit_and_publication.md)：区分本地流水依赖、buffer credit、跨核 ready 信号和阶段性 GM publication，避免将 barrier 与 flag 混作全局同步。
- [动态控制流中的 Tensor Binding](dynamic_control_flow_tensor_binding.md)：处理 dynamic-if、tla.range 和 outlined region 中 Tensor descriptor、数值状态与 loop-carried binding 的合法构造方式。
- [动态 Layout 与 DLPack 绑定](dynamic_layout_and_dlpack.md)：用动态 shape/stride 元数据复用编译产物，并保持 DLPack zero-copy 绑定。
- [动态尾块 Layout 与 Origin Shape](dynamic_tail_layout_and_origin_shape.md)：区分固定 storage tile、逻辑有效区域和真实地址 stride，构造可用于 GM、UB、L1 的动态尾块 tensor view。
- [用户提供的 Ascend C 外部函数](extern_ascendc.md)：用 tla.extern 声明、类型检查、编译并从 Cube/Vector region 调用单个内联 Ascend C 入口。
- [MMAD 操作数布局契约与转置表达](mmad_transpose_contract.md)：tla.mmad 强制 acc=L0Clayout、lhs=zN、rhs=nZ；转置只能靠同一块内存的 layout 视图重解释，不能用 transpose 参数。
- [PACK Store 与设备侧舍入](pack_store_and_round_trip_cast.md)：用 StoreDist.DIST_PACK_B32 直接落窄化结果，并在设备侧完成 scale 与 f32->f16/bf16 舍入，避免 host cast 改变舍入语义。
- [Python 语法与动态控制流](python_control_flow.md)：CATLASS DSL 中自包含静态值、动态分支、循环、短路条件和 loop-carried 状态的语法边界。
- [SIMT Vector Function 与 Tensor 标量访问](simt_and_scalar_access.md)：SIMT thread 索引、同步、标量算子和 UB/GM tensor 标量 load/store 的使用方式。
- [Tensor、layout 与本地内存](tensor_layout_memory.md)：Tensor 视图、layout 标签、地址空间及 C310 本地内存容量的源码约束。
