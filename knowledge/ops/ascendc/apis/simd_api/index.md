# simd api

- [adv api](adv_api/index.md)：汇总Ascend C SIMD高阶API中各类激活函数接口，包括SoftMax、LogSoftMax、Gelu、SwiGLU、Silu、Swish、GeGLU、ReGlu、Sigmoid等。
- [basic api](basic_api/index.md)：对GM地址上的值执行原子加操作，将旧值与输入标量求和后写回，返回修改前的旧值。
- [c api](c_api/index.md)：从GM地址预加载数据到Data Cache，每次调用预加载一个Cache Line大小的数据。
- [通用说明和约束（SIMD API）](general_description_and_constraints.md)：说明 SIMD 基础与高阶 API 的头文件、链接方式、存储单元对齐要求及 TPosition 内存映射。
