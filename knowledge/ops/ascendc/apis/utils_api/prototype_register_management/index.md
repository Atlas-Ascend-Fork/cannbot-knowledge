# 原型注册与管理

- [原型注册接口（OP_ADD）](op_add.md)：注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。
- [OpAICoreConfig](op_ai_core_config/index.md)：用于标识该算子实现是否支持入图时的静态Shape编译。
- [OpAICoreDef](op_ai_core_def/index.md)：注册算子支持的AI处理器型号以及OpAICoreConfig信息。
- [OpAICPUDef](op_aicpu_def/index.md)：此参数为预留参数，请保持固定值“100”。
- [OpAttrDef](op_attr_def/index.md)：设置算子属性的注释。用于在自动生成算子原型头文件时，同步生成算子原型注释。 基于OpDef算子原型定义，自定义算子工程可以实现如下自动化能力：自动生成图模式场景使用的算子原型头文件，开发者可以使用生成的算子原型进行构图、图编译、图执行等操作。 生成的注释有助于辅助理解算子原型，并可以基于这些注释自动生成算子原型的文档说明。通常情况下，内置CANN算子使用较多。开发者可以按需使用。
- [OpDef](op_def/index.md)：设置AICore的配置信息：包括Tiling处理回调函数、能力检查回调函数、基础的配置信息等。
- [OpHostCPUDef](op_host_cpu_def/index.md)：此参数为预留参数，请保持固定值“100”。
- [OpMC2Def](op_mc2_def/index.md)：配置通信域名称，每个名称对应一个通信域。配置后在Kernel侧调用GetHcclContext接口可获取通信域对应的context（消息区）地址。
- [OpParamDef](op_param_def/index.md)：配置该参数，当单算子API（aclnnxxx）接口中的输入（aclTensor类型）是非连续tensor时，框架会自动将其转换为连续tensor。 该接口仅在如下场景支持： - 通过单算子API执行的方式开发单算子调用应用。 - 间接调用单算子API\(aclnnxxx\)接口：Pytorch框架单算子直调的场景。
- [OpAICoreConfig注册接口（REGISTER_OP_AICORE_CONFIG）](register_op_aicore_config.md)：不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方式，针对不同的AI处理器型号注册差异化的算子原型。REGISTER_OP_AICORE_CONFIG宏在不改变原有注册的基础上，允许单独新增文件来注册算子在不同硬件形态上的差异化信息。 使用该注册宏需要包含以下头文件：
