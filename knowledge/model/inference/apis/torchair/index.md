# TorchAir模型接口参考

汇集固定版本证据支持的模型相关知识；具体适用范围以卡片正文为准。

- [create_npu_tensors：分离部署中的 Device 地址包装](create_npu_tensors.md)：说明同 shape/dtype 的 KV 地址转 Tensor 列表，明确地址有效性与内存所有权核验。
- [torchair.ops FIA：GE Device 长度 Tensor 与版本差异](device_length_attention_wrappers.md)：区分 TorchAir 图专用长度 Tensor 入口和 torch_npu 接口，记录 v1/v2 参数名及文档签名冲突。
- [GE cache_compile：持久编译缓存与 Guards 失效边界](ge_cache_compile.md)：说明 torchair.inference.cache_compile 的 config/backend、ge_cache、rank 命名空间及跨 CANN 版本和模型变更时的复用约束。
- [ge.custom_op：原生 Converter 的 IR 输入、属性与动态输出](ge_custom_op.md)：说明 REG_OP 映射、args 优先级、显式属性类型和动态输出结构，不混同自动适配路线。
- [GE 跨流接口：record、wait、npu_wait_tensor 与流标签](ge_stream_dependencies.md)：区分无输出节点标记、当前流等待与返回原 Tensor 的依赖注入，并说明流内并行参数的版本门槛。
- [get_compiler：自定义后端中的 GE 编译器](get_compiler.md)：说明 NpuFxCompiler 与 torch.compile backend 的层次差别，保留 AOT 集成前提。
- [torchair.get_npu_backend：获取 GE 图编译后端](get_npu_backend.md)：获取传给 torch.compile 的 GE 后端，说明 CompilerConfig、custom_decompositions 与配置生效时机。
- [torchair.ops.npu_print：GE 图内异步打印与展示量](npu_print.md)：说明 Tensor 参数、摘要和详细输出，明确异步顺序、额外开销及 dtype 限制。
- [npugraph_ex cache_compile：options、动态 trace 与缓存契约](npugraph_ex_cache_compile.md)：独立说明 torch.npu.npugraph_ex.inference.cache_compile，避免混用 GE config/ge_cache 和以跳 Guards 放宽实际输入。
- [npugraph_ex.compile_fx：AOT 后 FX 编译与功能缺口](npugraph_ex_compile_fx.md)：说明直接编译 FX 的输入和可执行返回值，明确自定义后端不继承全部 npugraph_ex 能力。
- [op_never_timeout：GE 算子标签与融合后的失效边界](op_never_timeout.md)：说明不超时 scope 的 True/False 嵌套、禁止断图以及融合不继承属性。
- [readable_cache：读取 GE 与捕获后端的编译缓存](readable_cache.md)：说明 compiled_module 解析、打印和文件输出，不将可读缓存当作运行兼容或性能证明。
- [register_fx_node_ge_converter：按准确 overload 注册 GE 转换](register_fx_node_ge_converter.md)：以装饰器为准确的 torch.ops 节点注册 Ascend Converter，并区分 Meta 推导与 GE 转换。
- [register_replacement：两后端 Pattern 替换与匹配校验](register_replacement.md)：记录融合注册参数、标量绑定、重复模式版本门槛和后端开关，链接模型侧布局规则。
- [set_dim_gears：GE 动态 shape 分档的维度与档位限制](set_dim_gears.md)：设置输入 Tensor 的动态维度档位，说明 dynamic=True、非私有格式、档位数量和 0/1 边界。
- [use_internal_format_weight：模型权重私有格式转换](use_internal_format_weight.md)：说明原地转换模型权重且无返回值，不将格式转换与固定地址或所有算子支持混同。
