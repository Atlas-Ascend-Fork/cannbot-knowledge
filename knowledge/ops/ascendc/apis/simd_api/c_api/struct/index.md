# struct

- [AscFillValueConfig](asc_fill_value_config.md)：fill_value的初始化参数结构体，包含fill_l0a、fill_l0b和fill_l1接口需要配置的初始化参数。
- [AscL13dFmatrixConfig](asc_l13d_fmatrix_config.md)：用于设置3D格式搬运接口的Feature map属性参数，包括宽高和四周填充大小。
- [AscLoad3dV2Config](asc_load3d_v2_config.md)：用于设置Load3Dv2接口的repeat参数，包括迭代步长、次数和方向。
- [AscNdimPadCountConfig](asc_ndim_pad_count_config.md)：用于设置asc_ndim_copy_gm2ub接口各维度左右侧的padding元素个数。
- [AscStoreAtomicConfig](asc_store_atomic_config.md)：原子操作配置结构体，包含原子操作启用位与操作类型，用于asc_get_store_atomic_config接口使用。
- [数据结构](data_structures.md)：SIMD C API数据结构汇总，包含填充值配置、3D矩阵加载配置、多维padding配置及原子存储配置等结构体定义。
