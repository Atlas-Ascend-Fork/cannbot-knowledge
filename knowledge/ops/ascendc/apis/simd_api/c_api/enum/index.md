# enum

- [AscHf32RoundMode](asc_hf32_round_mode.md)：用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。
- [AscLoadL2CacheMode](asc_load_l2_cache_mode.md)：表示数据从GM搬运到UB时的L2 cache管理策略，在调用asc_copy_gm2ub_align和asc_ndim_copy_gm2ub时使用。
- [AscStoreL2CacheMode](asc_store_l2_cache_mode.md)：表示数据从UB搬运到GM时的L2 cache策略，在调用asc_copy_ub2gm_align时使用。
- [枚举类型](enum_types.md)：枚举类型索引页，包含asc_hf32_round_mode、asc_load_l2_cache_mode与asc_store_l2_cache_mode。
