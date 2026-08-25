# 数据压缩

- [数据压缩](data_compression.md)：Reg矢量计算数据压缩接口索引页，包含Unsqueeze、Pack与UnPack。
- [Pack](pack.md)：将源操作数元素的低位部分写入目的寄存器的低半部分或高半部分，实现数据位宽压缩。
- [UnPack](un_pack.md)：将源操作数低半或高半部分元素以高位填0或保持符号位方式扩充位宽写入目的寄存器。
- [Unsqueeze](unsqueeze.md)：以目的寄存器为源和目标，根据mask进行解压缩，生成前缀1计数序列。
