# 卷积计算

- [Conv3DBackpropFilter核函数（Kernel）侧接口](conv3_d_backprop_filter_kernel/index.md)：Ascend C提供一组Conv3DBackpropFilter高阶API，便于用户快速实现卷积的反向运算，求解反向传播的误差。
- [Conv3DBackpropFilter Tiling侧接口](conv3_d_backprop_filter_tiling/index.md)：用于创建一个Conv3DBackpropFilter单核Tiling对象。
- [Conv3DBackpropInput核函数（Kernel）侧接口](conv3_d_backprop_input_kernel/index.md)：提供实现3D卷积反向运算的高阶API，求解反向传播误差，也可用于实现转置卷积Conv3DTranspose算子。
- [Conv3DBackpropInput Tiling侧接口](conv3_d_backprop_input_tiling/index.md)：用于创建一个Conv3DBackpropInput单核Tiling对象。
- [conv3 d kernel](conv3_d_kernel/index.md)：创建Conv3D对象时需要传入： - Input、Weight、Output和Bias（可选）的参数类型信息，类型信息通过ConvType来定义，包括：内存逻辑位置、数据格式、数据类型。 - Conv3dParam信息（可选），用于开启不同场景的性能优化模板。当前暂不支持使用。
- [conv3 d tiling](conv3_d_tiling/index.md)：Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。
