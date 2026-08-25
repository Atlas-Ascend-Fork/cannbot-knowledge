# 卷积计算

- [Conv3DBackpropFilter Kernel侧接口](conv3_d_backprop_filter_kernel/index.md)：提供Conv3D反向卷积滤波器梯度的Kernel侧接口，包含Init、SetInput、SetGradOutput、Iterate等方法及使用说明。
- [Conv3DBackpropFilter Tiling侧接口](conv3_d_backprop_filter_tiling/index.md)：提供Conv3D反向卷积滤波器梯度的Host侧Tiling接口，包含TConv3DBpFilterTiling结构体、GetTiling及形状与类型设置方法。
- [Conv3DBackpropInput Kernel侧接口](conv3_d_backprop_input_kernel/index.md)：提供Conv3D反向卷积输入梯度的Kernel侧接口，包含Init、SetGradOutput、SetWeight、Iterate等方法及使用说明。
- [Conv3DBackpropInput Tiling侧接口](conv3_d_backprop_input_tiling/index.md)：提供Conv3D反向卷积输入梯度的Host侧Tiling接口，包含TConv3DBackpropInputTiling结构体、GetTiling及形状与类型设置方法。
- [conv3 d kernel](conv3_d_kernel/index.md)：创建Conv3D对象时需要传入： - Input、Weight、Output和Bias（可选）的参数类型信息，类型信息通过ConvType来定义，包括：内存逻辑位置、数据格式、数据类型。 - Conv3dParam信息（可选），用于开...
- [conv3 d tiling](conv3_d_tiling/index.md)：Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格...
- [卷积计算](convolution_compute.md)：汇总Ascend C SIMD高阶API中的卷积计算接口，包含Conv3D及其反向卷积的Kernel侧与Tiling侧接口。
