# 逻辑计算

- [AscAnd](asc_and.md)：根据mask对源操作数src0、src1执行按位与操作，结果写入dst，支持矢量数据寄存器和掩码寄存器。
- [AscNot](asc_not.md)：对源操作数src执行按位取反操作，将结果写入目的操作数dst。
- [AscOr](asc_or.md)：根据mask对源操作数src0、src1执行按位或操作，结果写入dst，支持矢量数据寄存器和掩码寄存器。
- [AscShiftLeft](asc_shiftleft.md)：根据mask对输入数据src0按照src1对应元素进行左移操作，结果写入dst。
- [AscShiftLeftScalar](asc_shiftleft_scalar.md)：根据mask对源操作数src执行左移，左移位数由标量参数value决定，结果写入dst。
- [AscShiftRight](asc_shiftright.md)：根据mask对输入数据src0按照src1对应元素进行右移操作，结果写入dst。
- [AscShiftRightScalar](asc_shiftright_scalar.md)：根据mask对源操作数src执行右移，右移位数由标量参数value决定，结果写入dst。
- [AscXor](asc_xor.md)：根据mask对矢量数据寄存器或掩码寄存器src0和src1执行按位异或操作，结果写入dst。
- [逻辑计算](logic_compute.md)：寄存器侧逻辑计算类接口汇总，提供and、or、not、xor及左右移位等按位逻辑与移位操作。
