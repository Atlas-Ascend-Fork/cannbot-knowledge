# SIMD API

- [高阶API](adv_api/index.md)：采用GELU作为激活函数的GLU变体，按元素对两源Tensor计算GeGLU结果
- [基础API](basic_api/index.md)：对GM地址上的值执行原子加操作，将旧值与输入标量求和后写回，返回修改前的旧值。
- [API列表](c_api/index.md)：C API文档按最细粒度公共头文件归类。除试验接口外，整体使用时可以包含c_api/asc_simd.h。
- [通用说明和约束（SIMD API）](general_description_and_constraints.md)：说明 SIMD 基础与高阶 API 的头文件、链接方式、存储单元对齐要求及 TPosition 内存映射。
- [Tensor API](tensor_api/index.md)：Tensor API的Algorithm层为基于Tensor的数据搬运和矩阵计算提供统一的调用入口。其中，copy和mmad接口分别用于执行数据搬运和矩阵计算，make_copy和make_mmad接口用于构造对应的Atom原子对象。
