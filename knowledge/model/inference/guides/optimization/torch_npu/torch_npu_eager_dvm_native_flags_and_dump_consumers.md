---
type: Guide
title: Eager DVM环境解析、运行门控与Dump消费者
description: 核对环境首token与内部选项解析、算子等级门控、调优和确定性读取时机，以及文本dump保存方式。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_flags.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_flags.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_control.h
  role: implementation
created_at: '2026-11-11T02:59:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Eager DVM环境解析、运行门控与Dump消费者

## 固定实现与公开使用范围

静态审阅OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的本地flags、管理器与文本dump实现。公开配置与产品条件见[Eager DVM融合](torch_npu_eager_lazy_fusion.md)。本卡记录内部实现与调试路径，产品矩阵和发布配套待核，保持draft、空平台。运行和性能验收待执行。

## 环境变量首token决定后续解析

LazyFusionFlags构造时读取TORCH_NPU_LAZY_FUSION。未设置或仅由空格/制表符组成时关闭。首token识别True/true/TRUE/1/on与False/false/FALSE/0/off，False分支直接返回。其余首token按flag列表处理并将enabled置True，随后才登记已知key。

因此代码注释所称裸O1/O2应使用level=形式，与解析行为需要同时核对。所读实现会将裸O1作为未知flag告警，enabled已为True且等级仍取默认O2。部署沿用文档支持的公开写法，内部调试值按实际解析记录。

flag列表按空格分token，key或key=value有效，前导--、空key和多重等号会告警。重复key由map insert保留首次值并告警。列表本身的token分隔与首token的空格/制表符处理不同。布尔flag空值视为True，接受true/True/on/1及false/False/off/0。未知key告警，已知值解析失败时保留原默认字段。

## 内部字段及门控

默认等级为O2，level只识别O1/o1和O2/o2。dump_as_text、synchronize、online_tuning默认False，dump_dir默认./lazy_fusion_dump。disable_ops、enable_ops和enable_ops_only使用逗号列表。foreach_max_tensors默认8，foreach_min_numel默认65536。数值字段使用流提取和eof判定，本地未另建所有正负、溢出和上界约束。

IsEnabled(op, required)先检查最低等级。enable_ops_only非空时使用该名单，否则全局enabled为真时排除disable_ops，enabled为假时查询enable_ops。具体可执行路径还经过无参数IsEnabled，它检查脚本禁用标志、全局enabled和TaskQueue，过滤同步下发stream，并允许主线程或处于autograd graph task的线程。需要按两个层次及实际handler一起判断。

Manager::Get首次配置online_tuning，之后根据PyTorch deterministicAlgorithms布尔状态的变化调用SetDeterm/UnsetDeterm。这条Eager消费者读取布尔状态，源码没有在此读取TorchNPU的完整确定性整数等级。Inductor编译的等级Guard有自己的入口与条件。

## Dump开关和实际落盘

每次新kernel的dump标志来自dump_as_text与动态dump_enabled_的合取。SetDumpEnabled状态变化时先提交当前图，再更新开关。ShouldDump控制图文本、codegen前后DVM文本和Das的收集。DumpOp与ToString记录算子参数、dtype、shape、stride及Tensor/Storage地址等信息，输出标号按登记Store顺序组织。

LazyFusionDump单例首次构造时创建并解析dump_dir。目录创建权限为0750。图和kernel分别追加到含pid的graph.txt与kernel.txt文件，写入前后调整用户写/读权限。打开文件失败时记录告警并保留缓冲，打开成功后尝试追加并close，再清空对应字符串缓冲，本地没有检查写入或close状态。文件名及追加模式需结合多图、重复运行和目录状态核对。

这些文本由诊断路径产生，Tensor格式化和文件写入都有实际工作量。synchronize为另一项独立选项，会在Launch后请求stream同步。评估融合收益时记录真实选项、读取时机、codegen与dump开销，保存有效执行信号后再解释生成文件。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_flags.cpp)（primary），读取范围 1–249。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_flags.h)（implementation），读取范围 1–59。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.cpp)（implementation），读取范围 1–792。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.h)（implementation），读取范围 1–451。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_control.h)（implementation），读取范围 1–24。
