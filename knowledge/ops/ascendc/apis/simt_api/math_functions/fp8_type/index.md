# fp8类型

- [fp8数据转换函数](fp8_conversion_functions/index.md)：将float2的两个分量按CAST_RINT模式转换为FP8类型（e4m3或e5m2）的8位浮点数，支持饱和与非饱和溢出处理，结果以位级打包存储。
- [fp8数据类型简介（FP8类型）](fp8_data_type_intro.md)：SIMT编程支持3种fp8数据类型，分别是float8_e4m3_t、float8_e5m2_t、hifloat8_t。其数据范围如下：
