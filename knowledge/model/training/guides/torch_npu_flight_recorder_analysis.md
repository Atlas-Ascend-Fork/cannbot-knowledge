---
type: Guide
title: HCCL飞行记录器：输入身份、匹配分析和当前实现缺口
description: 保留主线/发布版离线工具的参数差异、缺rank与版本校验，并说明静态发现的解析、报告和结果字段问题。
tags:
- task.debugging
- topic.parallelism
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/flight_recorder.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/flight_recorder.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/fr_trace.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/config_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/loader.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/builder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/types.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/fr_logger.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/fr_trace.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/config_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/loader.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/builder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/types.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/fr_logger.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HCCLUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HCCLUtils.hpp
  role: implementation
created_at: '2026-11-09T16:51:39Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# HCCL飞行记录器：输入身份、匹配分析和当前实现缺口

## 固定版本与草稿原因

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf及发布提交f3ecfe4a7ef7395754da7ca2e35661a7132b519b。两版工具文档没有完整产品矩阵，解析器还存在下面的实现缺口，故draft、platforms为空。不把能读取文件或生成输出当作诊断可靠、设备支持或本次运行验证。

## 采集端与输入身份

文档示例开启TORCH_HCCL_ENABLE_MONITORING、DUMP_ON_TIMEOUT，将TRACE_BUFFER_SIZE设1、HEARTBEAT_TIMEOUT_SEC设20。1是集合通信记录容量示例，不是推荐完整历史；20秒也不是所有作业合适的超时。主线构造函数默认监控/超时dump关闭、trace buffer为0、heartbeat为600秒；心跳监控检查watchdog的heartbeat_推进，不能简单等同Python多久没下发新collective。监控、Watchdog、通信执行超时是不同层次。

主线DebugInfoWriter把TORCH_HCCL_DEBUG_INFO_TEMP_FILE作为文件名前缀拼global rank，默认/tmp/hccl_trace_rank_；文档仅设/tmp/时可能得到/tmp/0等数字文件，而非固定子目录布局。Python线程栈另为前缀+rank+_py_traceback，加载器跳过含py_traceback的文件。每次dump可覆盖此前同名输出，需先保留本次作业身份与多次采集顺序；没有文件先查采集开关、buffer、写入和线程条件。

默认writer二进制写trace；离线loader以SafeUnpickler读取，find_class只允许列出的builtins str/int/float/list/dict/tuple。输出-o则由pickle.dump写(types, db)，不是SQLite或JSON；本次没有读取任何真实dump或反序列化文件。

## 参数与入口的实际拼写

| 项目 | 固定实现 |
| --- | --- |
| trace_dir | argparse虽为nargs=?，main仍检查非空字符串且必须为可读目录，不能省略后自动发现采集路径 |
| -j / --just_print_entries | 只打印条目；文档和错误信息写--just-print-entries，但两版parser只注册下划线长名，建议按真实-j识别，不声称文档长名已可运行 |
| --selected-ranks / --pg-filters | 分别为整数列表、PG名称/描述列表，都要求-j；不是完整分析时的任意过滤条件 |
| --allow-incomplete-ranks | 关闭缺dump的强制检查，尽力分析；不会补齐rank数据或证明其未参加通信 |
| -p / --prefix | 显式文件前缀；自动推断要求唯一的字母数字下划线前缀+末尾rank，不接受任意扩展名/混杂多前缀目录 |
| -o / --output、-v / --verbose | 可选输出及详细日志；-j时build_db返回None，因此-o可能只保存(types,None)，文件存在不证明完整数据库已构建 |

真实入口为仓内tools/flight_recorder/fr_trace.py，文档还混用script.py占位；其包导入以tools.flight_recorder为根，不能从任意目录仅照文件名启动就假设导入路径齐全。这里不提供已验证执行命令。

## 分析做了什么

loader从各rank读取version/entries/pg_config，递归深度上限3，超过时break结束遍历，不保证读到所有其他分支；同rank多个匹配文件会覆盖details该项。路径校验还限制字符、软链、属主/权限及单文件默认4GiB，拒绝不等于通信根因。

builder先校验各rank的trace schema version一致，再按所有rank首个record_id的最大值丢弃更早记录，以环形缓存共同窗口对齐。这里的X.Y是trace格式版本，不是torch包版本；对齐前假定每个entries非空，缺rank开关不能修复空entries导致的索引错误。主线对若干缺失键使用默认值，发布版多为直接索引，不能把主线容错自动回填发布版。

PG按pg_uid加成员集合hash区分，检查描述和成员一致；不是把同名PG全部合为一组。条目按组和collective_seq_id寻找对应操作，以类型、状态、size和dtype等进行启发匹配。AllToAll另聚合首个输入/输出Tensor的numel，源码major<=2且minor<=3分支不按大小判错，不将该合取表达式扩写成任意版本的词典序比较；总元素数相等也不能证明全部split配对正确。缺dump会报告证据不足，未发现匹配错误仍可能有其他超时原因。

第一处失配后不再把后续配对当作可靠collective关联，保留未关联HCCLCall；单PG累计失配超过10会中止，不代表全作业所有异常已穷举。不能仅用哪个rank出现在日志里判断唯一责任方。

## 静态发现的实现缺口

| 位置 | 两固定版本中的问题及影响 |
| --- | --- |
| Op.__init__ | 操作名称取frames[0].name后split，分支却比较内置type而非self.type，导致P2P参数和size初始化不按操作类型分支；真实profiling_name与栈名称也不能无条件互换 |
| Op.match | dtype辅助函数用self传给other位置，不能证明已比较两个rank的dtype；未知类型还可能走末尾FULLY_MATCHED |
| error_analysis→EntryState.log | 错误分支传errors关键字，但log仅接受additional_info，可能先发生TypeError而非生成预期报告 |
| EntryState.to_collective | errors为空就pass_check=True，即使另有missing_ranks；必须联合原始证据判断，不能把此标志当全部rank已通过 |
| 结果与打印依赖 | tracebacks列表当前未填充、HCCLCall.traceback_id固定0，不据此伪造可连接堆栈表；utils缺tabulate时只日志、不定义替代函数，-j可能失败，builder的替代函数不会修复另一模块 |
| 读入异常 | read_dump捕获异常后仍返回dump，但失败时未赋值，可能继发UnboundLocalError；不是静默跳过损坏文件的合同 |

这些是逐文件静态核对，未执行故障样本，不声明已修复上游。发布版builder/types/utils/logger通过全文已读主线加完整差异审阅，主线缺键处理和日志格式改动单独保留；共同代码中的上述问题没有因加默认值消失。需先确认实际版本并验证解析与报告，再消费结论。

- [周期状态日志采证](torch_npu_hccl_status_capture.md)
- [Watchdog与独立心跳监控](torch_npu_hccl_watchdog_timeout.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/flight_recorder.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/flight_recorder.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/fr_trace.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/config_manager.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/loader.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/builder.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/types.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/utils.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/flight_recorder/components/fr_logger.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/fr_trace.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/config_manager.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/loader.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/builder.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/types.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/utils.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/tools/flight_recorder/components/fr_logger.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HCCLUtils.cpp)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HCCLUtils.hpp)（implementation）
