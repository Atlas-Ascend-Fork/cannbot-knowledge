# 数据压缩

- [asc_pack (废弃)](asc_pack_deprecated.md)：该接口已废弃，请使用 asc_pack_to_low 和 asc_pack_to_high 替代。 将源操作数中的元素选取低8位（b16）、低16位（b32）、低32位（b64）写入目的操作数的低半部分或高半部分。 - asc_pack：将源操作数写入目的操作数的低半部分。 - asc_pac...
- [AscPackToHigh](asc_pack_to_high.md)：将源操作数元素的低位写入目的操作数的高半部分，支持b16、b32、b64和bool类型压缩。
- [AscPackToLow](asc_pack_to_low.md)：将源操作数元素按位压缩写入目的操作数低半部分，支持bool、b16、b32、b64等位宽模式
- [AscUnpack](asc_unpack.md)：将源操作数低半或高半部分元素扩充位宽后写入目的操作数，支持无符号、有符号及bool类型
- [AscUnsqueeze](asc_unsqueeze.md)：根据掩码对矢量数据进行解压缩，dst各元素值取决于mask中前序元素为1的数量
- [数据压缩](data_compress.md)：寄存器侧数据压缩类接口汇总，提供pack_to_low、pack_to_high、unpack、unsqueeze等数据打包与解包能力。
