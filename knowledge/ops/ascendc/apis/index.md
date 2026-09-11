# Ascend C API

- [AI CPU API](ai_cpu_api/index.md)：该接口实现AI CPU算子Kernel调试场景下的assert断言功能。 算子执行中，如果assert内部条件判断不为真，则输出assert条件、触发文件名、行号等信息。
- [附录](appendix/index.md)：本节汇总介绍了一些主要的API的流水类型，以下内容针对如下型号生效：
- [SIMD API](simd_api/index.md)：说明 SIMD 基础与高阶 API 的头文件、链接方式、存储单元对齐要求及 TPosition 内存映射。
- [SIMT API](simt_api/index.md)：SIMT API是面向AI处理器的并行计算编程接口，可以实现高效的数据并行计算。SIMT API支持两种编程模型：SIMT编程、SIMD与SIMT混合编程，用户可先阅读SIMT编程简介和SIMD与SIMT混合编程简介，以了解编程基础，后续章节将详细介绍API接口。
- [Utils API](utils_api/index.md)：比较相同数据类型的两个数，返回最大值。
