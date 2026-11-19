---
type: Guide
title: TorchAir 数据 Dump：GE、FX Eager 与捕获图的配置差异
description: 区分实际 Tensor 与图结构导出，说明 JSON 配置优先级、范围并集、Watcher 和 original 模式。
tags:
- task.debugging
- topic.performance.analysis
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/data_dump.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/data_dump_eager.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/data_dump.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/scope/data_dump.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/superkernel.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/data_dump.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/data_dump_eager.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/data_dump.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/data_dump.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/data_dump.png
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/SECURITY_README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-print_npugraph_tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-print_npugraph_tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/graphs.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Graph.cpp
  role: implementation
created_at: '2026-11-09T02:51:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir 数据 Dump：GE、FX Eager 与捕获图的配置差异

## 版本与范围

固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`，A2/A3 推理；这与只导出 FX/GE 节点结构是不同的诊断任务。未运行 Dump 或设备比对。

## GE 数据与范围

config.dump_config.enable_dump=True 开启，dump_mode 选 input/output/all；dump_step 可用 "0|3-5|10"，未设置则所有迭代。dump_data="stats" 先取统计 CSV，再针对异常节点取 tensor，避免全网全量数据。

dump_config_path 指向 JSON，来源推荐该路径并说明其他非 JSON 配置不再演进；不要混用两套细项，非 JSON options 优先、可能使 JSON 失效。quant_dumpable=True 才要求保留可能被优化掉的量化前数据。

torchair.scope.data_dump() 的范围与 dump_layer 是并集，scope 内不能断图。dump_layer 使用实际 GE 节点名，融合后名称可能变化；不是 Python 模块名的通用通配。

## Watcher 与溢出

Watcher 在 layer 节点执行后导出 watcher_nodes 的输出以排查内存踩踏；两者需位于静态图/静态子图，融合节点用最终名称，当前只支持 output，不配置 model_name。Watcher 不与溢出或模型/单算子 Dump 同开；溢出 Dump 也不与模型/单算子模式同开，并仅采 AI Core。框架已默认开启的 exception 信息 Dump 不会被这里的 exception 配置再次使能。

## FX Eager 与 npugraph_ex

GE config.debug.data_dump.type="npy" 以 FX Eager 取数据，GE 相关配置不生效；filter 返回 FX Node 或 None，按 FX 名过滤，不能把它当作优化后 GE 的运行产物。

npugraph_ex options.dump_tensor_data=True，data_dump_stage="optimized" 默认取优化后数据；"original" 仅以 Eager 执行原始 FX，不进入 aclgraph。data_dump_dir 必须存在且可读写，产物按 rank/device/计数标识。单点 replay 数据可用 save_npugraph_tensor，但需另核对该接口限制。固定主线 92e1e967bd35ebc37a442b4a969730bf3cf77a3c 的 npugraph_ex SuperKernel 优化会使 Data Dump 失效；该主线组合不推定为发布版已支持。

## 对照验证

保存相同 rank、token/step、shape 和输入的结构与数据，先确认实际执行模式，再寻找首个分歧。Dump 会干扰性能，性能采集另行进行，不能将调试产物的耗时报告为正常吞吐。

- [图结构与运行路径定界](torchair_graph_dump_and_run_eagerly.md)
- [精度和性能对照](torchair_accuracy_and_performance_triage.md)

## 主线GE、FX Eager与捕获图对照

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节文档/实现已核对，主线总览覆盖A2/A3与950PR/950DT；发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的A2/A3条件仍独立保留，不回推发布版950或两仓主线配套。

完整主线GE Dump页及图示将执行数据采集定位在GE实际图执行阶段，与Dynamo/IR转换、图优化的结构产物不同；支持与结构Dump共同使用，但不能用结构文本推导已采到实际Tensor。主线仍按enable_dump默认False、dump_mode默认all、quant_dumpable默认False、dump_data默认tensor和dump_step未设采所有迭代解释。dump_layer按空格分隔真实节点名，选中节点的输入涉及Data节点时还会采集该Data信息。来源建议用DUMP_GE_GRAPH=3生成各阶段ge_proto*.txt，从op.name取得GE节点名；不能把Python模块名或FX节点名直接替代。

JSON模型/单算子Dump、溢出Dump及Watcher均要求dump_path；模型示例以dump_op_switch="off"配合dump_list中的model_name/layer，单算子示例用空dump_list与dump_op_switch="on"。溢出用dump_debug="on"开启，未配置或off关闭；Watcher用dump_scene="watcher"。这些模式仍有前述互斥条件，推荐JSON不表示可以同时用旧细项且仍以JSON为准。Watcher无layer时会在所有可Dump节点执行后观察watcher_nodes；layer与watcher同名或layer为Hcom开头通信节点时，只导出watcher_nodes所指数据，不能按一般layer Dump解释。Watcher仍只支持output、静态图/子图，不支持model_name，融合节点用最终名称。

GE旧细项产物目录按dump_path、world/rank、时间、device、model_name、model_id、data_index组织；model_name中的点、斜杠、反斜杠与空格会转下划线。配置dump_step时data_index对应指定步，否则一般从0递增。GE二进制Dump需按工具转换后读取，不直接当文本或npy加载。

主线FX Eager的data_dump.type="npy"保留按FX Node或None过滤，GE配置不生效。文件按world/rank→子图→step组织，step从0开始，名中含FX节点/ATen IR、INPUT或OUTPUT、参数索引和时间戳；不要用融合后GE节点名去套FX过滤器，或把这一路径的数据和性能当优化后GE执行结果。

主线npugraph_ex的original仍只执行原始FX Eager，optimized取优化后FX，文件名的device与计数用于对齐；开启SuperKernel后dump_tensor_data失效。另一个单点save_npugraph_tensor会打断SuperKernel，文档提供task_breaker_bypass=1避开该打断；它只针对单点保存的融合中断，不表示能让整图dump_tensor_data在SuperKernel下重新生效。

本节主线A2/A3与950范围不补出发布段的950组合；全部路径均未在本仓运行验证。

## 安全声明的摘要与逐路径合同

双语根安全声明将GE图结构、实际计算数据Dump分开，均默认关闭；图文件的默认600声明不扩大为所有Tensor/统计/日志产物的统一保证。根CompilerConfig摘要仍列旧dump_mode=input/output/all、dump_data=tensor/stats、quant_dumpable默认False，与JSON路径/Watcher/溢出等完整合同按各自版本消费，不能从摘要未列功能断言不支持。

特殊场景表把from_pretrained下载列“随机端口/无风险”，这只是该页表述，不构成任意模型代码/权重来源可信、版本固定或可安全执行的证明；未查询/下载外部模型。公网地址表是开发依赖和示例IP清单，不新增真实通信端点、默认地址或外部模型知识覆盖。

## 单点张量诊断的版本与落盘边界

[print/save API](../../../apis/torch_npu/npugraph_tensor_io.md)明确区分发布多文件参数与main的overwrite及列表单文件；主线NPU路径先D2H再排Python pending回调，流event完成不证明文件已写完。单点接口的A2/A3文档不继承本Guide其他后端的950产品表；需在实际执行后核对文件路径、错误和内容完整性。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/data_dump.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/data_dump_eager.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/data_dump.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/scope/data_dump.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/superkernel.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/data_dump.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/data_dump_eager.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/scope/data_dump.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/data_dump.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/data_dump.png)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/SECURITY_README.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-print_npugraph_tensor.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-print_npugraph_tensor.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/graphs.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Graph.cpp)（implementation）
