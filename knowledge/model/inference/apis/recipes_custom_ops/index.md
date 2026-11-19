# Recipes 自定义推理接口

- [custom.npu_dequant_swiglu_clamp_quant：A3 INT8 输出与变体门控](npu_dequant_swiglu_clamp_quant.md)：聚焦二维 INT8 输出路径，明确静态/动态量化、反量化输入及变体截断的区别。
- [custom.npu_gather_selection_kv_cache：A3 选择缓存与原地元数据](npu_gather_selection_kv_cache.md)：说明稀疏 Gather 的四个原地输入、实际长度返回和 TopK 分块限制，区分函数化五返回。
- [custom.npu_moe_init_routing_group_quant：950 分组 FP8 路由](npu_moe_init_routing_group_quant.md)：聚焦 quant_mode 4/5 和固定 128 分组，说明显式专家范围、四返回及包装层形状差异。
- [custom.npu_swiglu_clip_quant：A3 分组削波与有效输出范围](npu_swiglu_clip_quant.md)：限定 BF16 输入、count 分组与动态量化，说明激活方向、形状和尾部垃圾数据边界。
