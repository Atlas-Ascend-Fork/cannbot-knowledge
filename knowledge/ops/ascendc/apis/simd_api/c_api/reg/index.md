# Reg矢量计算

- [基础算术](arithmetic_compute/index.md)：寄存器侧基础算术类接口汇总，提供abs、add、sub、mul、div、exp、ln、sqrt、relu等逐元素矢量计算能力。
- [比较与选择](compare_and_select/index.md)：逐元素比较两个源操作数是否相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。仅在AIV上生效。
- [复合计算](compound_compute/index.md)：根据mask对源操作数src0和src1进行按元素相减再求绝对值，将结果写入dst。
- [数据压缩](data_compress/index.md)：该接口已废弃，请使用 asc_pack_to_low 和 asc_pack_to_high 替代。 将源操作数中的元素选取低8位（b16）、低16位（b32）、低32位（b64）写入目的操作数的低半部分或高半部分。 - asc_pac...
- [数据填充](data_fill/index.md)：将src的最低位元素广播到dst中被mask筛选的位置，未被mask筛选的位置置为0。
- [数据重排](data_rearrange/index.md)：将src0和src1中的元素解交织存入dst0和dst1，提供矢量数据解交织和掩码解交织两种模式，仅在AIV上生效。
- [类型转换](data_type_convert/index.md)：将bfloat16_t类型转化为fp4x2_e1m2_t类型，并支持多种舍入模式。 关于舍入模式的详细说明，请参见舍入模式。 由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索...
- [直方图计算](histogram_compute/index.md)：对直方图数据进行累计统计，支持低位和高位两种模式，统计结果在目的寄存器原始数据基础上累加。
- [索引操作](index_operate/index.md)：以指定起始值生成递增或递减索引序列并保存到矢量数据寄存器，仅在AIV上生效。
- [逻辑计算](logic_compute/index.md)：根据mask对源操作数src0、src1执行按位与操作，结果写入dst，支持矢量数据寄存器和掩码寄存器。
- [归约计算](reduce_compute/index.md)：将源操作数中每两个相邻数值相加，结果连续保存在目的操作数的低半部分。
- [Reg矢量计算](reg.md)：C语言Reg矢量计算接口集合，涵盖数据类型、数据搬入搬出、算术计算、类型转换、同步控制等。
- [寄存器数据类型](reg_data_types/index.md)：该接口已废弃，请使用asc_update_addr_reg实现此功能。 地址寄存器通过该接口初始化，然后在循环之中使用地址寄存器存储地址偏移量，该重载接口同步支持1-4个offset参数，并支持初始化b8/b16/b32位宽的寄存器，...
- [reg数据搬入](reg_load/index.md)：完成矢量寄存器之间、掩码寄存器之间以及矢量寄存器到掩码寄存器的数据搬运。
- [reg数据搬出](reg_store/index.md)：根据索引值index将源操作数src中的元素分散存储到目的操作数dst中。
- [同步控制](sync_control/index.md)：Reg计算宏函数内不同流水线之间的同步指令，目的流水线等待源流水线所有指令完成后执行。
- [系统变量访问](system_variables_access/index.md)：该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。
