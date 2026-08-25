# bfloat16类型算术函数

- [__habs](_habs.md)：获取输入数据的绝对值。
- [__hadd](_hadd.md)：计算两个bfloat16类型数据相加的结果，并遵循CAST_RINT模式对结果进行舍入。
- [__hdiv](_hdiv.md)：计算两个bfloat16类型数据相除的结果，并遵循CAST_RINT模式对结果进行舍入。
- [__hfma](_hfma.md)：对输入数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入处理。
- [__hfma_relu](_hfma_relu.md)：对输入bfloat16类型数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。
- [__hmul](_hmul.md)：计算两个bfloat16类型数据相乘的结果，并遵循CAST_RINT模式对结果进行舍入。
- [__hneg](_hneg.md)：获取输入bfloat16类型数据的负值。
- [__hsub](_hsub.md)：计算两个bfloat16类型数据相减的结果，并遵循CAST_RINT模式对结果进行舍入。
- [bfloat16类型算术函数](bfloat16_arithmetic_functions.md)：bfloat16类型算术函数集合，包括绝对值、乘加、加减乘除、取反及融合ReLU的乘加运算。
