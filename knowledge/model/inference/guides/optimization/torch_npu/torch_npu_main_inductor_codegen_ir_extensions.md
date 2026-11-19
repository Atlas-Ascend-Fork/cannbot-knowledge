---
type: Guide
title: NPU Inductor代码生成IR层：扁平化索引、间接内存与批量融合调优
description: 记录torch_npu._inductor对torch._inductor codegen IR的扩展面：flattened dims检测与重建、inductor_indirect_memory_mode、A5(950)专属线性化跳过、IndexputTemplate间接索引、kernel_analysis步长分析、Scheduler的L2敏感批量profiling、AOTI导出与shape_handling门面。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/ir.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/ir.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/ir_fx.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/ir_fx.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/kernel_analysis.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ir.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ir.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/scheduler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/shape_handling.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/export.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_config_generator.py
  role: implementation
created_at: '2026-11-13T04:14:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# NPU Inductor代码生成IR层：扁平化索引、间接内存与批量融合调优

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的`torch_npu/_inductor`对torch._inductor codegen/调度IR的扩展层（codegen/ir.py、ir_fx.py、kernel_analysis.py、graph.py、ir.py、scheduler.py及小门面）。静态阅读；大文件按结构+定向范围阅读并在Evidence标注。本卡补绑发布f3ecfe4a（TorchNPU 26.0.0）四个差异文件的来源并在「两版差异边界」分节——**本卡正文所述的间接内存与A5线性化机制为主线独有**。环境变量语义与fx pass框架见[编译资源与pass](torch_npu_inductor_compile_resources_and_passes.md)，DVM/MLIR路线见[DVM融合执行](torch_npu_dvm_mlir_codegen_and_fallback.md)。整卡draft、platforms为空。

## 扁平化索引：检测、重建与A5专属跳过

`codegen/ir.py`的核心主题是把多循环索引表达式重写为设备友好的扁平形式：`detect_flattened_dims`从ModularIndexing/FloorDiv结构识别可扁平化的(var,length)对（含s77**2这类复合表达式按自由符号回退跳过）；`rebuild_flattened_dims`/`substituted_dims_in_indexing`负责替换与回填；`analyze_modular/floordiv_expression`、`calculate_max_remainder`等做系数与余项分析。两个版本门控值得注意：**`inductor_indirect_memory_mode`配置驱动间接索引替换**（`substitube_indirect_index`等）；**`should_skip_linearization_on_a5`在is_ascend950时按动态shape条件跳过线性化**（`transform_dims_in_indexing`同样按is_ascend950分流）——即索引线性化策略按SoC代际分叉，950与非950生成的索引形态可以不同，性能对比须先固定芯片型号。`NPUIndexTritonKernel`/`get_indirect_mem_var`等与triton_utils协作提供间接内存变量管线。**上述门控与间接内存管线均为主线独有（发布26.0.0的codegen/ir.py仅199行、7个顶层符号），见「两版差异边界」**。

## ir_fx与graph：origin_node传播与mutation反射

`codegen/ir_fx.py`以monkey patch方式给torch._inductor的loops/IRNode补`origin_node`/`traced_graph`传播（_patch_loops_create等），让代码生成期能回溯FX节点；`graph.py`在薄re-export之上新增`npu_propagate_mutation`：旧参数与新参数同对象或同名buffer时视为“mutation已反射”，避免重复标记。**这两个文件是对torch内部结构的定点patch**，PyTorch升级时是高脆性面；`ir.py`定义`IndexputTemplate`（Scatter子类）：store_output里识别`indirect`前缀索引变量并传给ops.indexput_template，附带boundary参数——index_put模板的间接索引与边界语义在此闭合（**ir.py与graph.py在发布pin为完全不同的模块内容，见「两版差异边界」**）。

## kernel_analysis：按步长排序的轴分析

`codegen/kernel_analysis.py`的`extract_axis_strides`/`IndexAnalysis`/`ReductionAnalysis`从索引表达式抽取(var,stride,hint,position)，过滤stride=0与不可消var项后按“是否0步长、绝对步长、位置”排序，供调度器判断fusion与布局；`collect_stride_sorted_vars_from_nodes`面向整个node schedule。这是NPU侧融合决策的输入之一，与[平行调度](torch_npu_inductor_parallel_schedule.md)的消费关系以该卡为准。

## Scheduler：为什么必须批量profiling

`scheduler.py`的`_do_batch_profiling_for_fusion`注释给出了机制性理由：**逐choice的event计时（benchmark_gpu）对L2 cache效果不敏感**——L2_MODE_A/B这类只在缓存行为上差异的配置，单次基准分不出快慢（举例：L2_MODE=2测20us、L2_MODE=0实际14us，逐choice计时可能随机选中慢配置），因此用torch_npu.profiler做批量profile后再选。这是“autotune随机选慢配置”问题的结构性缓解，不是消除；CATLASSTemplateCaller等choice类型接入同一路径。`patch_get_graph_partition_signature`维护分区签名。**迁移结论时注意**：该收益论证只针对L2敏感参数，普通配置仍走常规autotune。

