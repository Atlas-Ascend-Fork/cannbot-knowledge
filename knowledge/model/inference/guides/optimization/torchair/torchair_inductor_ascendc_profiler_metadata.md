---
type: Guide
title: Inductor AscendC Profiler：队列内Range、形状与观测参数
description: 保留Profiler设计并补完整元数据生成、pk符号收集、标量/别名方向以及rt下发的HostToDevice归因报告。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/profiling_report_summary.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/profiling_report_summary_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/_asc_codegen.py
  role: implementation
created_at: '2026-11-09T18:28:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC Profiler：队列内Range、形状与观测参数

## 固定设计与范围

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c双语Profiler设计。整套硬件/运行组合未闭合，保留draft/空platforms；设计中的测试结论是来源记录，本次没有启动Profiler或编译Wrapper。

## 运行时刷新与下发位置

prof_enabled是可变运行状态，在同步初次加载和逐次launch刷新，避免“编译时未开采集，以后永远无元数据”。Python走is_prof_inited，Cpp走profilerEnabled，不把两种状态来源仅因设计称“相同”就当所有时序完全等价。

RangePushEx/RangePop及元数据生成放在实际launch lambda内，覆盖TaskQueue0/1与2路径；block_dim和stream到实际下发时才最终确定，若放在入队之外容易记录错误线程、流或配置。Host队列本身与Device执行仍区分，不用Range包围Host调用的时长直接替代设备耗时。

## Tensor和符号元数据

每个输入/输出分别记type0/1，原地输入输出可同时有两条，不因同地址只保留一个方向。shapeDim最多8、超出截断，未知dtype记-1；opType=AscBackend、message version1以及运行时block_dim/stream属于该实现的观测合同，不推导全部原始Tensor信息已完整保留。

设计写format常数2并解释成NCHW，但同版本GE枚举2为ND；本卡只记录常数/占位行为，不能拿它证明真实输入是NCHW或私有格式。float8及fnuz变体映射同35/36也不证明表示语义和数值可互换。

符号形状先用prof_arg_shapes（如转置分支的原始形状），没有则按V.graph做简化；外层s*需要映射到已有ks*或新增pk*。pk只服务Profiler形状，不进入实际Tiling参数；看到额外参数不能认定搜索空间或计算行为已改变。采集元数据需先于参数遍历，并通过graph标记防止重复插入。

CppPrinter将FloorDiv等表达成div_floor_integer，避免Python //在C++中变成注释；Mod用%、floor用std::floor并补头文件。能打印符号表达式不等于所有动态输入都能被具体化或该shape已真实运行。

## 验证及设计更新

设计通过宏自定义必要CANN结构体，帮助缺头文件时编译，不是任意版本CANN ABI兼容保证。结构/字符串断言测试只证明生成代码形态，不等于Profiler在设备实际记录了正确shape、block数或时间。

设计仍提示PGO首调与外部采集互斥；同提交较新手册及[完整选优实现](torchair_inductor_ascendc_static_topn.md)已采用独立子进程，不能由旧条目抹去这一变化，也不据子进程隔离推定所有采集工具组合兼容。核对父/子进程采集目录、当前配置、实际CSV和时间线后，才用元数据解释模型路径。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/profiling_report_summary.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/profiling_report_summary_en.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals.md)（constraint）

## 完整生成器对照

本次完整静态核对主线codegen/_asc_codegen.py，包括普通AutofuseLaunch与rtLaunch生成字符串。没有执行其中任何Python/C++、启动采集或设备。完整调用与加载分支见[Codegen实现](torchair_inductor_ascendc_codegen_contract.md)。

_collect_unmapped_prof_symbols仅第一次执行：以现有SizeArg的expr字符串及内部name构成已绑定集合，扫描TensorArg对应buffer的simplify后shape自由符号；已有prof_arg_shapes覆盖的参数跳过，查询异常被吞掉。新符号命名pk0…并追加为graph.args的SizeArg，设置prof_size_var_names、prof_size_vars及_prof_symbols_collected标记；后续调用不自动按新图内容重新扫描。这里只扫描shape，不另把所有stride、offset或外部符号无条件加入。

_codegen_profiling_func的观测形状优先prof_arg_shapes，否则V.graph buffer shape，查询异常可留下空shape；符号经CppPrinter映射再最多取8维，每维写static_cast<uint32_t>，没有在这里保留任意大/负维度的无损语义。一个TensorArg若其name命中inplace_input_outers，先额外记input，再按name是否在outputs_outer决定正常type；不能把任意共享data_ptr或内存重叠都当作已识别原地输入。

实际dtype枚举映射如下；这是观测编码，不是算子支持矩阵。

| dtype | 写入值 |
| --- | --- |
| float32/float16/bfloat16 | 0/1/27 |
| int8/int16/int32/int64 | 2/6/3/9 |
| uint8/uint16/uint32/uint64 | 4/7/8/10 |
| float64/bool | 11/12 |
| complex32/complex64/complex128 | 33/16/17 |
| float8_e5m2及e5m2fnuz | 35 |
| float8_e4m3fn及e4m3fnuz | 36 |
| 其他dtype | 生成字面值-1，目标字段为uint32 |

helper设置format=2、type0/1、opType=AscBackend、kernelType=0、message version=1、tensorNum、blockNums与stream。没有Tensor信息时返回两个空字符串，不产生这一组Range代码。生成的aclprofTensor/Info/EventAttributes置于lambda顶部、if(prof_enabled)之外，保证从push到launch后的pop都处于本地作用域；setter把uint8非零视为开启，源中这个全局bool没有独立加锁协议。

rtLaunch除Range外，还在aclrtLaunchKernelWithHostArgs前读cycle begin，随后生成node_basic_info和node_launch两份报告：opName用规范化Kernel名、opType用AscBackend的hash，线程取SYS_gettid，node时间戳放在begin/end之间，taskType固定AIV，blockDim来自本次Tiling。MsprofReportCompactInfo/ReportApi返回值被丢弃；这些调用存在不证明后处理一定建立flow或采集成功。普通AutofuseLaunch分支没有同一段本地Msprof补报代码。

结构体头的fallback定义、8维裁剪、固定格式/任务类型与参数名判断都保留准确范围；不能从观测信息推导真实存储布局、设备完成时间、所有别名、完整输入Tensor或数值正确性。本次无新增verified。

## 本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/_asc_codegen.py)（implementation）：1–1623。
