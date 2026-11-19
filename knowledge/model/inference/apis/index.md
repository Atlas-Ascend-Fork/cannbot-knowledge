# 模型推理接口

- [torch npu](torch_npu/index.md)：共 134 张知识卡（如 张量内存复制（torch_npu.copy_memory_）、推理接口 empty_with_format（torch_npu.empty_with_format）、推理接口 empty_with_swapped_memory（torch_npu.empty_with_swapped_memory） 等）。

- [DeepEP 通信接口](deepep/index.md)：共 5 张知识卡（如 DeepEP fused_deep_moe：融合模式、激活与返回计数差异、DeepEP get_dispatch_layout：Normal 路由统计与返回值边界、DeepEP Low-Latency：容量、有效 token 与量化兼容边界 等）。
- [SGLang 推理加速与框架调用接口](sgl_kernel_npu/index.md)：共 92 张知识卡（如 SGLang ADA 分块稀疏注意力接口、SGL 残差相加与RMSNorm偏置融合接口、SGLang AICPU AddExample的输入与独立存储合同 等）。
- [Recipes 自定义推理接口](recipes_custom_ops/index.md)：独立 custom 命名空间的选择缓存、SwiGLU 量化和 950 分组路由；与标准 TorchNPU 接口分开核对交付件。

- [TorchAir模型接口参考](torchair/index.md)：共 16 张知识卡（如 create_npu_tensors：分离部署中的 Device 地址包装、torchair.ops FIA：GE Device 长度 Tensor 与版本差异、GE cache_compile：持久编译缓存与 Guards 失效边界 等）。
