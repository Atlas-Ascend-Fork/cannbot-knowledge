# 运行时诊断

- [asc_dump 数据不可信诊断：四项核对与最小验证](kernel_asc_dump_data_untrusted_diagnosis.md)：asc_dump 数据不可信时，先核对地址空间、模板类型、元素数和起始地址；区分有效数据的 32B 对齐估算与每核、单次及 VF 容量约束，再用已知长度的小数组复验。
- [Kernel 侧 assert 与 __trap 选型及失败诊断](kernel_assert_and_trap_failure_diagnosis.md)：在 AscendC Kernel 中选择 assert/ascendc_assert 或 __trap；先核对失败是否归属目标断言，再区分标准上下文和可选消息缺失，以确定失败输入验证断言链路并保留 Trap 前的证据。
- [Kernel 调试接口路由矩阵：症状 × 目标平台与编程模式](kernel_debug_api_platform_mode_matrix.md)：把"症状 → 该用哪个 Kernel 调试接口 → 在目标平台/编程模式是否可用"做成一张可执行的路由表，覆盖 printf、assert/ascendc_assert、__trap、asc_dump、clock、asc_time_stamp，并给出"主要为 SIMD 不等于所有形式可用""API 支持不等于当前调用场景可运行"两条判定规则。
- [Kernel printf 无输出诊断](kernel_printf_no_output_diagnosis.md)：按平台与模式、头文件与命名空间、dump 开关、容量及执行路径五类原因排查 AscendC::printf 无输出，再用短字符串复验。
