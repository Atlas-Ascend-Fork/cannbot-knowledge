# 基础定义

- [常量](constant/index.md)：ASC_C_API_MRGSORT_ELEMENT_LEN表示MrgSort4操作支持的队列数量，值为4。该常量用于asc_mrgsort4接口的src数组长度，以及asc_get_vms4_sr接口的sorted_num数组长度。
- [枚举](enum/index.md)：asc_hf32_round_mode用于Mmad计算开启HF32模式时由FP32舍入到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。
- [寄存器类型](type/index.md)：矢量数据寄存器用于存储矢量数据，其长度为VL（Vector Length）。在Ascend 950PR/Ascend 950DT产品中，VL为256字节，可存储VL / sizeof(dtype)个dtype类型的元素。例如，vector_float可存储256 / sizeof(float) = 64个float类型的元素。
- [联合体](union/index.md)：asc_fill_value_config为fill_value的初始化参数结构体，包含asc_fill_l0a/asc_fill_l0b/asc_fill_l1接口需要配置的各种初始化参数。
