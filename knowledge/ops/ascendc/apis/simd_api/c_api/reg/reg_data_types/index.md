# 寄存器数据类型

- [asc_create_iter_reg (废弃)](asc_create_iter_reg_deprecated.md)：该接口已废弃，请使用asc_update_addr_reg实现此功能。 地址寄存器通过该接口初始化，然后在循环之中使用地址寄存器存储地址偏移量，该重载接口同步支持1-4个offset参数，并支持初始化b8/b16/b32位宽的寄存器，适配1-4维Tensor。底层在多维循环中自动计算地址偏移，...
- [AscCreateMask](asc_create_mask.md)：根据pat_mode生成掩码寄存器，支持b8、b16、b32三种位宽模式，指定参与计算的元素位置
- [AscGetMaskSpr](asc_get_mask_spr.md)：从特殊功能寄存器读取mask值，并按b16或b32数据类型格式化后返回
- [AscUpdateAddrReg](asc_update_addr_reg.md)：更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式
- [AscUpdateMask](asc_update_mask.md)：根据元素个数生成mask并自动扣减当前向量处理单元元素数，支持b8、b16、b32位宽模式
- [reg数据类型定义](data_type_definition.md)：定义矢量数据寄存器的数据类型，按位宽分类列举vector_int8_t、vector_half、vector_float等类型，仅Ascend 950PR/950DT支持。
- [寄存器数据类型](reg_data_types.md)：寄存器数据类型相关接口汇总，包含数据类型定义、地址寄存器更新、掩码创建与获取等能力。
