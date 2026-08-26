# 故障手册

- [编译故障](compilation/index.md)：编译故障知识导航。
- [性能故障](performance/index.md)：性能故障知识导航。
- [精度故障](precision/index.md)：精度故障知识导航。
- [运行故障](runtime/index.md)：运行故障知识导航。

- [validations](validations/index.md)：LongBench 输入构造 input_max_len < system_prompt 长度 → 负索引尾切静默裁掉正文。跑 LongBench / 自定义长序列数据集（dataset != "default"）时，喂给模型的 prompt 正文被大幅裁掉，长序列 case 实际输入远短于预期——但控制台只有一条 logging.info（"The parameter 'input_max_len' should be greater than the length of system_prompt..."），无报错、无中断，极易被忽略。看到这条 info 即代表已越界。
