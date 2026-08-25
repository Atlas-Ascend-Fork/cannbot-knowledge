# 激活函数

- [激活函数](activation_functions.md)：汇总Ascend C SIMD高阶API中各类激活函数接口，包括SoftMax、LogSoftMax、Gelu、SwiGLU、Silu、Swish、GeGLU、ReGlu、Sigmoid等。
- [GeGLU接口](ge_glu_interface/index.md)：采用GELU作为激活函数的GLU变体，按元素对两源Tensor计算GeGLU结果
- [Gelu接口](gelu_interface/index.md)：GELU激活函数的FastGelu化简版本，通过公式化简大幅提升计算性能，支持高精度和高性能模式。
- [LogSoftMax接口](log_soft_max_interface/index.md)：对输入tensor做LogSoftmax计算。
- [ReGlu接口](re_glu_interface/index.md)：用于在host侧获取ReGlu接口所需的最大最小临时空间大小，作为Tiling参数传递到kernel侧使用。
- [Sigmoid接口](sigmoid_interface/index.md)：用于在host侧获取Sigmoid接口所需的最大最小临时空间大小，作为Tiling参数传递到kernel侧使用。
- [Silu接口](silu_interface/index.md)：用于获取Silu Tiling参数：Silu接口能完成计算所需最大临时空间大小和最小临时空间大小。
- [SoftMax接口](soft_max_interface/index.md)：调整SoftMax计算结果为指定值，当maxTensor中存在指定值时，按行将对应softMaxRes结果替换为自定义值，用于SoftMax后处理。
- [SwiGLU接口](swi_glu_interface/index.md)：在host侧获取SwiGLU接口预留临时空间的最大和最小值，用于Tiling参数选择
- [Swish接口](swish_interface/index.md)：用于获取Swish Tiling参数：Swish接口能完成计算所需最大临时空间大小和最小临时空间大小。
