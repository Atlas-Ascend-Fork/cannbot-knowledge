---
type: Guide
title: TorchNPU错误定位：首错、分层错误码与Core证据
description: 整理错误码结构、日志关联与崩溃取证，区分参数、底层调用和历史案例；整套定位路径缺少产品矩阵，保留草稿。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_code_description/error_code_information.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/error_code_description/error_code_information.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_code_description/error_code_mechanism.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/error_code_description/error_code_mechanism.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_information_analysis_guide/error_information_analysis/error_information_analysis_process.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/error_information_analysis_guide/error_information_analysis/error_information_analysis_process.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_information_analysis_guide/error_information_introduction.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/error_information_analysis_guide/error_information_introduction.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_information_analysis_guide/locating_core_dump_faults.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/error_information_analysis_guide/locating_core_dump_faults.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_process.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/troubleshooting_process.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_information_analysis_guide/error_information_classification/command_output.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_information_analysis_guide/error_information_classification/plog_log.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/failed_verify_op_parameters.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/initialization_error.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/operator_called_error.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/description_each_field.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/description_each_field.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/meaning_field_2.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/meaning_field_2.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/meaning_field_3.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/meaning_field_3.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/error_information_analysis_process.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/error_information_analysis_process.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/example.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/example.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/python_call_stack.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/python_call_stack.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/locate_component_reports_error_plog.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/locate_component_reports_error_plog.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/viewing_stack.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/viewing_stack.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/troubleshooting_process.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/troubleshooting_process.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/viewing_stack_information_python_applications.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/application_logs.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/obtaining_plog_logs.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/plog_log_HCCL.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/plog_log_OOM.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/CANN_software_error_code.png
  role: constraint
created_at: '2026-11-09T16:08:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU错误定位：首错、分层错误码与Core证据

## 固定来源与范围

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf中英文故障说明及所附历史图。页面未给整套路径的产品矩阵，draft、platforms为空；不将示例PyTorch2.1/Python3.8或旧时间戳当作当前配套。本次仅静态审阅，没有运行故障、日志采集、gdb或系统配置命令。

## 从首错到相关组件

先保存同次作业的完整屏显、各rank首个异常及时间，再区分CANN错误码、Python Traceback、TorchNPU错误码和原生框架异常；屏显不足再看相同进程/时间的plog。异步执行可能在synchronize等后续调用才报告错误，不能凭最后一帧认定最初失败的算子。

流程图将有错误码时查码、无错误码时收集/分析信息，最后重新验证并记录处理过程；它不是“有错误码就不需要日志”。首节点屏显与各节点实际执行也不是同一范围；过滤/精简可能改变能看到的内容，见[日志开关](torch_npu_log_filters_and_error_output.md)。来源给第三方工具和技术支持入口，但不代表已自动采集、上传或提交问题。

## ERR的模块和类型分别解读

格式为ERR+两位模块+三位类型，共8字符。模块00=PTA框架、01=OPS算子、02=DIST分布式、03=GRAPH图、04=PROF采集、99=UNKNOWN。图里将ERR栏写“级别3位/Level 3 digits”，正文明确前缀ERR是错误类，不按图词误读成三个数字。

| 类型后缀 | 含义及下一步 |
| --- | --- |
| 001 | 无效参数，核对实际入参 |
| 002 | 参数类型，结合消息检查dtype/device等，不能仅凭后缀确定是哪一项 |
| 003 | 值、shape或维度不合法 |
| 004 | 无效指针，保留准确调用和日志，不读取未知活跃地址 |
| 005 | 内部错误，保留首错与栈进一步定位 |
| 006 | 内存异常，不直接等同于某一个分配器OOM路径 |
| 007 | 特性不支持，确认入口/版本/参数再选择可替代路径 |
| 008 / 009 | 资源不存在 / 资源不可用，分别检查路径和运行状态 |
| 010 / 011 / 012 | 系统调用 / 超时 / 权限错误，继续查具体调用、参与者和对象 |
| 100 / 200 / 300 | ACL / HCCL / GE调用失败，是框架包装层线索，继续关联底层错误 |
| 999 | 应用或第三方异常，检查业务栈、依赖和配置 |

例如ERR00100不能唯一证明框架自身缺陷，ERR02200也不能直接归因为网络；这些代码与EZ3002、EI0002等CANN编码是不同层。日志包含级别、时间、PID/Device/RankID、码及释义；Device获取失败或RANK未配置时可为-1，不据-1推定真实设备号或通信组成员身份。

## 历史图的相关性边界

