# torch extensions

- [PyTorch 自定义 ACLNN 算子的四层接口契约](aclnn_schema_and_graph_contracts.md)：对齐 ACLNN 参数、GE OpDef、PyTorch schema 与 Meta/图转换，避免将不同接口层的名称和顺序直接互换。
- [ACLNN 扩展辅助层的符号解析与异步资源生命周期](aclnn_symbol_resolution_and_lifetime.md)：从 ops_common 模板提取动态符号、路径缓存、ACL 对象转换和工作空间生命周期约束，保留实现版本边界。
- [PyTorch Ascend C 扩展的编译单元与启动 ABI](compilation_and_launch_boundary.md)：分离设备编译单元、普通 C++ 注册代码和共享 Tiling 布局，核对编译成功到算子可调用之间的各层契约。
- [PyTorch Ascend C 扩展的任务队列与 Stream 顺序](task_queue_and_stream_order.md)：区分框架任务队列和 Device Stream，解释直接启动 Kernel 与 OpCommand 回调的排序及重入边界。

- [直调 Add 的 Tensor 合同与 Tiling 生命周期](direct_add_tensor_and_tiling_lifetime.md)：补全线性指针 Kernel 对 shape、stride、设备、Meta 与异步临时区的约束。

- [MX 扩展的原始存储与分发验证](mx_raw_storage_and_dispatch_validation.md)：补全四输入设备、数据与 Scale 元信息以及直接函数注册的适用边界。

- [算子 Python 包装的形状、路径与进程参数](python_shape_paths_and_process_arguments.md)：提取除数合法性、整除维度、环境根与列表传参，纠正仅 exists 就算路径安全的示例。

- [直调对象库构建与 PyTorch 分发合同](direct_object_build_and_dispatch_contracts.md)：补充双编译链、ABI3 范围、Meta 分发与运行产物身份，限定骨架示例的可执行程度。

- [注册 PyTorch 适配器的 Tensor 身份与异步所有权](registry_adapter_tensor_identity_and_async_ownership.md)：补全 Meta 与真实分发一致性、ACL 描述符、回调捕获和异常释放。

- [PyTorch 接入的事件驱动 tile 流水（单组地址复用与四向事件）](pytorch_event_driven_tile_pipeline.md)：框架接入（pybind/torch_library）下的向量核 tile 流水：GetBlockNum/GetBlockIdx 分核后，x/y/z 各复用一块 UB（非双缓冲），V_MTE2/MTE2_V/V_MTE3/MTE3_V 四向事件驱动 tile 循环——循环前预授权事件，重叠发生在不同缓冲之间（x/y 搬入与上一 tile z 搬出），同缓冲的下一 tile 搬入必须等本 tile 计算释放；host 侧经 NPUStream 直发 kernel。
