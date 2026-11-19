---
type: Guide
title: 主线 Inductor 调度/分区测试族：NPUCombinedScheduling 索引失败拆分、npu graph 分区语义与 overlap 计算节点清单
description: 固定提交下 test/_inductor 七个调度/分区测试文件及其实现面：NPUCombinedScheduling 的 codegen_node 异常回退拆分与 benchmark 拒收语义（npu_combined_scheduling.py 245 行实现面）、graph_partition 的 npugraph 计数/自定义分区/内核无关路径、overlap 估时的六个注册计算算子包、流融合回归的跳过态。
tags:
- task.testing
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_nolinear_fallback_fusion.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/npu_combined_scheduling.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_inductor_graph_partition.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_overlap_scheduling_npu.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_npu_stream_fusion_regression.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_lowering_device_dispatch.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_inductor_fallback_list_triton.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_shape_handling.py
  role: primary
created_at: '2026-11-12T17:08:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 主线 Inductor 调度/分区测试族：NPUCombinedScheduling 索引失败拆分、npu graph 分区语义与 overlap 计算节点清单

## 固定版本与范围

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `test/_inductor` 七个调度/lowering/回退测试加实现面 `codegen/npu_combined_scheduling.py`（245 行；其余卡只持 `_inductor/__init__.py:258/:263` 的注册锚）。调度器 `NPUTritonScheduling`/Welford 主体归[Welford 调度卡](torch_npu_main_inductor_scheduling_welford_and_fusion.md)，overlap 估时主体归 [overlap 估时卡](../../../../training/guides/torch_npu_inductor_overlap_runtime_estimation.md)，lowering 分派器归 [分解注册卡增补](../../../../training/guides/torch_npu_mlir_dvm_decomposition_registry_and_training_math.md)。未运行任何测试。

## NPUCombinedScheduling：索引失败拆分与 benchmark 拒收（test_nolinear_fallback_fusion.py + npu_combined_scheduling.py）

组合调度器把 `_triton_scheduling`（index 后端）失败转化为 no-linear 拆分（实现 :181-202，测试逐分支镜像）：

- **codegen_node 事务性**：先备份 `removed_buffers`/`inplaced_to_remove`/`generated_kernel_count`，index codegen 抛异常即**恢复三者**（失败融合 kernel 可能已把中间 buffer 标成 kernel-local，拆分后需要重新物化），再 `_regroup_for_nolinear`（对合并后的 loop 用 nolinear `group_fn` 重算标量组；`enable_welford` 时按 canonical group 归一）→ `_split_nolinear_nodes`（先 `topological_sort_schedule`，随后祖先相交走 vertical、否则 horizontal 的 `can_fuse` 逐步 `FusedSchedulerNode.fuse`）→ 逐组 emit。
- **新核边界的生命周期重算**（实现 :155-179，测试 :125-167）：以 `future_used_buffers` 从后向前传播，`mutation_real_name` 别名随组重映射；`buffer_names_to_free` 先 `difference_update` 原融合节点的 last_usage、再逐组补各组的；`name_to_fused_node` 指向新组；`current_node` 保持原入口节点（wrapper 内存规划用它在 scheduler.nodes 中的位置分配/释放）。静态可证的等价组（symbolic=False）不拆分；`SIMDKernel.is_compatible` 拒收同样触发拆分（测试 :163-167）。
- **benchmark_fused_nodes 拒收**（实现 :204-224，测试 :197-217）：index 基准异常 → nolinear 重分组+拆分，若拆出多于 1 组则返回 `(inf, "")`（拆分 kernel 不是被基准的融合候选）；无论成败 `snode.group` 在 finally 中还原。welford 的融合优先级：同 Welford 输出组 0、epilogue 融合 1，其余保持上游默认序（实现 :84-105）。`can_fuse_reduction_pair` 恒 True、`can_fuse_reduction_epilogue` 恒 False——注释原义：NPU 不产 NV universal-GEMM 模板，CUDA 侧冲突不可能存在。combo 路径的 subkernel 节点组也经 nolinear group_fn 重算后交 `_triton_scheduling.codegen_combo_kernel`（:240-245）。

## graph_partition 的 npugraph 语义（test_inductor_graph_partition.py）