ReduceAny样例显示EZ3002与DT_FLOAT不符合该例BOOL规格，后续在npu.synchronize报告ERR00100；它说明先读底层消息及异步栈提示，不代表所有版本ReduceAny都只有该类型。另一幅plog是更早时间的DynamicGRUV2，不能因放在同一分析示例中就将两算子拼成同一故障链。

其他截图展示旧Autocast退出栈、HCCL初始化后续错误与底层内存失败。历史PID、IP、地址、约2.7GB申请及包路径不是当前事实；图中某条“pool failed可忽略”的提示不覆盖同屏Runtime/driver的out of memory。按同作业、同rank/进程和时间关联，单一截图不提供完整因果。

## 常见调用失败先分层

同提交参数案例torch.add(CPU Tensor,NPU Tensor)报告ERR01002，应检查真实参数device/dtype；不能从代码标题推定所有device混用都可自动搬运。初始化例AclSetCompileopt/500001/ERR00100只定位到初始化调用层，不能无日志就指定是某个精度配置错误。

Cannot find bin of op Range / ERR01100的历史案例给两类检查：匹配的Kernels或ops包是否存在，以及输入dtype/格式是否有对应二进制。Python接口能导入、Schema存在不证明匹配的设备Kernel已安装；仍按准确软件栈和产品规格核对，不能仅清缓存或改任意dtype来掩盖原因。

## SIGSEGV与实际Core文件

Segmentation fault或收到signal 11是崩溃线索，不等于core文件必然已经落盘。按目标进程环境检查ulimit -c、core_pattern及输出目录；文档的unlimited/0分别表示大小不限制/不保存，但实际还取决于系统收集机制与路径。core_pattern是系统配置，文档示例需要root；不能把来源“默认不生成”推广到每个系统。本次未修改任何限制或sysctl。

容器中应保留匹配的解释器、库、符号与可持久化路径，再对准确core文件使用gdb。bt查看当前线程，thread apply all bt查看该被调试进程的所有线程，原文“所有进程”注释不准确。图中mutex/Event查询/WorkHCCL/watchdog栈只是历史崩溃位置，不独立证明某模块就是根因；没有Python栈也不能排除原生线程错误。

## 验收

修复后重跑相同输入域并核对输出、梯度、所有rank推进和正常异步配置；只增大超时、关闭告警或错误变短不证明问题消失。CANN完整故障码、设备日志工具与GDB外部手册均只是原文链接，不在本卡来源内。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_code_description/error_code_information.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/error_code_description/error_code_information.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_code_description/error_code_mechanism.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/error_code_description/error_code_mechanism.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_information_analysis_guide/error_information_analysis/error_information_analysis_process.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/error_information_analysis_guide/error_information_analysis/error_information_analysis_process.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_information_analysis_guide/error_information_introduction.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/error_information_analysis_guide/error_information_introduction.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_information_analysis_guide/locating_core_dump_faults.md)（primary）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/error_information_analysis_guide/locating_core_dump_faults.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_process.md)（primary）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/troubleshooting/troubleshooting_process.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_information_analysis_guide/error_information_classification/command_output.md)（primary）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/error_information_analysis_guide/error_information_classification/plog_log.md)（primary）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/failed_verify_op_parameters.md)（primary）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/initialization_error.md)（primary）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/operator_called_error.md)（primary）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/description_each_field.png)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/description_each_field.png)（constraint）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/meaning_field_2.png)（constraint）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/meaning_field_2.png)（constraint）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/meaning_field_3.png)（constraint）
- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/meaning_field_3.png)（constraint）
- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/error_information_analysis_process.png)（constraint）
- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/error_information_analysis_process.png)（constraint）
- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/example.png)（constraint）
- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/example.png)（constraint）
- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/python_call_stack.png)（constraint）
- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/python_call_stack.png)（constraint）
- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/locate_component_reports_error_plog.png)（constraint）
- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/locate_component_reports_error_plog.png)（constraint）
- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/viewing_stack.png)（constraint）
- [固定来源 33](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/viewing_stack.png)（constraint）
- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/troubleshooting_process.png)（constraint）
- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/troubleshooting_process.png)（constraint）
- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/viewing_stack_information_python_applications.png)（constraint）
- [固定来源 37](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/application_logs.png)（constraint）
- [固定来源 38](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/obtaining_plog_logs.png)（constraint）
- [固定来源 39](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/plog_log_HCCL.png)（constraint）
- [固定来源 40](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/plog_log_OOM.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/CANN_software_error_code.png)（constraint）
