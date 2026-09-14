# 标量计算

- [位运算](scalar_bit/index.md)：对一个64位无符号整数执行位清除操作，将bits中第idx位清零，其余位保持不变。返回修改后的64位无符号整数。
- [类型转换](scalar_convert/index.md)：将float类型的标量转换为half类型并返回，舍入模式固定为ODD（最近邻奇数舍入）。
- [数据搬入](scalar_load/index.md)：不经过DCache直接从GM地址读取整型数据。 当多核操作GM地址且数据无法对齐到Cache Line时，经过DCache读写可能引入Cache Line粒度的数据覆盖。此时，可使用本接口绕过DCache读取GM数据。
- [数据搬出](scalar_store/index.md)：不经过DCache向GM地址上写数据。 当多核操作GM地址时，如果数据无法对齐到Cache Line，经过DCache的方式下，由于按照Cache Line大小进行读写，会导致多核数据随机覆盖的问题。此时，可以采用不经过DCache直接读写GM地址的方式，从而避免上述随机覆盖的问题。