## 小门面：shape_handling、export、index_select补丁、flex配置生成

`shape_handling.py`是`torch_npu.utils._dynamo.NPUShapeHandling`的门面（patch_dynamo_context/patch_shape_handling，幂等保护）；`export.py`给torch._export.aot_load打NPU补丁：device为npu时用`AOTIModelContainerRunnerNpu`加载.so并按call_spec做pytree展开/收拢，其余设备回原实现——**AOTI导出产物在NPU上的加载入口**。`triton_experimental/codegen/__init__.py`给CaptureIndexing/SimplifyIndexing补index_select：A5 __builtin_index_select的gather带一个sympy权重索引（内嵌间接TMP行符号），按MemoryUsageType.LOAD注册、行索引变量与bound直通。`kernel/flex_attention_config_generator.py`生成FlexAttention分块配置（FlexMode分FWD/BWD/BWDDQ/BWDDKDV，block_m/block_n等，NO_SPARSE_BLOCK_SIZE=1<<30），与triton_experimental侧adapter的分工见[FlexAttention源适配](torch_npu_experimental_flex_attention_source_adapter.md)。

## 两版差异边界（发布f3ecfe4a对照，静态diff）

固定源码对照（diff+AST比对）：

- **codegen/ir.py**：主线2052行/44顶层符号，发布199行/仅7符号（`num_splits`、`detect_flattened_dims`、`rebuild_flattened_dims`、`substituted_dims_in_indexing`、`generate_body_indexing`、`transform_dims_in_indexing`、`loopbody__call__`）。主线独有：`inductor_indirect_memory_mode`间接索引管线（`substitube_indirect_index`/`get_indirect_index`/`generate_masked_indexing`/`generate_indirect_replacements`/`get_masked_index`等）、`should_skip_linearization_on_a5`与`transform_dims_in_indexing`的is_ascend950分流、`_SIMT_TEMPLATE_UNSAFE_REDUCTION_TYPES`、`analyze_modular/floordiv_expression`族、symbol index map（共37个符号）。发布版保留扁平化dims检测/重建核（函数体有差异、无A5分流）。**950线性化分叉与间接内存结论不外推发布26.0.0**。
- **codegen/ir_fx.py**：`origin_node`/`traced_graph`传播与`_patch_loops_create`两版都在（卡内锚成立）；主线独有`try_get_buffer`、`_patch_Reduction_create_multilayer(+helper)`，发布对应为`get_buffer`；52公共符号21个AST一致，7个补丁函数体差异。
- **graph.py**：文件用途反转——主线125行为薄再导出+`npu_propagate_mutation`（+`patch_propagate_mutation`/`patch_count_bytes`），发布114行为`patch_codegen_with_cpp_wrapper`接线（把Inductor codegen替换为cpp wrapper版本），无mutation反射逻辑。**卡内mutation反射结论主线独有**。
- **ir.py**：文件用途反转（整文件级）——主线132行（带BOM）定义`IndexputTemplate`/`ScatterTemplate`/`reduction_split_factor`/`num_splits`/`patch_num_splits`；发布88行为`patch_fallback_kernel_codegen`（fallback kernel codegen补丁），无IndexputTemplate内容。**卡内IndexputTemplate结论主线独有**。

## 边界与验证方式

本卡对codegen/ir.py（2052行）、ir_fx.py（991行）、scheduler.py（1074行）为结构+定向范围阅读，未逐函数覆盖；引用具体重写规则前以文件实际内容为准。索引形态、L2批量profiling、AOTI加载都未运行验证：比较950与非950生成代码、开/关indirect_memory_mode、L2敏感配置的选择稳定性与AOTI roundtrip须按真实环境复核；**以上重写规则类验证只在主线pin有实现基础，发布26.0.0无对应机制**（见「两版差异边界」）。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/ir.py)（primary）：定向范围1–45、144–200、1464–1590（结构与关键函数）；两版diff比对（U0 42 hunks，+63/−1916）。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/scheduler.py)（implementation）：定向范围34–100（批量profiling动机与实现）。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/kernel_analysis.py)（implementation）：定向范围10–62。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/ir_fx.py)（implementation）：定向范围1–60；两版diff比对（U0 54 hunks，+80/−194）。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/graph.py)（implementation）：定向范围1–40；发布版114行全读（用途反转）。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ir.py)（implementation）：定向范围1–40；发布版88行全读（用途反转）。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/export.py)（implementation）：全文件27行。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/__init__.py)（implementation）：全文件29行。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_config_generator.py)（implementation）：定向范围1–45。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/shape_handling.py)（implementation）：全文件19行。
- [补绑发布来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/ir.py)（implementation）：分界绑定，全文件阅读+顶层符号清点（199行/7符号）。
- [补绑发布来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/ir_fx.py)（implementation）：分界绑定，全文件两版diff+符号AST比对。
- [补绑发布来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/graph.py)（implementation）：分界绑定，全文件阅读（114行，patch_codegen_with_cpp_wrapper）。
- [补绑发布来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ir.py)（implementation）：分界绑定，全文件阅读（88行，patch_fallback_kernel_codegen）。