- **计数契约**：图含 CPU 中段 → 2 分区 → 2 个 npugraph id；`mode="reduce-overhead"` 之外（默认 mode）不建 npugraph（manager None）；动态形状每 shape 一个 npugraph（3 shape → 3 id）；reorder 把 NPU 段并成 1 分区；前向 2 分区+反向 1 分区 = 3 个 graph id。首个用例（refcount）在 mm 前断言输入弱引用已清——分区边界即释放点。
- **自定义算子**：带 `cudagraph_unsafe` tag 的 custom op 是分区切点（2 个 unsafe op → 3 graph）；`torch._inductor.config.custom_should_partition_ops` 可按 packet 名或 overload 名指定切点（`mylib::baz_npu` 与 `mylib::baz_npu.default` 均生效 → 2 分区），改配置不触发重编译（`fail_on_recompile` stance 通过）。kernel-free 路径（torch≥2.14 `KERNEL_FREE_CUDAGRAPH_SUPPORTED`）：view-only 图不分区，树节点 `wrapped_function.kernel_free_cudagraph` 为真、`graph` 为 None——注释原义：节点仍须在私有池执行，但不得创建/重放空 NPU graph。CPU 标量分区含 host-side `.item()`，不得 capture-unsafe 或改变结果。上述 kernel_free/计数语义与 [npugraph 接线卡](torch_npu_npugraphs_backend_wiring_and_legacy_capture.md) 的 `kernel_free_cudagraph` 转发记录互为消费镜像。
- **测试基建事实**：`TORCH_NPU_USE_COMPATIBLE_IMPL=1` 须在 import torch_npu 前设置（`aten.matmul_backward` 只在兼容模式注册 NPU meta）；torch_npu 必须先于 `inductor_utils` import（后者在导入时冻结 `HAS_TRITON = has_triton()`，顺序错会让 `@requires_triton()` 在 NPU 上全部静默跳过）；`NPU TreeManagerContainer` 强引用 tree manager，`reset_npugraph_trees()` 清理。

## overlap 估时的注册计算节点与日志（test_overlap_scheduling_npu.py）

该文件大部分为 [overlap 估时卡](../../../../training/guides/torch_npu_inductor_overlap_runtime_estimation.md) 的单元镜像（median/事件 warmup 序/合成分组三形态/缓存键不含 group_list 内容/unbacked 维报错/collective 自定义优先→benchmark→0.0/roofline 0.0/analytical 与 deterministic 入口拒绝/pre_bucketing 关闭）。新增两锚：

- **注册计算算子包全集**（:230-265）：`_build_npu_is_compute_node` 认定的 NPU 包为 `npu_grouped_matmul`、`npu_fused_matmul`、`npu_fusion_attention_v3`、`npu_fusion_attention_grad_v3`、`npu_fusion_attention_v3_unsafe`、`npu_fusion_attention_grad_v3_unsafe`（含两个 unsafe 变体），上游谓词命中另算，其余 False——估时卡此前只说"替换上游的计算节点识别"未列清单。
- `_wait_collective_result` 沿 dict/list/tuple 嵌套走全部 Tensor 逐个 `wait_tensor`（非 Tensor 跳过）；collective logger 以 `trace_structured("artifact")` 落 CSV，含 `# World size: N` 头与四位小数对齐中位值（:207-225, :573-598）。

## 流融合回归的跳过态与两处镜像定案

- test_npu_stream_fusion_regression.py（90 行）整类 `@unittest.skip("currently not passing")`：意图契约是融合调度节点在 `node_to_stream` 中叶片与父节点同流、侧流融合 stream>0、双流各自保持、融合不跨默认流(0)与侧流——跳过状态本身即当前固定提交的静态意图记录。
- test_lowering_device_dispatch.py（369 行）：分派器优先级/包展开/幂等/恢复保持 lowerings 字典对象身份/FakeTensor 元数据保留，全部为 [分解注册卡增补](../../../../training/guides/torch_npu_mlir_dvm_decomposition_registry_and_training_math.md) 分派器节的逐分支镜像。
- test_inductor_fallback_list_triton.py（33 行）：`NPU_INDUCTOR_FALLBACK_LIST=aten.div,aten.add.Tensor` 导入前设置后，div 编译产物不含 `unk_fused_div` 融合 kernel——[配置解析卡](torch_npu_inductor_config_parsing.md) 与 [矩阵乘族卡](torch_npu_inductor_triton_matmul_kernel_family.md) 已持该 env 的逐项 resolve 与 LOWERING_OVERRIDE_OP 移除语义，本文件是其编译产物级观测镜像。
- test_shape_handling.py（882 行）：NPUShapeHandling 的 padding/split/recover/校验分支/策略注册主体为 [shape handling API 卡](shape_handling.md) 镜像；测试侧新增微锚：`_construct_indices` 默认规则（BATCHSIZE 全张量、SEQLEN 只收 2 维张量）、`delay_initialize` 补空 indices、`transform_hook`/`recover_hook` 的 pre/post fn 挂点、`patch_shape_handling` 幂等（`_is_patched`）、`TorchCompileInductorWrapper` 注册 `enable_shape_handling/shape_handling_configs` 且仅启用时调 `_patch_shape_handling` 一次、`unified_copy` deepcopy 失败回原件；桶化收益的编译计数观测——无桶 4 形状 4 次 kernel、桶化后 2 次、符号化 1 次。

## 失效边界与静态口径

- 全部未运行；分区计数、`fail_on_recompile`、kernel-free 断言、`(inf, "")` 拒收均按字面控制流与 mock 骨架读出。
- `npu_combined_scheduling.py` 的 CATLASS 分支（`is_catlass_template`/`FusedCATLASSBenchmarkRequest`）只按调用形态记录，CATLASS 调度器本体不在本卡范围；上游 `CUDACombinedScheduling` 继承面在六 pin 外。
