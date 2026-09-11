# Utils API

- [C++标准库](cpp_stdlib/index.md)：比较相同数据类型的两个数，返回最大值。
- [log](log/index.md)：提供Host侧打印Log功能，支持在TilingFunc中输出日志；Tiling下沉场景下必须使用本接口，日志需Dump落盘解析。
- [平台信息获取](platform_info/index.md)：Kernel直调场景下获取硬件平台信息的单例管理类，通过GetInstance获取PlatformAscendC指针以访问核数等平台信息。
- [原型注册与管理](prototype_register_management/index.md)：注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。
- [RTC](rtc/index.md)：注册指定的名称表达式，该表达式代表了一个__global__函数。 主要用于__global__函数为模板函数的场景，调用本接口后，可以通过aclrtcGetLoweredName接口获取函数的mangling name，在launch阶段调用对应的模板__global__函数。
- [SuperKernel](super_kernel/index.md)：本接口为算子SuperKernel场景提供绑定原核函数和SK子函数的能力。核函数直调算子的完整适配方法请参见核函数直调算子额外适配说明。
- [Tiling数据结构注册](tiling_data_structure_register/index.md)：定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。
- [Tiling下沉](tiling_sink/index.md)：在Tiling下沉场景中，该宏定义用于生成Tiling下沉的注册类，再通过调用注册类的成员函数来注册需要下沉的Tiling函数。
- [Tiling模板编程](tiling_template_programming/index.md)：Tiling模板编程时，开发者通过调用此接口自动生成并配置TilingKey。 使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
- [Tiling调测](tiling_tuning/index.md)：设置算子的属性以及对应值
- [调测接口](tuning_interface/index.md)：在SIMT代码中调用此接口会中断算子的运行，适用于Kernel侧异常场景的调试。
