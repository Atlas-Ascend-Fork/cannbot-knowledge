# 概念

## 算子工具

- [npu-check 运行时正确性检查工具的使用与结论边界](npu_check_usage_and_boundaries.md)：通过 npu-check 启动应用执行 memcheck（搬运指令 GM 访问越界/释放后访问）与 synccheck（SET_FLAG/WAIT_FLAG、GET_BUF/RLS_BUF 配对）检查；GM 越界判定以 aclrtmalloc 成功分配为基准、检测数据在流同步时导出；已验证配置仅 Ascend 950。
- [npu-compute 算子级性能采集工具的命令契约与产物结构](npu_compute_cli_and_artifacts.md)：用 Set（basic/full）或 Section 选择采集范围生成 .npu-rep 报告；解包后按 HardwareInfo.jsonl、Section CSV、summary.jsonl（OpInfoSummary/PerformanceHints）、PipeTrace.json 识别结果。
- [npu-objdump 算子编译产物分析与 AI Core 指令反汇编](npu_objdump_elf_metadata_and_sass.md)：dump-elf 查看 KERNEL_TYPE/TilingKey 等元数据，list/extract 内嵌 device ELF，--sass 反汇编 AIC/AIV 指令并定位异常 PC 指令窗口。
- [Runtime Dump 配置采集与 msaccucmp 精度比对流程](runtime_dump_and_msaccucmp_workflow.md)：acl.json 配置模型/单算子 Dump（stats 筛查与 tensor 采集）、kernel 直调 aclDumpOpTensors 接入、msaccucmp convert/file_compare 与 golden 比对及配对纪律。
- [算子性能报告解读的双源输入契约（npu-rep 与 msopprof PROF 目录）](operator_perf_report_dual_source_contract.md)：950 用 npu-compute .npu-rep（自动识别芯片）、非 950 用 msopprof PROF_*（须显式指定 SoC）；NA 剔除、ratio 双口径归一、active_bw 与全程平均带宽区分等通用口径规则。

## 整网工具

## 故障诊断工具
