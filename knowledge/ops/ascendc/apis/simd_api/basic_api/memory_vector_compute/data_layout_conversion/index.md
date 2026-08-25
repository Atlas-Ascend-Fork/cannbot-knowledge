# 数据排布转换

- [数据排布转换](data_layout_conversion.md)：矢量数据排布转换接口集，包含 Transpose、TransDataTo5HD 等数据布局转换接口。
- [TransDataTo5HD](trans_data_to5_hd.md)：将NCHW格式转换为NC1HWC0格式，也可用于二维矩阵数据块转置，单次repeat可处理512字节数据。
- [Transpose](transpose.md)：实现16x16二维矩阵数据块转置，或NCHW与NHWC数据格式互相转换，支持普通和增强两种模式。
