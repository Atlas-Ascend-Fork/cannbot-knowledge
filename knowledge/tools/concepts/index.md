# 概念

## 算子工具

- [npu-check 运行时正确性检查工具的使用与结论边界](npu_check_usage_and_boundaries.md)：通过 npu-check 启动应用执行 memcheck（搬运指令 GM 访问越界/释放后访问）与 synccheck（SET_FLAG/WAIT_FLAG、GET_BUF/RLS_BUF 配对）检查；GM 越界判定以 aclrtMalloc 成功分配为基准、检测数据在流同步时导出；已验证配置仅 Ascend 950。
- [npu-compute 算子级性能采集工具的命令契约与产物结构](npu_compute_cli_and_artifacts.md)：用 Set（basic/full）或 Section 选择采集范围生成 .npu-rep 报告；解包后按 HardwareInfo.jsonl、Section CSV、summary.jsonl（OpInfoSummary/PerformanceHints）、PipeTrace.json 识别结果。
- [npu-objdump 算子编译产物分析与 AI Core 指令反汇编](npu_objdump_elf_metadata_and_sass.md)：dump-elf 查看 KERNEL_TYPE/TilingKey 等元数据，list/extract 内嵌 device ELF，--sass 反汇编 AIC/AIV 指令并定位异常 PC 指令窗口。
- [Runtime Dump 配置采集与 msaccucmp 精度比对流程](runtime_dump_and_msaccucmp_workflow.md)：acl.json 配置模型/单算子 Dump（stats 筛查与 tensor 采集）、kernel 直调 aclDumpOpTensors 接入、msaccucmp convert/file_compare 与 golden 比对及配对纪律。
- [算子性能报告解读的双源输入契约（npu-rep 与 msopprof PROF 目录）](operator_perf_report_dual_source_contract.md)：950 用 npu-compute .npu-rep（自动识别芯片）、非 950 用 msopprof PROF_*（须显式指定 SoC）；NA 剔除、ratio 双口径归一、active_bw 与全程平均带宽区分等通用口径规则。

## 整网工具

- [torch_npu.profiler 模型推理性能采集的使用契约与产物验收](torch_npu_profiler_collection_contract.md)：必须显式传 ExperimentalConfig(Level1+PipeUtilization) 否则 kernel_details.csv 只有 9 列；schedule 的 prof.step() 总次数按 wait+warmup+active+skip_first 与重复周期核算跨出 active 窗口（wait≠0 不能只补 1 步）；采后按 run failed 计数、按 export_type 区分 CSV/JSON 与 Db 产物验收。
- [模型推理性能数据的按层拆解方法（kernel_details 到 component 实例）](model_perf_breakdown_component_split.md)：按用户描述的模型结构把 op 序列切成 component 实例，按 cluster 规则统计 wall_ms/bubble_ms 中位数与异常 layer；小改/中改/大改三档判档复用。
- [NPU 训练 OOM 诊断流程：来源分类、静态估算与内存快照分析](npu_train_oom_diagnosis_flow.md)：按报错关键字判定 OOM 来源，静态估算（峰值 ≤ 显存×0.95）先行；临时内存 OOM 走条件化排查分支（记录可用显存/allocated/reserved/占用后再做水线 A/B，含失败回退条件），CachingAllocator OOM 做 memory snapshot 六维分析与泄漏线索检测（须控制 shape/负载并区分 allocated 与 reserved）。
- [npugraph_ex 图模式问题的五步分层采集与分诊路由](npugraph_ex_dfx_five_step_triage.md)：eager→compile eager→aot_eager→npugraph_ex force_eager→npugraph_ex 五步顺序执行，首败 step 即问题所在层，按首败层路由到编译/运行时/精度/性能专科。
- [GE 图编译执行进程崩溃的归属判定与 coredump 诊断入口](ge_coredump_attribution_and_diagnosis.md)：从栈顶向下只忽略标准库帧，最近非标准库帧属 GE 库才纳入；以崩溃现场和匹配二进制为主、日志为辅，归属不明标 undetermined 并指路。

## 故障诊断工具

- [昇腾训练推理工具全景：问题域到工具的路由总览](ascend_tool_landscape_routing.md)：故障诊断/算子检测/性能采集/内存采集/精度比对五类场景的工具路由，故障诊断两条命令闭环（asys collect → analyze）与精度三步流程，工具定位与部署位置速查。
- [asys 一键式故障信息收集工具的命令路由与使用约束](asys_command_routing_and_constraints.md)：collect/launch/stacktrace/info/health/diagnose/analyze（六类文件解析前置依赖）/config/profiling 症状路由表；六条使用约束与采集环境变量一致性；压测后电压恢复须逐卡显式指定设备（config 默认只作用 Device 0）。
- [msaicerr AI Core Error 分析工具的三模式命令与约束](msaicerr_aicore_error_analysis.md)：-p 完整分析（info.txt + 内置算子样例环境检查）、-d 解析异常算子 Dump、-dtype 类型转换、-e 自检；仅本地分析、暂不支持通信与 Matmul 融合类算子。
- [msnpureport Device 侧维测信息导出与配置命令](msnpureport_export_and_device_config.md)：单次/常驻导出 Device 系统日志、黑匣子、stackcore、coretrace；config 查询与设置日志级别、加速器复位、singlecommit（AI Core 内部多指令串行化控制，影响性能观测）、坏核屏蔽；导出目录结构解读。
- [AI Core Error 系统化诊断工作流（msaicerr/asys 管线六阶段）](aicore_error_diagnosis_workflow.md)：P0 环境检查→P1 收集→P2 报错行定位→P3 错误类型识别（结论码 101-107）→P4 单算子复现三态→P5 四证据链汇聚与优先级链（105→107→104→106→102→101→103→0）。
- [AscendC 核函数调试接口的选型与调用约束（printf/assert/__trap/asc_dump/clock/时间戳）](ascendc_kernel_debug_api_selection.md)：按观测目标选型；asc_dump 的 dump_size 单位、地址空间匹配、30KB 上限与 32 字节补齐等高频陷阱；观测有效性纪律。
